client_id=$1
test_date=$2
test_type="LGVT"
version=$3

edupsy_admin -w WARN mk_report $client_id\
    $test_date $test_type --version $version
