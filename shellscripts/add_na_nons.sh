client=$1
nta_sprachen=$2

edupsy_admin -w DEBUG set_client \
    $client \
    "nachteilsausgleich=1" \
    "notenschutz=0" \
    "nta_mathephys=10" \
    "nta_sprachen=$nta_sprachen"
