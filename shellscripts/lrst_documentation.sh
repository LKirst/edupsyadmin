diagnosis=1
while getopts "n" flag; do
case "$flag" in
    n) diagnosis=0;;
esac
done

client_id=${@:$OPTIND:1}

if [ $diagnosis -eq 1 ]
then
edupsyadmin -w WARN \
    create_documentation $client_id\
    ~/Templates/Beratung/LRSt_GenehmigungSchulleitung_fosbos.pdf\
    ~/Templates/Beratung/LRSt_Stellungnahme_fosbos.pdf\
    ~/Templates/Beratung/LRSt_Informationsschreiben.pdf\
    ~/Templates/Beratung/LRSt_Anschreiben.pdf
else
edupsyadmin -w WARN \
    create_documentation $client_id\
    ~/Templates/Beratung/LRSt_StellungnahmeKeinBefund.pdf\
    ~/Templates/Beratung/LRSt_AnschreibenKeinBefund.pdf
fi
