client_id=$1

edupsy_admin -w WARN -c ~/bin/edupsy_admin/etc/config.yml\
    create_documentation lukas.liebermann $client_id\
    ~/Templates/Beratung/Inklusion/Inklusion_Anschreiben_Regierung_bfsmn.md\
    ~/Templates/Beratung/Inklusion/Inklusion_SchulpsychologischeStellungnahme_bfsmn.md\
    ~/Templates/Beratung/Inklusion/Inklusion_Antrag_bfsmn.pdf\
    ~/Templates/Beratung/Inklusion/Inklusion_Schulleitung_bfsmn.pdf\
