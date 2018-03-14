#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Mapping of CSV columns to RDF properties
"""
from datetime import date, datetime
from functools import partial

from converters import convert_dates, strip_dash, convert_swedish
from namespaces import SCHEMA_NS, BIOC, WARSA_NS

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
            'name_en': 'Date of birth',
            'description_fi': 'Henkilön syntymäaika muodossa pp.kk.vvvv',
        },
    'synnyinkunta':
        {
            'uri': WARSA_NS.birth_place_literal,
            'value_separator': '/',
            'name_fi': 'Syntymäkunta',
            'name_en': 'Municipality of birth',
            'description_fi': 'Henkilön syntymäkunta',
        },
    'kotikunta':
        {
            'uri': SCHEMA_NS.home_place_literal,
            'value_separator': '/',
            'name_fi': 'Kotikunta',
            'name_en': 'Home municipality',
            'description_fi': 'Kunta, jossa henkilö on ollut kirjoilla vangitsemishetkellä',
        },
    'asuinkunta':
        {
            'uri': SCHEMA_NS.residence_place,
            'name_fi': 'Asuinpaikka',
            'name_en': 'Municipality of residence',
            'value_separator': '/',
            'description_fi': 'Kunta, jossa henkilö on tosiasiassa asunut sotaan lähtiessä. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai on lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta, KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24–KA-T 26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
        },
    'kuolinkunta, palanneet':
        {
            'uri': SCHEMA_NS.municipality_of_death,
            'name_en': 'Municipality of death',
            'name_fi': 'Kuolinkunta'
        },
    'ammatti':
        {
            'uri': SCHEMA_NS.occupation_literal,
            'name_fi': 'Ammatti',
            'name_en': 'Occupation',
            'value_separator': '/',
            'description_fi': 'Ammatti, jota henkilö on harjoittanut ennen vangitsemista. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta, KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
        },
    'siviilisääty':
        {
            'uri': SCHEMA_NS.marital_status,
            'name_fi': 'Siviilisääty',
            'name_en': 'Marital status',
            'value_separator': '/',
            'description_fi': 'Henkilön tiedossa oleva siviilisääty vangitsemishetkellä. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta, KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA-T 26073/49, Kansallisarkisto kantakortit',
        },
    'lasten lkm':
        {
            'uri': SCHEMA_NS.amount_children,
            'converter': strip_dash,
            'name_fi': 'Lasten lukumäärä',
            'name_en': 'Amount of children',
            'value_separator': '/',
            'description_fi': 'Henkilön lasten tiedossa oleva lukumäärä vangitsemishetkellä. Vankeuden jälkeen syntyneistä lapsista ei ole kerätty tietoa. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta',
        },
    'sotilasarvo':
        {
            'uri': SCHEMA_NS.rank,
            'name_fi': 'Sotilasarvo',
            'name_en': 'Military rank',
            'value_separator': '/',
            'description_fi': 'Henkilön sotilasarvo vangitsemishetkellä. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta, KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
        },
    'joukko-osasto':
        {
            'uri': SCHEMA_NS.unit,
            'name_en': 'Military unit',
            'name_fi': 'Joukko-osasto',
            'description_fi': 'Henkilön tiedossa oleva joukko-osasto vangitsemishetkellä',
        },
    'katoamisaika':
        {
            'uri': SCHEMA_NS.time_gone_missing,
            'converter': convert_dates,
            'validator': validate_dates,
            'value_separator': '/',
            'name_en': 'Date of going missing',
            'name_fi': 'Katoamispäivä',
            'description_fi': 'Päivä, jona henkilö on suomalaisten lähteiden mukaan kadonnut. Päivämäärät ilmoitetaan muodossa pp.kk.vvvv',
        },
    'katoamispaikka':
        {
            'uri': SCHEMA_NS.place_gone_missing,
            'value_separator': '/',
            'name_en': 'Place of going missing',
            'name_fi': 'Katoamispaikka',
            'description_fi': 'Paikka, jossa henkilö on suomalaisten lähteiden mukaan kadonnut',
        },
    'vangiksi aika':
        {
            'uri': SCHEMA_NS.time_captured,
            'converter': convert_dates,
            'validator': validate_dates,
            'value_separator': '/',
            'name_en': 'Date of capture',
            'name_fi': 'Vangiksi jäämisen päivämäärä',
            'description_fi': 'Päivä, jona henkilö on suomalaisten lähteiden mukaan kadonnut. Päivämäärät ilmoitetaan muodossa pp.kk.vvvv',
        },
    'vangiksi paikka, kunta':
        {
            'uri': SCHEMA_NS.place_captured_municipality,
            'value_separator': '/',
            'name_en': 'Municipality of capture',
            'name_fi': 'Vangiksi jäämisen kunta',
            'description_fi': 'Kunta, jonka alueella henkilö on jäänyt sotavangiksi. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
        },
    'vangiksi paikka, kylä, kaupunginosa':
        {
            'uri': SCHEMA_NS.place_captured,
            'value_separator': '/',
            'name_en': 'Village or district of capture',
            'name_fi': 'Vangiksi jäämisen kylä tai kaupunginosa',
            'description_fi': 'Kylä tai kaupunginosa, jossa henkilö on jäänyt sotavangiksi. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
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
            'name_fi': 'Selvitys vangiksi jäämisestä',
            'description_fi': 'Tieto siitä, miten henkilö on jäänyt vangiksi joko hänen oman kertomansa tai muun lähteen mukaan. Lähteinä ilman erillistä merkintää KA T-26073/1, KA T-26073/2–KA T-26073/22, KA T-26073/23, KA T-26073/24-KA T-26073/47, KA T-26073/48, KA T-26073/49, Kansallisarkisto kantakortit',
        },
    'palannut':
        {
            'uri': SCHEMA_NS.returned_date,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date(1980, 1, 1)),
            'value_separator': '/',
            'name_en': 'Date of return',
            'name_fi': 'Palaamisaika',
            'description_fi': 'Päivä, jona henkilö on palannut Suomeen sotavankeudesta'
        },
    'kuollut':
        {
            'uri': SCHEMA_NS.death_date,
            'converter': convert_dates,
            'validator': partial(validate_dates, after=date(1939, 11, 30), before=date.today()),
            'value_separator': '/',
            'name_en': 'Date of death',
            'name_fi': 'Kuolinpäivä',
            'description_fi': 'Henkilön tiedossa oleva kuolinpäivä muodossa pp.kk.vvvv. Mikäli lähdettä ei ole mainittu, ovat käytetyt lähteet tiedosta yksimielisiä tai lähde on Kansallisarkisto: Suomen sodissa 1939–1945 menehtyneiden tietokanta.',
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
            'name_fi': 'Kuolinpaikka',
            'description_fi': 'Sotavankeuden jälkeen kuolleen henkilön kuolinpaikka. Jollei lähdettä ole erikseen mainittu, on lähde Väestörekisterikeskuksen Väestötietojärjestelmä (VTJ)',
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
            'name_fi': 'Vankeuspaikat',
            'description_fi': 'Ne kuulustelupaikat, vankileirit, vankilat ja sairaalat, joissa vanki on eri lähteistä saatujen tietojen mukaan ollut sotavankeusaikanaan sekä kussakin paikassa oleskelun päivämäärät.  Leirin tai sairaalan numeroa klikkaamalla näet sen tiedossa olevan sijainnin ja mahdolliset muut tiedot. Mikäli vankeuspaikkamerkintää ei voi klikata, on se tuntematon (esim. tiedossa on vankeuspaikan paikkakunta, mutta ei virallista numeroa tai nimeä)',
        },
    'muita tietoja':
        {
            'uri': SCHEMA_NS.other_information,
            'value_separator': ';',
            'name_fi': 'Muita vankeustietoja',
            'name_en': 'Other information',
            'description_fi': 'Muita sotavankeuteen liittyviä tietoja',
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
            'name_en': 'Radio reports',
            'name_fi': 'PM:n valvontatoimiston radiokatsaukset',
            'description_fi': 'Neuvostoliitto lähetti suomenkielisiä propagandalähetyksiä sekä talvi- että jatkosodan aikana, enimmillään 14 lähetystä päivässä. Lähetysasemat sijaitsivat Leningradissa, Moskovassa, Petroskoissa, Karhumäessä ja Sorokassa (Belomorsk). Kadonneiden omaisille radiolähetykset olivat tärkeitä siksi, että niissä luettiin sotavankien kirjeitä ja terveisiä omaisilleen sekä varsinkin kesällä 1944 vankeuteen joutuneiden luetteloja. Joskus lähetettiin myös leireillä levytettyjä haastatteluja. Suomessa lähetysten kuuntelu oli Päämajan valvontatoimiston tehtävänä. Valvontatoimisto laati sotavankinimistä luetteloja jo seuraavaksi päiväksi, viikonlopun jälkeen ensimmäiseksi arkipäiväksi.',
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
    'vankeudessa takavarikoitu omaisuus markoissa':
        {
            'uri': SCHEMA_NS.confiscated_possession,
            'name_en': 'Confiscated possessions in prisonment',
            'name_fi': 'Vankeudessa takavarikoitu omaisuus markoissa',
            'description_fi': 'Jatkosodan toisen (25.12.1944) ja kolmannen (28.3.1945) palautuserän sotavangeille tehty erillinen kysymys. Lähteinä KA T-26073/2–KA T-26073/22',
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
    'Neuvostoliittolaiset sotavankikortistot ja henkilömappikokoelmat':
        {
            'uri': SCHEMA_NS.soviet_card_files,
            'name_en': 'Soviet prisoner of war card files and person registers',
            'name_fi': 'Neuvostoliittolaiset sotavankikortistot ja henkilömappikokoelmat',
            'desciption_fi': 'Talvisodan kortisto, Jatkosodan kortisto, Palautettujen henkilömapit, Sotavankeudessa kuolleiden henkilömapit, Vangittujen ja internoitujen henkilömapit. Mikäli korttien tai mappien lukumäärää ei ole mainittu, on kyseisessä kokoelmassa yksi vankia koskeva kortti tai mappi. Mikäli henkilömapin sisältöä ei ole lueteltu, sisältää mappi vain ns. kuulustelulomakkeen. Kokoelmia voi selata Digitaaliarkistossa Kansallisarkiston toimipisteiden yleisöpäätteillä, haku vangin nimellä. Vangittujen ja internoitujen henkilömappien selailu vaatii erillisen luvan hakemista. Asiakirjat ovat pääosin venäjänkielisiä.',
        },
    'Jatkosodan VEN henkilömapit, kuolleet F 465':
        {
            'uri': SCHEMA_NS.continuation_war_russian_card_file_F_465,
            'value_separator': ';',
            'name_en': 'Continuation War Russian card file F 465',
            'name_fi': 'Kuolleiden jatkosodan venäjänkieliset kuulustelulomakkeet F 465'
        },
    'Jatkosodan VEN henkilömapit, tuomitut ja internoidut 461/p':
        {
            'uri': SCHEMA_NS.continuation_war_russian_card_file_461p,
            'name_en': 'Continuation War Russian card file 461/p',
            'name_fi': 'Jatkosodan internoitujen venäjänkieliset kuulustelulomakkeet 461/p'
        },
    'Talvisodan kokoelma':
        {
            'uri': SCHEMA_NS.winter_war_collection,
            'name_en': 'Winter War collection',
            'name_fi': 'Talvisodan kokoelma',
            'description_fi': 'Venäjän valtion sota-arkisto RGVA, Fondi 34980 Talvisodan kokoelma. Neuvostoliittolaisia talvisotaa koskevia asiakirjoja, jotka ovat selattavissa Digitaaliarkistossa Kansallisarkiston toimipisteiden yleisöpäätteillä. Asiakirjan hakuohje: tee Digitaaliarkiston etusivulla Aineiston haku esim. sanoilla ’talvisodan kokoelma’ -> klikkaa linkkiä ’RGVA Fondi 34980 Talvisodan kokoelma’ -> klikkaa ’asiakirjat’ -> valitse avautuvan sivun ylälaidasta ’kaikki’ -> tee haku sivulta painamalla ensin ctrl + f ja kirjoita hakuruutuun hakemasi arkistoyksikön numerotunnus muotoa x:xxx (tunnuksia on eripituisia) -> klikkaa oikeaa arkistoyksikköä, jolloin pääset selaamaan ko. kansiossa olevia asiakirjoja.',
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
            'uri': SCHEMA_NS.flyers,
            'value_separator': ';',
            'name_en': 'Flyers',
            'name_fi': 'Lentolehtiset',
            'description_fi': 'Neuvostoliittolaiset propagandalentolehtiset, joissa henkilö on mainittu',
        },
    'Sotilaan Ääni-lehti':
        {
            'uri': SCHEMA_NS.sotilaan_aani,
            'value_separator': ';',
            'name_en': 'Sotilaan Ääni magazine',
            'name_fi': 'Sotilaan Ääni'
        },
    'Kansan Valta -lehti, Kansan  Mies -lehti, Kansan Ääni':
        {
            'uri': SCHEMA_NS.propaganda_magazine,
            'value_separator': ';',
            'name_en': 'Propaganda magazine',
            'name_fi': 'Propagandalehti',
            'description_fi': 'Neuvostoliittolaiset suomen- ja venäjänkieliset propagandalehdet (pl. Sotilaan Ääni), joissa henkilö on mainittu.',
        },
    'muistelmat, lehtijutut, tietokirjat, tutkimukset, Kansa taisteli-lehti, näyttelyt':
        {
            'uri': SCHEMA_NS.memoirs,
            'value_separator': ';',
            'name_en': 'Memoirs',
            'name_fi': 'Muistelmat, lehtiartikkelit ja kirjallisuus',
            'description_fi': 'Kirjallisissa lähteissä olevat maininnat henkilön sotavankeudesta',
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
