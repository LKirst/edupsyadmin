client=$1

edupsyadmin -w DEBUG set_client \
    $client \
    "nachteilsausgleich=1" \
    "notenschutz=1" \
    "nta_mathephys=10" \
    "nta_sprachen=25" \
    "nta_font=1" \
    "lrst_diagnosis=lrst"
