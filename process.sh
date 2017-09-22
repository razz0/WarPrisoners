#!/usr/bin/env bash

command -v s-put >/dev/null 2>&1 || { echo >&2 "s-put is not available, aborting"; exit 1; }
command -v rapper >/dev/null 2>&1 || { echo >&2 "rapper is not available, aborting"; exit 1; }

echo "Converting to csv" &&
libreoffice --headless --convert-to csv:"Text - txt - csv (StarCalc)":44,34,76,1,1,11,true data/prisoners.xls --outdir data &&
libreoffice --headless --convert-to csv:"Text - txt - csv (StarCalc)":44,34,76,1,1,11,true data/camps.xlsx --outdir data &&
libreoffice --headless --convert-to csv:"Text - txt - csv (StarCalc)":44,34,76,1,1,11,true data/hospitals.xlsx --outdir data &&

echo "Converting to ttl" &&
python csv_to_rdf.py CAMPS data/camps.csv --outdata=data/new/camps.ttl --outschema=data/new/camp_schema.ttl &&
python csv_to_rdf.py HOSPITALS data/hospitals.csv --outdata=data/new/camps2.ttl &&

sed -r -i 's/\/prisoners\/r\_/\/prisoners\/camp_/g' data/new/camps.ttl &&
sed -r -i 's/\/prisoners\/r\_/\/prisoners\/hospital_/g' data/new/camps2.ttl &&

cat data/new/camps.ttl data/new/camps2.ttl > data/new/camps.ttl &&
rm data/new/camps2.ttl &&

python csv_to_rdf.py PRISONERS data/prisoners.csv --outdata=data/new/prisoners_plain.ttl --outschema=data/new/schema.ttl &&

echo "Linking ranks" &&

python linker.py ranks data/new/prisoners_plain.ttl data/new/rank_links.ttl --endpoint "http://localhost:3030/warsa/sparql" &&

echo "Linking units" &&

cat data/new/prisoners_plain.ttl data/new/rank_links.ttl > data/new/prisoners_temp.ttl &&

# Updated data needed for unit linking
s-put http://localhost:3030/warsa/data http://ldf.fi/warsa/prisoners data/new/prisoners_temp.ttl &&

echo 'query=' | cat - sparql/period.sparql | sed 's/&/%26/g' | curl -d @- http://localhost:3030/warsa/sparql -v > data/new/periods.ttl &&

./link_units.sh &&

rm data/new/prisoners_temp.ttl &&

echo "Linking people" &&

cat data/new/prisoners_plain.ttl data/new/rank_links.ttl data/new/unit_linked_validated.ttl > data/new/prisoners_temp.ttl &&
python linker.py persons data/new/prisoners_temp.ttl data/new/persons_linked.ttl &&
rm data/new/prisoners_temp.ttl &&

sed -r 's/^(p:.*) cidoc:P70_documents (<.*>)/\2 cidoc:P70i_is_documented_in \1/' data/new/persons_linked.ttl > data/new/person_backlinks.ttl &&

# TODO: Link camps
# TODO: Link places using Arpa-linker

echo "Finishing prisoners" &&

cat data/new/prisoners_plain.ttl data/new/rank_links.ttl data/new/unit_linked_validated.ttl data/new/persons_linked.ttl > data/new/prisoners_full.ttl &&
rapper -i turtle data/new/prisoners_full.ttl -o turtle > data/new/prisoners.ttl &&

echo "Generating people..." &&

echo "...Updating db with prisoners" &&
s-put http://localhost:3030/warsa/data http://ldf.fi/warsa/prisoners data/new/prisoners.ttl &&

echo "...Constructing people" &&
echo 'query=' | cat - sparql/construct_people.sparql | sed 's/&/%26/g' | curl -d @- http://localhost:3030/warsa/sparql -v > data/new/prisoner_people.ttl &&

echo "...Constructing documents links" &&
echo 'query=' | cat - sparql/construct_documents_links.sparql | sed 's/&/%26/g' | curl -d @- http://localhost:3030/warsa/sparql -v > data/new/prisoner_documents_links.ttl &&

echo "...Updating db with new people" &&
cat data/new/prisoner_people.ttl data/new/prisoner_documents_links.ttl > prisoners_temp.ttl &&
s-put http://localhost:3030/warsa/data http://ldf.fi/warsa/prisoner_persons data/new/prisoner_people.ttl &&
rm prisoners_temp.ttl &&

for construct in births promotions ranks unit_joinings captures disappearances
do
    echo "...Constructing $construct" &&
    echo 'query=' | cat - "sparql/construct_$construct.sparql" | sed 's/&/%26/g' | curl -d @- http://localhost:3030/warsa/sparql -v > "data/new/prisoner_$construct.ttl"
done &&

echo "...Deleting temp graph" &&
s-delete http://localhost:3030/warsa/data http://ldf.fi/warsa/prisoner_persons &&

echo "...Finished"
