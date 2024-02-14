csv_input=$1
client_id=$2

csv_output="s_$student.csv"
in2csv $csv_input | csvgrep -c client_id -r "^$client_id$" > $csv_output
