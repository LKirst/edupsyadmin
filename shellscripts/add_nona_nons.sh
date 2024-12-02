client=$1

edupsyadmin -w DEBUG set_client \
    $client \
    "nachteilsausgleich=0" \
    "notenschutz=0" \
    "nta_mathephys=0" \
    "nta_sprachen=0"
