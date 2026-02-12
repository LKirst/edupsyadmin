client=$1

edupsyadmin -w DEBUG set_client \
  $client \
  "nachteilsausgleich=1" \
  "notenschutz=1" \
  "nta_zeitv_wenigtext=10" \
  "nta_zeitv_vieltext=25" \
  "nta_font=1" \
  "lrst_diagnosis_encr=lrst"
