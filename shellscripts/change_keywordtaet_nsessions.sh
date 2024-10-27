client=$1
keyword=$2
n_sessions=$3

edupsy_admin -w DEBUG set_client \
    $client keyword_taetigkeitsbericht --value $keyword

edupsy_admin -w DEBUG set_client \
    $client n_sessions --value $n_sessions
