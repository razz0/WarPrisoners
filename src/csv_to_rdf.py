#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Convert Prisoners of War from CSV to RDF using CIDOC CRM.
"""

import argparse
import datetime
import logging
import re
from functools import partial

import pandas as pd
from slugify import slugify

from converters import convert_person_name, convert_dates
from csv2rdf import CSV2RDF
from mapping import PRISONER_MAPPING, SOURCE_MAPPING
from namespaces import RDF, XSD, DCT, SKOS, DATA_NS, SCHEMA_POW, SCHEMA_WARSA, bind_namespaces
from rdflib import URIRef, Graph, Literal, Namespace
from rdflib.term import Identifier

from validators import validate_person_name, validate_dates


def get_triple_reifications(graph, triple):
    found_reifications = Graph()
    s, p, o = triple
    reifications = list(graph.subjects(RDF.subject, s))
    for reification in reifications:
        if not (graph[reification:RDF.predicate:p] and graph[reification:RDF.object:o]):
            continue
        for (rs, rp, ro) in graph.triples((reification, None, None)):
            found_reifications.add((rs, rp, ro))

    return found_reifications


def get_person_related_triples(graph, person):
    found_triples = Graph()
    for (s, p, o) in graph.triples((person, None, None)):
        found_triples.add((s, p, o))
        for (s2, p2, o2) in graph.triples((o, None, None)):
            found_triples.add((s2, p2, o2))
        found_triples += get_triple_reifications(graph, (s, p, o))

    return found_triples


class RDFMapper:
    """
    Map tabular data (currently pandas DataFrame) to RDF. Create a class instance of each row.
    """

    def __init__(self, mapping, instance_class, loglevel='WARNING'):
        self.mapping = mapping
        self.instance_class = instance_class
        self.table = None
        self.data = Graph()
        self.schema = Graph()
        # self.errors = pd.DataFrame(columns=['nro', 'sarake', 'virhe', 'arvo'])
        self.errors = []

        logging.basicConfig(filename='output/logs/prisoners.log',
                            filemode='a',
                            level=getattr(logging, loglevel),
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.log = logging.getLogger(__name__)

    def read_value_with_source(self, orig_value):
        """
        Read a value with source given in the end in parenthesis

        :param orig_value: string in format "value (source)"
        :return: value, sources, erroneous content
        """

        sourcematch = re.search(r'(.+) \(([^()]+)\)(.*)', orig_value)
        (value, sources, trash) = sourcematch.groups() if sourcematch else (orig_value, None, None)

        if sources:
            # if ',' in sources:
            #     print(sources)
            # self.log.debug('Found sources: %s' % sources)
            # sources = [s.strip() for s in sources.split(',')]
            sources = [sources.strip()]

        if trash:
            self.log.warning('Found some content after sources, reverting to original: %s' % orig_value)
            value = orig_value

        return value.strip(), sources or [], trash or ''

    def read_semicolon_separated(self, orig_value: str):
        """
        Read semicolon separated values (with possible sources and date range)

        :param orig_value: string in format "source: value date1-date2", or just "value"
        :return: value, sources, date begin, date end, error
        """

        date_validator = partial(validate_dates, before=datetime.date(1960, 1, 1))

        errors = []
        if ': ' in orig_value:
            (sources, value) = orig_value.split(': ', maxsplit=1)
        else:
            (sources, value) = ('', orig_value)

        if ': ' in value:
            errors.append('Mahdollinen virhe kentän arvossa, ": " löytyy lähdeviitteen jälkeen')
            (sources, value) = ('', orig_value)

        datematch = re.search(r'(.+) ([0-9xX.]{5,})-([0-9xX.]{5,})', value)
        (value, date_begin, date_end) = datematch.groups() if datematch else (value, None, None)

        if date_begin:
            date_begin = convert_dates(date_begin)
            error = date_validator(date_begin, None)
            if error:
                errors.append(error)

        if date_end:
            date_end = convert_dates(date_end)
            error = date_validator(date_end, None)
            if error:
                errors.append(error)

        if sources:
            # if ',' in sources:
            #     print(sources)
            #
            # self.log.debug('Found sources: %s' % sources)
            # sources = [s.strip() for s in sources.split(',')]
            sources = [sources.strip()]

        if date_begin or date_end:
            self.log.debug('Found dates for value %s: %s - %s' % (value, date_begin, date_end))

        return value, sources or [], date_begin, date_end, errors

    def create_resource(self, resource_uri, rdf_class, rdf_value, value_property, label_fi: str, label_en: str, capture_order,
                        capture_dates, order, date_begin, date_end, resource_name):
        """
        Create a resource based on a CSV column
        """
        resource_rdf = Graph()

        resource_rdf.add((resource_uri, RDF.type, rdf_class))
        resource_rdf.add((resource_uri, value_property, rdf_value))

        resource_rdf.add((resource_uri, SKOS.prefLabel, Literal(label_fi.format(person=resource_name), lang='fi')))
        resource_rdf.add((resource_uri, SKOS.prefLabel, Literal(label_en.format(person=resource_name), lang='en')))

        if capture_order:
            resource_rdf.add((resource_uri, SCHEMA_POW.order, order))

        if capture_dates and (date_begin or date_end):
            resource_rdf.add((resource_uri, SCHEMA_POW.date_begin, Literal(date_begin)))
            resource_rdf.add((resource_uri, SCHEMA_POW.date_end, Literal(date_end)))

        return resource_rdf

    def map_row_to_rdf(self, entity_uri, row, prisoner_number=None):
        """
        Map a single row to RDF.

        :param entity_uri: URI of the instance being created
        :param row: tabular data
        :param prisoner_number:
        :return:
        """
        resource_template = '{entity}_{prop}_{id}'
        reification_template = '{entity}_{prop}_{id}_reification_{reason}'
        row_rdf = Graph()
        row_errors = []
        unmapped_columns = set()

        # Handle first and last names

        (firstnames, lastname, fullname) = convert_person_name(row[0])
        error = validate_person_name(' '.join((lastname, firstnames)) if firstnames else lastname, row[0])

        original_name = row[0].strip()
        if error:
            row_errors.append([prisoner_number, fullname, 'sukunimi ja etunimet', error, row[0]])

        if firstnames:
            row_rdf.add((entity_uri, SCHEMA_WARSA.given_names, Literal(firstnames)))
        if lastname:
            row_rdf.add((entity_uri, SCHEMA_WARSA.family_name, Literal(lastname)))
        if fullname:
            row_rdf.add((entity_uri, URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'), Literal(fullname)))
        if original_name:
            row_rdf.add((entity_uri, SCHEMA_POW.original_name, Literal(original_name)))

        # Loop through the mapping dict and convert data to RDF
        for column_name in row.index[1:]:

            mapping = self.get_mapping(column_name)
            if not mapping:
                unmapped_columns.add(column_name)
                continue

            value = row[column_name]
            separator = mapping.get('value_separator')

            # Make an iterable of all values in this field

            # values = (val.strip() for val in re.split(r'\s/\s', str(value))) if separator == '/' else \
            if separator == '/':
                values = (val.strip() for val in re.split(r'(?: /)|(?:/ )', str(value)) if val)
            elif separator == ';':
                values = (val.strip() for val in re.split(';', str(value)) if val)
            else:
                values = [str(value).strip()]

            for index, value in enumerate(values):

                sources = []
                date_begin = None
                date_end = None
                trash = None
                sep_errors = []
                original_value = value

                if separator == '/':
                    value, sources, trash = self.read_value_with_source(value)
                elif separator == ';':
                    value, sources, date_begin, date_end, sep_errors = self.read_semicolon_separated(value)

                # temp = [s for s in sources if ',' in s]
                # if temp:
                #     print(temp)

                if trash:
                    sep_errors = ['Ylimääräisiä merkintöjä suluissa annetun lähteen jälkeen: %s' % original_value]
                for sep_error in sep_errors:
                    row_errors.append([prisoner_number, fullname, column_name, sep_error, original_value])

                converter = mapping.get('converter')
                validator = mapping.get('validator')
                value = converter(value) if converter else value
                conv_error = validator(value, original_value) if validator else None

                if conv_error and not sep_errors:
                    row_errors.append([prisoner_number, fullname, column_name, conv_error, original_value])

                if value:
                    if isinstance(value, Identifier):
                        rdf_value = value
                    else:
                        rdf_value = Literal(value, datatype=XSD.date) if type(value) == datetime.date else Literal(value)

                    if mapping.get('create_resource'):
                        resource_uri = DATA_NS[resource_template.format(entity=entity_uri.split('/')[-1],
                                                                        prop=mapping['uri'].split('/')[-1],
                                                                        id=index * 10)]

                        row_rdf += self.create_resource(resource_uri, mapping['create_resource'], rdf_value,
                                                        mapping['capture_value'], mapping['create_resource_label_fi'],
                                                        mapping['create_resource_label_en'],
                                                        mapping.get('capture_order_number'),
                                                        mapping.get('capture_dates'), Literal(index * 10),
                                                        date_begin, date_end, original_name)

                        rdf_value = resource_uri

                    row_rdf.add((entity_uri, mapping['uri'], rdf_value))

                    for source in sources:
                        reification_uri = DATA_NS[reification_template.format(entity=entity_uri.split('/')[-1],
                                                                              prop=mapping['uri'].split('/')[-1],
                                                                              id=index,
                                                                              reason='source')]
                        row_rdf.add((reification_uri, RDF.subject, entity_uri))
                        row_rdf.add((reification_uri, RDF.predicate, mapping['uri']))
                        row_rdf.add((reification_uri, RDF.object, rdf_value))
                        row_rdf.add((reification_uri, RDF.type, RDF.Statement))
                        row_rdf.add((reification_uri, DCT.source, Literal(source)))

        if row_rdf:
            row_rdf.add((entity_uri, RDF.type, self.instance_class))
        else:
            # Don't create class instance if there is no data about it
            logging.debug('No data found for {uri}'.format(uri=entity_uri))
            row_errors.append([prisoner_number, fullname, '', 'Ei tietoa henkilöstä', ''])

        # self.errors = self.errors.append(pd.DataFrame(data=row_errors, columns=self.errors.columns))
        for error in row_errors:
            self.errors.append(error)

        logging.debug('Unmapped columns: %s' % '\n'.join(sorted(unmapped_columns)))

        return row_rdf

    def get_mapping(self, column_name: str):
        """
        Get mapping for column name
        """
        mapping = self.mapping.get(column_name)
        if not mapping:
            column_name = column_name.split('(')[0].strip()
            mapping = self.mapping.get(column_name)
        return mapping

    def read_csv(self, csv_input):
        """
        Read in a CSV files using pandas.read_csv

        :param csv_input: CSV input (filename or buffer)
        """
        csv_data = pd.read_csv(csv_input, encoding='UTF-8', index_col=False, sep=',', quotechar='"',
                               # parse_dates=[1], infer_datetime_format=True, dayfirst=True,
                               na_values=[' '],
                               converters={
                                   'ammatti': lambda x: x.lower(),
                                   0: lambda x: int(x) if x and x.isnumeric() else -1
                               })

        self.table = csv_data.fillna('').applymap(lambda x: x.strip() if type(x) == str else x)
        logging.info('Read {num} rows from CSV'.format(num=len(self.table)))

    def preprocess_prisoners_data(self):
        self.table.rename(columns={'Unnamed: 0': 'nro'}, inplace=True)
        missing_ids = self.table[self.table.nro < 0]
        self.table = self.table[self.table.nro >= 0]

        logging.info(f'Table contains {len(list(self.table))} columns')

        for missing in missing_ids['sukunimi ja etunimet']:
            logging.warning('Person with name %s missing id number' % missing)

        logging.info('After pruning rows without proper index, {num} rows remaining'.format(num=len(self.table)))

    def serialize(self, destination_data, destination_schema):
        """
        Serialize RDF graphs

        :param destination_data: serialization destination for data
        :param destination_schema: serialization destination for schema
        :return: output from rdflib.Graph.serialize
        """
        data = bind_namespaces(self.data).serialize(format="turtle", destination=destination_data)
        schema = bind_namespaces(self.schema).serialize(format="turtle", destination=destination_schema)
        self.log.info('Data serialized to %s' % destination_data)
        self.log.info('Schema serialized to %s' % destination_schema)

        return data, schema  # Return for testing purposes

    def process_rows(self):
        """
        Loop through CSV rows and convert them to RDF
        """
        used_ids = []
        for index in self.table.index:
            prisoner_number = str(self.table.ix[index][0])
            while prisoner_number in used_ids:
                prisoner_number += '_duplicate'
            used_ids.append(prisoner_number)
            prisoner_uri = DATA_NS['prisoner_' + prisoner_number]
            row_rdf = self.map_row_to_rdf(prisoner_uri, self.table.ix[index][1:], prisoner_number=prisoner_number)
            if row_rdf:
                self.data += row_rdf

        for prop in self.mapping.values():
            self.schema.add((prop['uri'], RDF.type, RDF.Property))
            if 'name_fi' in prop:
                self.schema.add((prop['uri'], SKOS.prefLabel, Literal(prop['name_fi'], lang='fi')))
            if 'name_en' in prop:
                self.schema.add((prop['uri'], SKOS.prefLabel, Literal(prop['name_en'], lang='en')))
            if 'description_fi' in prop:
                self.schema.add((prop['uri'], DCT.description, Literal(prop['description_fi'], lang='fi')))

    def write_errors(self):
        """Write conversion errors to a CSV file"""
        error_df = pd.DataFrame(columns=['nro', 'nimi', 'sarake', 'virhe', 'arvo'], data=self.errors)
        error_df.to_csv('output/errors.csv', ',', index=False)


def convert_camps(class_uri, prop1, prop2, namespace):
    mapper = CSV2RDF()
    mapper.read_csv(args.input, sep=',')
    mapper.convert_to_rdf(DATA_NS, SCHEMA_POW, class_uri)

    for old_uri in list(mapper.data.subjects(RDF.type, class_uri)):
        new_uri = slugify(mapper.data.value(old_uri, prop1, default='')
                          or mapper.data.value(old_uri, prop2, default='') or 'unknown')
        new_uri = namespace[new_uri]
        logging.debug(f'Minted new URI for POW camp/hospital: {old_uri}  -->  {new_uri}')
        for (sub, pre, obj) in mapper.data.triples((old_uri, None, None)):
            mapper.data.add((new_uri, pre, obj))

        for (sub, pre, obj) in mapper.data.triples((old_uri, None, None)):
            mapper.data.remove((old_uri, pre, obj))

    mapper.write_rdf(args.outdata, args.outschema, fformat='turtle')


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Process war prisoners CSV", fromfile_prefix_chars='@')

    argparser.add_argument("mode", help="CSV conversion mode", default="PRISONERS",
                           choices=["PRISONERS", "CAMPS", "HOSPITALS"])
    argparser.add_argument("input", help="Input CSV file")
    argparser.add_argument("--outdata", help="Output file to serialize RDF dataset to (.ttl)", default=None)
    argparser.add_argument("--outschema", help="Output file to serialize RDF schema to (.ttl)", default=None)
    argparser.add_argument("--loglevel", default='INFO', help="Logging level, default is INFO.",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    args = argparser.parse_args()

    if args.mode == "PRISONERS":
        pow_mapper = RDFMapper(PRISONER_MAPPING, SCHEMA_WARSA.PrisonerRecord, loglevel=args.loglevel.upper())
        pow_mapper.read_csv(args.input)
        pow_mapper.preprocess_prisoners_data()

        pow_mapper.process_rows()
        pow_mapper.write_errors()

        pow_mapper.serialize(args.outdata, args.outschema)

    elif args.mode == "CAMPS":
        convert_camps(SCHEMA_WARSA.PowCamp,
                      SCHEMA_POW['vankeuspaikan-numero'],
                      SCHEMA_POW['vankeuspaikka'],
                      Namespace('http://ldf.fi/warsa/prisoners/camp_'))

    elif args.mode == "HOSPITALS":
        convert_camps(SCHEMA_WARSA.PowHospital,
                      SCHEMA_POW['sairaala'],
                      SCHEMA_POW['sijainti'],
                      Namespace('http://ldf.fi/warsa/prisoners/hospital_'))

    elif args.mode == "SOURCES":
        mapper = CSV2RDF(mapping=SOURCE_MAPPING)
        mapper.read_csv(args.input, sep=',')
        mapper.convert_to_rdf(Namespace("http://ldf.fi/warsa/prisoners/"),
                              Namespace("http://ldf.fi/schema/warsa/prisoners/"),
                              SCHEMA_WARSA.OriginalSource)
        mapper.write_rdf(args.outdata, args.outschema, fformat='turtle')
