#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""War prisoner linking tasks"""
from typing import DefaultDict

import numpy

import argparse
import logging
import random
import re
from glob import glob

import pandas as pd
from arpa_linker.arpa import ArpaMimic, Arpa
from rdflib import Graph, URIRef, RDF, Literal
from rdflib.exceptions import UniquenessError
from rdflib.namespace import SKOS
from rdflib.util import guess_format
import rdf_dm as r

from namespaces import SCHEMA_POW, BIOC, SCHEMA_WARSA, bind_namespaces, SCHEMA_ACTORS, CRM, DATA_NS, MEDIA_NS
from warsa_linkers.municipalities import link_to_pnr, link_warsa_municipality
from warsa_linkers.occupations import link_occupations
from warsa_linkers.person_record_linkage import link_persons, intersection_comparator, activity_comparator, \
    get_date_value, read_person_links
from warsa_linkers.ranks import link_ranks

log = logging.getLogger(__name__)

# TODO: Write some tests using responses


def _preprocess(literal, prisoner, subgraph):
    """Default preprocess implementation for link function"""
    return str(literal).strip()


def link(graph, arpa, source_prop, target_graph, target_prop, preprocess=_preprocess, validator=None):
    """
    Link entities with ARPA based on parameters

    :return: target_graph with found links
    """
    prop_str = str(source_prop).split('/')[-1]  # Used for logging

    for (prisoner, value_literal) in list(graph[:source_prop:]):
        value = preprocess(value_literal, prisoner, graph)

        log.debug('Finding links for %s (originally %s)' % (value, value_literal))

        if value:
            arpa_result = arpa.query(value)
            if arpa_result:
                res = arpa_result[0]['id']

                if validator:
                    res = validator.validate(arpa_result, value_literal, prisoner)
                    if not res:
                        log.info('Match {res} failed validation for {val}, skipping it'.
                                 format(res=res, val=value_literal))
                        continue

                log.info('Accepted a match for property {ps} with original value {val} : {res}'.
                         format(ps=prop_str, val=value_literal, res=res))

                target_graph.add((prisoner, target_prop, URIRef(res)))
            else:
                log.warning('No match found for %s: %s' % (prop_str, value))

    return target_graph


def link_camps(graph, endpoint):
    """Link PoW camps."""

    value_mapping = {
        'Siestarjoki': "Siestarjoki, ven. Sestroretsk",
        'Karhumäki': "Karhumäki, evakuointipiste",
        'Sorokka': 'Sorokka ven. Belomorsk',
    }

    def preprocess(literal, prisoner, subgraph):
        literal = str(literal).strip().replace('"', '\\"')

        log.debug(f'Preprocessing camp for linking, {literal} : {value_mapping.get(literal, literal)}')
        return value_mapping.get(literal, literal)

    query = "PREFIX ps:<http://ldf.fi/schema/warsa/prisoners/>" + \
            "SELECT * {" + \
            "  GRAPH <http://ldf.fi/warsa/prisoners> {" + \
            "    VALUES ?place { \"<VALUES>\" }" + \
            "    ?id ps:camp_id|ps:captivity_location ?place . " + \
            "  }" + \
            "}"

    arpa = ArpaMimic(query, url=endpoint, retries=3, wait_between_tries=3)

    return link(graph, arpa, SCHEMA_POW.location_literal, Graph(), SCHEMA_POW.location, preprocess=preprocess)


def _generate_prisoners_dict(graph: Graph, ranks: Graph):
    """
    Generate a persons dict from POW records.
    """

    prisoners = {}
    for person in graph[:RDF.type:SCHEMA_WARSA.PrisonerRecord]:
        if graph.value(person, SCHEMA_POW.personal_information_removed):
            log.info('Skipping pruned person: {}'.format(str(person)))
            continue  # Personal information has been removed, do not try to link

        rank_uris = list(graph.objects(person, SCHEMA_POW.rank))

        given = str(graph.value(person, SCHEMA_WARSA.given_names, any=False))
        family = str(graph.value(person, SCHEMA_WARSA.family_name, any=False))
        rank = sorted(str(r) for r in rank_uris if r) or None
        birth_places = sorted(str(place) for place in graph.objects(person, SCHEMA_WARSA.municipality_of_birth)) or None
        death_places = sorted(str(place) for place in graph.objects(person, SCHEMA_POW.municipality_of_death)) or None
        units = sorted(str(unit) for unit in graph.objects(person, SCHEMA_POW.unit)) or None
        occupations = sorted(str(occ) for occ in graph.objects(person, BIOC.has_occupation)) or None

        births = [get_date_value(bd) for bd in graph.objects(person, SCHEMA_WARSA.date_of_birth)]
        deaths = [get_date_value(dd) for dd in graph.objects(person, SCHEMA_POW.date_of_death)]
        birth_begin = min([d for d in births if d] or [None])
        birth_end = max([d for d in births if d] or [None])
        death_begin = min([d for d in deaths if d] or [None])
        death_end = max([d for d in deaths if d] or [None])

        rank_levels = []
        try:
            for rank_uri in rank_uris:
                rank_levels.append(int(ranks.value(rank_uri, SCHEMA_ACTORS.level, any=False)))
        except (TypeError, UniquenessError):
            pass

        prisoner = {'person': None,
                    'rank': rank,
                    'rank_level': max(rank_levels or [None]),
                    'given': given,
                    'family': re.sub(r'\(ent\.\s*(.+)\)', r'\1', family),
                    'birth_place': birth_places,
                    'birth_begin': birth_begin,
                    'birth_end': birth_end,
                    'death_begin': death_begin,
                    'death_end': death_end,
                    'death_place': death_places,
                    'activity_end': death_end,
                    'unit': units,
                    'occupation': occupations
                    }
        prisoners[str(person)] = prisoner

        log.debug('Prisoner {uri}: {data}'.format(uri=person, data=prisoner))

    return prisoners


def _prune_person_links(graph, links):
    pruned_links = []
    for link in links:
        doc = link[0]
        if not graph.value(URIRef(doc), SCHEMA_POW.personal_information_removed):
            log.debug('Using link %s in training data' % str(link))
            pruned_links.append(link)
        else:
            log.info('Pruning prisoner %s from training data' % doc)

    return pruned_links


def link_prisoners(input_graph, endpoint):
    data_fields = [
        {'field': 'given', 'type': 'String'},
        {'field': 'family', 'type': 'String'},
        {'field': 'birth_place', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
        {'field': 'birth_begin', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'birth_end', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'death_begin', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'death_end', 'type': 'DateTime', 'has missing': True, 'fuzzy': False},
        {'field': 'death_place', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
        {'field': 'activity_end', 'type': 'Custom', 'comparator': activity_comparator, 'has missing': True},
        {'field': 'rank', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
        {'field': 'rank_level', 'type': 'Price', 'has missing': True},
        {'field': 'unit', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
        {'field': 'occupation', 'type': 'Custom', 'comparator': intersection_comparator, 'has missing': True},
    ]

    ranks = r.read_graph_from_sparql(endpoint, "http://ldf.fi/warsa/ranks")

    random.seed(42)  # Initialize randomization to create deterministic results
    numpy.random.seed(42)

    training_links = read_person_links('data/person_links.json')

    for (prisoner, person) in training_links:
        if not input_graph.triples((URIRef(prisoner), None, None)):
            log.warning('Prisoner %s found in training links but not present in data.' % prisoner)

    training_links = _prune_person_links(input_graph, training_links)

    log.info('Using %s person links as training data' % len(training_links))

    return link_persons(endpoint, _generate_prisoners_dict(input_graph, ranks), data_fields, training_links,
                        sample_size=100000,
                        training_size=500000,  # 500000 provides good results but takes ages
                        threshold_ratio=0.8
                        )


def add_link(graph: Graph, munic_mapping: dict, sourceprop: URIRef, targetprop: URIRef):
    literals = graph.subject_objects(sourceprop)
    munic_links = Graph()
    for sub, obj in literals:
        try:
            munic_links.add((sub, targetprop, munic_mapping[str(obj)]))
        except KeyError:
            pass

    return munic_links


def link_municipalities(g: Graph, warsa_endpoint: str, arpa_endpoint: str):
    """
    Link to Warsa municipalities.
    """

    warsa_munics = r.helpers.read_graph_from_sparql(warsa_endpoint,
                                                    graph_name='http://ldf.fi/warsa/places/municipalities')

    log.info('Using Warsa municipalities with {n} triples'.format(n=len(warsa_munics)))

    pnr_arpa = Arpa(arpa_endpoint)
    pnr_links = link_to_pnr(g,
                            SCHEMA_POW.municipality_of_death,
                            SCHEMA_POW.municipality_of_death_literal,
                            pnr_arpa,
                            preprocess=False,
                            new_graph=True)['graph']

    war_munics = set(g.objects(None, SCHEMA_WARSA.municipality_of_birth_literal)) | \
        set(g.objects(None, SCHEMA_POW.municipality_of_domicile_literal)) | \
        set(g.objects(None, SCHEMA_POW.municipality_of_residence_literal)) | \
        set(g.objects(None, SCHEMA_POW.municipality_of_capture_literal))

    war_munic_mapping = {}
    war_munic_links = Graph()

    for munic_literal in war_munics:
        warsa_match = link_warsa_municipality(warsa_munics, [str(munic_literal)])
        if warsa_match:
            war_munic_mapping[str(munic_literal)] = warsa_match
        else:
            log.warning('No warsa link found for municipality {}'.format(munic_literal))

    for source, target in [(SCHEMA_WARSA.municipality_of_birth_literal, SCHEMA_WARSA.municipality_of_birth),
                           (SCHEMA_POW.municipality_of_domicile_literal, SCHEMA_POW.municipality_of_domicile),
                           (SCHEMA_POW.municipality_of_residence_literal, SCHEMA_POW.municipality_of_residence),
                           (SCHEMA_POW.municipality_of_capture_literal, SCHEMA_POW.municipality_of_capture)]:
        war_munic_links += add_link(g, war_munic_mapping, source, target)

    return war_munic_links + pnr_links


def link_sotilaan_aani(g: Graph, input_file: str):
    """
    Link textual Sotilaan Ääni references to the magazine files. Also create magazine resources.
    """
    magazine_index = pd.read_csv(input_file, encoding='UTF-8', index_col=False, sep=',', quotechar='"', dtype=str)
    magazine_index = magazine_index.dropna()  # Drop rows with empty values

    mapping = DefaultDict(list)
    sa_links = Graph()
    documents = Graph()

    for index, row in magazine_index.iterrows():
        key = str(row['VIITE']).strip()

        uri = MEDIA_NS['sotilaan_aani_{dir}_{filenumber}'.format(dir=row['HAKEMISTO'], filenumber=row['TIEDOSTONIMI'])]

        file_url = URIRef('https://static.sotasampo.fi/sotilaan_aani/{dir}/Thumbs/{filenumber}.jpg'.format(
            dir=row['HAKEMISTO'], filenumber=row['TIEDOSTONIMI']))

        mapping[key].append(uri)

        # Create document resource
        label = 'Sotilaan Ääni {year}/{num}'.format(year=row['HAKEMISTO'], num=row['TIEDOSTONIMI'])
        documents.add((uri, SKOS.prefLabel, Literal(label)))
        documents.add((uri, RDF.type, SCHEMA_WARSA.SotilaanAani))
        documents.add((uri, URIRef('http://schema.org/contentUrl'), file_url))

    missing = 0
    triples = list(g.triples((None, SCHEMA_POW.sotilaan_aani, None))) + \
              list(g.triples((None, SCHEMA_POW.photograph_sotilaan_aani, None)))

    for (sub, _, obj) in triples:

        textual_reference = str(obj).strip()
        uris = mapping.get(textual_reference)

        if uris:
            for uri in uris:
                sa_links.add((sub, SCHEMA_WARSA.sotilaan_aani_magazine, uri))
                log.debug('Found Sotilaan Ääni reference %s for %s' % (uri, textual_reference))
        else:
            log.warning('No Sotilaan Ääni reference found for %s' % textual_reference)
            missing += 1

    log.info('Found %s Sotilaan Ääni links, with %s unidentified references' % (len(sa_links), missing))

    return sa_links, documents


def link_person_documents(g: Graph):
    """
    Link references from document files to prisoner records. Also create document media resources.
    """
    links = Graph()
    documents = Graph()

    paths = ['data/person_documents/returned/*.pdf',
             'data/person_documents/winterwar_interrogation/*.pdf',
             'data/person_documents/winterwar_registration/*.pdf']

    label_map = {'returned': 'Neuvostoliittolainen palautettujen henkilömappi',
                 'winterwar_registration': 'Neuvostoliittolainen vangittujen ja internoitujen henkilömappi',
                 'winterwar_interrogation': 'Neuvostoliittolainen kuulustelulomake'}

    unidentified_references = 0

    for path in paths:
        log.info('Finding documents for path %s' % path)
        for f in glob(path):
            id_groups = re.match(r'data/person_documents/([a-z_]+)/(\d{1,4})(_.+\.pdf)', str(f))
            directory = id_groups.groups()[0] if id_groups else None
            prisoner_id = id_groups.groups()[1] if id_groups else None
            suffix = id_groups.groups()[2] if id_groups else None

            if not (directory and prisoner_id and suffix):
                log.warning('Prisoner ID not identified from file %s' % f)
                unidentified_references += 1
                continue

            prisoner_uri = DATA_NS['prisoner_{id}'.format(id=prisoner_id)]
            document_uri = MEDIA_NS['{dir}_{prisoner_id}'.format(dir=directory, prisoner_id=prisoner_id)]
            file_url = URIRef('https://static.sotasampo.fi/person_documents/{dir}/{id}{suffix}'.format(
                dir=directory, id=prisoner_id, suffix=suffix))

            links.add((prisoner_uri, SCHEMA_WARSA.person_document, document_uri))

            log.debug('Found document for prisoner %s: %s' % (prisoner_uri, document_uri))

            label = '{prefix} {id}'.format(prefix=label_map.get(directory, 'Dokumentti'), id=prisoner_id)

            documents.add((document_uri, SKOS.prefLabel, Literal(label)))
            documents.add((document_uri, RDF.type, SCHEMA_WARSA.PersonDocument))
            documents.add((document_uri, URIRef('http://schema.org/contentUrl'), file_url))

    log.info('Found %s document links, with %s unidentified references' % (len(links), unidentified_references))

    return links, documents


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("task", help="Linking task to perform",
                           choices=["camps", "occupations", "municipalities", "persons", "ranks", "sotilaan_aani",
                                    "person_documents"])
    argparser.add_argument("input", help="Input RDF file")
    argparser.add_argument("output", help="Output file location")
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")
    argparser.add_argument("--loglevel", default='INFO', help="Logging level, default is INFO.",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--endpoint", default='http://localhost:3030/warsa/sparql', help="SPARQL Endpoint")
    argparser.add_argument("--arpa", type=str, help="ARPA instance URL for linking")
    argparser.add_argument("--output2", type=str, help="Additional output file (media document metadata)")

    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    input_graph = Graph()
    input_graph.parse(args.input, format=guess_format(args.input))

    if args.task == 'camps':
        log.info('Linking camps and hospitals')
        bind_namespaces(link_camps(input_graph, args.endpoint)).serialize(args.output, format=guess_format(args.output))

    elif args.task == 'municipalities':
        log.info('Linking municipalities')
        bind_namespaces(link_municipalities(input_graph, args.endpoint, args.arpa)).serialize(args.output, format=guess_format(args.output))

    elif args.task == 'occupations':
        log.info('Linking occupations')
        bind_namespaces(link_occupations(input_graph, args.endpoint, SCHEMA_POW.occupation_literal, BIOC.has_occupation,
                                         SCHEMA_WARSA.PrisonerRecord, score_threshold=0.84)).serialize(args.output, format=guess_format(args.output))

    elif args.task == 'persons':
        log.info('Linking persons')
        bind_namespaces(link_prisoners(input_graph, args.endpoint)).serialize(args.output, format=guess_format(args.output))

    elif args.task == 'ranks':
        log.info('Linking ranks')
        bind_namespaces(link_ranks(input_graph, args.endpoint, SCHEMA_POW.rank_literal, SCHEMA_POW.rank,
                                   SCHEMA_WARSA.PrisonerRecord)).serialize(args.output, format=guess_format(args.output))

    elif args.task == 'sotilaan_aani':
        log.info('Linking Sotilaan Ääni magazines')
        document_links, documents = link_sotilaan_aani(input_graph, 'data/SÄ-indeksi.csv')
        bind_namespaces(document_links).serialize(args.output, format=guess_format(args.output))
        bind_namespaces(documents).serialize(args.output2, format=guess_format(args.output2))

    elif args.task == 'person_documents':
        log.info('Linking person documents')
        document_links, documents = link_person_documents(input_graph)
        bind_namespaces(document_links).serialize(args.output, format=guess_format(args.output))
        bind_namespaces(documents).serialize(args.output2, format=guess_format(args.output2))
