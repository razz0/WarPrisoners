#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Hide parts of personal information.
"""
import argparse
import logging
from datetime import date
from pprint import pprint

from dateutil import parser
from dateutil.relativedelta import relativedelta
from rdflib.util import guess_format

from namespaces import bind_namespaces, SCHEMA_WARSA, SCHEMA_POW
from rdflib import Graph, RDF, URIRef, Literal
from rdflib.compare import graph_diff, isomorphic

from csv_to_rdf import get_person_related_triples, get_triple_reifications

log = logging.getLogger(__name__)


def cast_date(orig_date: str):
    datestr = orig_date.strip('Xx-')
    cast = None

    try:
        cast = parser.parse(datestr).date()
    except ValueError:
        try:
            cast = parser.parse(datestr[-4:]).date()
        except ValueError:
            log.warning('Bad date: %s' % orig_date)

    return cast


def hide_health_information(graph: Graph, person: URIRef):
    """
    Hide health information of a person record
    """
    triples = list(graph.triples((person, SCHEMA_POW.cause_of_death, None)))
    triples += list(graph.triples((person, SCHEMA_POW.additional_information, None)))

    for triple in triples:
        log.debug('Removing triple and its reifications:  {spo}'.format(spo=str(triple)))
        reifications = get_triple_reifications(graph, triple)

        for reification in reifications:
            graph.remove(reification)

        graph.remove(triple)

    return graph


def hide_personal_information(graph: Graph, person: URIRef):
    """
    Hide personal information of a person record
    """
    # TODO

    return graph


def prune_persons(graph: Graph, endpoint: str):
    """
    Hide information of people in graph if needed
    """
    persons = list(graph.subjects(RDF.type, SCHEMA_WARSA.PrisonerRecord))

    log.info('Got %s person records for pruning' % len(persons))
    died_recently = []
    possibly_alive = []
    n_public = 0

    for person in persons:
        death_dates = list(graph.objects(person, SCHEMA_POW.date_of_death))
        death_dates = [cast_date(d) for d in death_dates]

        death_without_date = any(True for d in death_dates if d is None)
        death_dates = [d for d in death_dates if d is not None]

        if len(death_dates) > 1:
            log.info('Multiple death dates for %s  (using latest)' % person)

        death_date = sorted(death_dates)[-1] if death_dates else None

        if (death_date and (death_date >= date.today() - relativedelta(years=50))) or death_without_date:
            # All information is public
            died_recently.append(person)
        else:
            if not (death_date or death_without_date):
                dob = graph.value(person, SCHEMA_POW.date_of_birth)
                if dob and cast_date(dob) < date(1911, 1, 1):
                    possibly_alive.append(person)
            else:
                log.debug('Person record with death date %s declared public')
                n_public += 1

    # Health information is hidden
    for person in died_recently + possibly_alive:
        log.debug('Hiding health information of %s' % person)
        graph = hide_health_information(graph, person)
        graph.add((person, SCHEMA_POW.hide_documents, Literal(True)))

    # Personal information is hidden
    for person in possibly_alive:
        log.debug('Hiding personal information of %s' % person)
        graph = hide_personal_information(graph, person)

    log.info('Person that have died more than 50 years ago: %s' % n_public)
    log.info('Persons suspected to have died less than 50 years ago: %s' % len(died_recently))
    log.info('Persons that might be alive: %s' % len(possibly_alive))

    return graph


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    argparser.add_argument("input", help="Input RDFfile")
    argparser.add_argument("output", help="Output RDF file")
    argparser.add_argument("--endpoint", default='http://localhost:3030/warsa/sparql', help="SPARQL Endpoint")
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")
    argparser.add_argument("--loglevel", default='INFO', help="Logging level, default is INFO.",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    g = Graph()

    g.parse(args.input, format='turtle')

    bind_namespaces(prune_persons(g, args.endpoint)).serialize(args.output, format=guess_format(args.output))
