client=$1

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client lukas.liebermann $client nachteilsausgleich --value 1
edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client lukas.liebermann $client notenschutz --value 1
