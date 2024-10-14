client=$1
nta_sprachen=$2

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client lukas.liebermann \
    $client \
    "nachteilsausgleich=1" \
    "notenschutz=0" \
    "nta_mathephys=10" \
    "nta_sprachen=$nta_sprachen"
