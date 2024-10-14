client=$1

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client lukas.liebermann \
    $client \
    "nachteilsausgleich=0" \
    "notenschutz=0" \
    "nta_mathephys=0" \
    "nta_sprachen=0"
