#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Mapping of CSV columns to RDF properties
"""
from datetime import date, datetime
from functools import partial

from converters import convert_dates, strip_dash, convert_swedish
from namespaces import SCHEMA_NS, BIOC

from validators import validate_dates, validate_mother_tongue

# CSV column mapping. Person name and person index number are taken separately.

PRISONER_MAPPING = {
    'syntymäaika':
        {
            'uri': SCHEMA_NS.birth_date,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1860, 1, 1), before=date(1935, 1, 1)),
            'value_separator': '/',
            'name_fi': 'Syntymäaika',
            'name_en': 'Date of birth'
        },
    'synnyinkunta':
        {
            'uri': SCHEMA_NS.birth_place,
            'value_separator': '/',
            'name_fi': 'Syntymäkunta',
            'name_en': 'Municipality of birth'
        },
    'kotikunta':
        {
            'uri': SCHEMA_NS.home_place,
            'value_separator': '/',
            'name_fi': 'Kotikunta',
            'name_en': 'Home municipality'
        },
    'asuinkunta':
        {
            'uri': SCHEMA_NS.residence_place,
            'name_fi': 'Asuinpaikka',
            'name_en': 'Municipality of residence',
            'value_separator': '/'
        },
    'kuolinkunta, palanneet':
        {
            'uri': SCHEMA_NS.municipality_of_death,
            'name_en': 'Municipality of death',
            'name_fi': 'Kuolinkunta'
        },
    'ammatti':
        {
            'uri': BIOC.has_occupation,
            'name_fi': 'Ammatti',
            'name_en': 'Occupation',
            'value_separator': '/'
        },
    'siviilisääty':
        {
            'uri': SCHEMA_NS.marital_status,
            'name_fi': 'Siviilisääty',
            'name_en': 'Marital status',
            'value_separator': '/'
        },
    'lasten lkm':
        {
            'uri': SCHEMA_NS.amount_children,
            'converter': strip_dash,
            'name_fi': 'Lasten lukumäärä',
            'name_en': 'Amount of children',
            'value_separator': '/'
        },
    'sotilasarvo':
        {
            'uri': SCHEMA_NS.rank,
            'name_fi': 'Sotilasarvo',
            'name_en': 'Military rank',
            'value_separator': '/'
        },
    'joukko-osasto':
        {
            'uri': SCHEMA_NS.unit,
            'name_en': 'Military unit',
            'name_fi': 'Joukko-osasto'
        },
    'katoamisaika':
        {
            'uri': SCHEMA_NS.time_gone_missing,
            'converter': convert_dates,
            'validator': validate_dates,
            'value_separator': '/',
            'name_en': 'Date of disappearance',
            'name_fi': 'Katoamispäivä'
        },
    'vangiksi aika':
        {
            'uri': SCHEMA_NS.time_captured,
            'converter': convert_dates,
            'validator': validate_dates,
            'value_separator': '/',
            'name_en': 'Date of capture',
            'name_fi': 'Vangiksi jäämisen päivämäärä'
        },
    'vangiksi paikka, kunta':
        {
            'uri': SCHEMA_NS.place_captured_municipality,
            'value_separator': '/',
            'name_en': 'Municipality of capture',
            'name_fi': 'Vangiksi jäämisen kunta'
        },
    'vangiksi paikka, kylä, kaupunginosa':
        {
            'uri': SCHEMA_NS.place_captured,
            'value_separator': '/',
            'name_en': 'Place of capture',
            'name_fi': 'Vangiksi jäämisen paikka'
        },
    'vangiksi, taistelupaikka':
        {
            'uri': SCHEMA_NS.place_captured_battle,
            'value_separator': '/',
            'name_en': 'Location of battle in which captured',
            'name_fi': 'Vangiksi jäämisen taistelupaikka'
        },
    'selvitys vangiksi jäämisestä':
        {
            'uri': SCHEMA_NS.explanation,
            'value_separator': ';',
            'name_en': 'Description of capture',
            'name_fi': 'Selvitys vangiksi jäämisestä'
        },
    'palannut':
        {
            'uri': SCHEMA_NS.returned_date,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date(1980, 1, 1)),
            'value_separator': '/',
            'name_en': 'Date of return',
            'name_fi': 'Palaamisaika'
        },
    'kuollut':
        {
            'uri': SCHEMA_NS.death_date,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date.today()),
            'value_separator': '/',
            'name_en': 'Date of death',
            'name_fi': 'Kuolinaika'
        },
    'kuolinsyy':
        {
            'uri': SCHEMA_NS.cause_of_death,
            'name_en': 'Cause of death',
            'name_fi': 'Kuolinsyy'
        },
    'kuolinpaikka':
        {
            'uri': SCHEMA_NS.death_place,  # epämääräinen muotoilu
            'value_separator': '/',
            'name_en': 'Place of death',
            'name_fi': 'Kuolinpaikka'
        },
    'hautauspaikka':
        {
            'uri': SCHEMA_NS.burial_place,
            'value_separator': ';',
            'name_en': 'Place of burial',
            'name_fi': 'Hautauspaikka'
        },
    'vankeuspaikat':
        {
            'uri': SCHEMA_NS.located_in,
            'value_separator': ';',
            'create_resource': SCHEMA_NS.Located_in,
            'capture_value': SCHEMA_NS.place,
            'capture_order_number': True,
            'capture_dates': True,
            'name_en': 'Captivity locations',
            'name_fi': 'Vankeuspaikat'
        },
    'muita tietoja':
        {
            'uri': SCHEMA_NS.other_information,
            'value_separator': ';',
            'name_fi': 'Muita tietoja',
            'name_en': 'Other information',
        },
    'palanneiden kuolinaika':
        {
            'uri': SCHEMA_NS.death_date,  # Property name given on previous usage
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date.today()),
            'value_separator': '/'
        },
    'kuolleeksi julistaminen':
        {
            'uri': SCHEMA_NS.declared_death,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date.today()),
            'name_en': 'Declared death',
            'name_fi': 'Kuolleeksi julistaminen'
        },
    'valokuva':
        {
            'uri': SCHEMA_NS.photograph,
            'value_separator': ';',
            'name_fi': 'Valokuva',
            'name_en': 'Photograph'
        },
    'suomalainen paluukuulustelupöytäkirja':
        {
            'uri': SCHEMA_NS.finnish_return_interrogation_file,
            'name_en': 'Finnish return interrogation file',
            'name_fi': 'Suomalainen paluukuulustelupöytäkirja'
        },
    # 'kantakortti':
    #     {
    #         'uri': SCHEMA_NS.military_record,
    #         'name_en': 'Military record',
    #         'name_fi': 'Kantakortti'
    #     },
    'radiossa, PM:n valvontatoimiston radiokatsaukset':
        {
            'uri': SCHEMA_NS.radio_report,
            'value_separator': ';',
            'name_en': 'Radio report',
            'name_fi': 'Radiokatsaus'
        },
    'Jatkosodan VEN henkilömapit F 473, palautetut':
        {
            'uri': SCHEMA_NS.russian_interrogation_sheets,
            'value_separator': ';',
            'name_en': 'Russian interrogation sheets',
            'name_fi': 'Jatkosodan venäläiset kuulustelulomakkeet'
        },
    'Talvisodan kortisto':
        {
            'uri': SCHEMA_NS.winterwar_card_file,
            'name_en': 'Winter War card file',
            'name_fi': 'Talvisodan kortisto'
        },
    'suomenruotsalainen':
        {
            'uri': SCHEMA_NS.mother_tongue,
            'converter': convert_swedish,
            'validator': validate_mother_tongue,
            'name_en': 'Mother tongue',
            'name_fi': 'Äidinkieli'
        },
    'Karagandan kortisto':
        {
            'uri': SCHEMA_NS.karaganda_card_file,
            'name_en': 'Karaganda card file',
            'name_fi': 'Karagandan kortisto'
        },
    'jatkosodan kortisto':
        {
            'uri': SCHEMA_NS.continuation_war_card_file,
            'name_en': 'Continuation War card file',
            'name_fi': 'Jatkosodan kortisto'
        },
    'Jatkosodan VEN henkilömapit, kuolleet F 465':
        {
            'uri': SCHEMA_NS.continuation_war_russian_card_file_F_465,
            'value_separator': ';',
            'name_en': 'Continuation War Russian card file F 465',
            'name_fi': 'Kuolleiden jatkosodan venäläiset kuulustelulomakkeet F 465'
        },
    'Jatkosodan VEN henkilömapit, vangitut ja internoidut 461/p':
        {
            'uri': SCHEMA_NS.continuation_war_russian_card_file_461p,
            'name_en': 'Continuation War Russian card file 461/p',
            'name_fi': 'Kuolleiden jatkosodan venäläiset kuulustelulomakkeet 461/p'
        },
    'Talvisodan kokoelma':
        {
            'uri': SCHEMA_NS.winter_war_collection,
            'name_en': 'Winter War collection',
            'name_fi': 'Talvisodan kokoelma'
        },
    'Talvisodan kokoelma, Moskovasta tulevat':
        {
            'uri': SCHEMA_NS.winter_war_collection_from_moscow,
            'value_separator': ';',
            'name_en': 'Winter War collection (Moscow)',
            'name_fi': 'Talvisodan kokoelma (Moskovasta)'
        },
    'lentolehtinen':
        {
            'uri': SCHEMA_NS.flyer,
            'value_separator': ';',
            'name_en': 'Flyer',
            'name_fi': 'Lentolehtinen'
        },
    'Sotilaan Ääni -lehti, Kansan Valta -lehti, Kansan  Mies -lehti':
        {
            'uri': SCHEMA_NS.propaganda_magazine,
            'value_separator': ';',
            'name_en': 'Propaganda magazine',
            'name_fi': 'Propagandalehti'
        },
    'muistelmat, lehtijutut, tietokirjat, tutkimukset, Kansa taisteli-lehti, näyttelyt':
        {
            'uri': SCHEMA_NS.memoirs,
            'value_separator': ';',
            'name_en': 'Memoirs',
            'name_fi': 'Muistelmat ja lehtijutut'
        },
    'TV-ja radio-ohjelmat, tallenne video/audio':
        {
            'uri': SCHEMA_NS.recording,
            'name_en': 'Recording (video/audio)',
            'name_fi': 'Tallenne (video/audio)'
        },
    'Karjalan kansallisarkiston dokumentit':
        {
            'uri': SCHEMA_NS.karelian_archive_documents,
            'name_en': 'Karelian archive documents',
            'name_fi': 'Karjalan kansallisarkiston dokumentit'
        },
}
