client=$1
nta_sprachen=$2
diagnosis=$3

edupsy_admin -w DEBUG set_client \
    $client \
    "nachteilsausgleich=1" \
    "notenschutz=1" \
    "nta_mathephys=10" \
    "nta_sprachen=$nta_sprachen" \
    "lrst_diagnosis_encr=$diagnosis"
