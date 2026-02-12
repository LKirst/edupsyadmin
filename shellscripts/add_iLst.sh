client=$1

edupsyadmin -w DEBUG set_client \
  $client \
  "nachteilsausgleich=1" \
  "notenschutz=0" \
  "nta_zeitv_wenigtext=10" \
  "nta_zeitv_vieltext=20" \
  "nta_font=1" \
  "lrst_diagnosis_encr=iLst"
