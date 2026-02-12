client=$1

edupsyadmin -w DEBUG set_client \
  $client \
  "nachteilsausgleich=0" \
  "notenschutz=0" \
  "nta_zeitv_wenigtext=0" \
  "nta_zeitv_vieltext=0"
