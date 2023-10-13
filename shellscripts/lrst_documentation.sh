diagnosis=1
while getopts "n" flag; do
case "$flag" in
    n) diagnosis=0;;
esac
done

client_id=${@:$OPTIND:1}

if [ $diagnosis -eq 1 ]
then
edupsy_admin -w WARN -c ~/bin/edupsy_admin/etc/config.yml\
    create_documentation lukas.liebermann $client_id\
    ~/Templates/Beratung/LRSt_GenehmigungSchulleitung_2023_fosbos.pdf\
    ~/Templates/Beratung/LRSt_Stellungnahme_2023_fosbos.pdf\
    ~/Templates/Beratung/LRSt_Informationsschreiben_2023.pdf\
    ~/Templates/Beratung/LRSt_Anschreiben_2023.pdf
else
edupsy_admin -w WARN -c ~/bin/edupsy_admin/etc/config.yml\
    create_documentation lukas.liebermann $client_id\
    ~/Templates/Beratung/LRSt_StellungnahmeKeinBefund_2023.pdf\
    ~/Templates/Beratung/LRSt_AnschreibenKeinBefund_2023.pdf
fi

