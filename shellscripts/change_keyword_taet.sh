client=$1
keyword=$2

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client \
    lukas.liebermann $client keyword_taetigkeitsbericht --value $keyword
