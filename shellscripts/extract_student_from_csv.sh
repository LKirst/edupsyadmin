csv_input=$1
student=$2

csv_output="s_$student.csv"
in2csv $csv_input -t -I | csvgrep -c name -m $student > $csv_output
