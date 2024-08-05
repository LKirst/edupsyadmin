client=$1
keyword=$2
n_sessions=$3

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client \
    lukas.liebermann $client keyword_taetigkeitsbericht --value $keyword

edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml set_client \
    lukas.liebermann $client n_sessions --value $n_sessions
