client_id=$1
test_date=$2
test_type="LGVT"
version=$3

edupsy_admin -w WARN -c ~/bin/edupsy_admin/etc/config.yml\
    mk_report lukas.liebermann $client_id\
    $test_date $test_type --version $version
