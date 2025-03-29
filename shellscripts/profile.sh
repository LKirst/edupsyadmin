outfile="profiling/$(date +'%Y-%m-%d_%H-%M-%S')_profile_output.prof"
python -m cProfile -o $outfile src/edupsyadmin/cli.py info
snakeviz $outfile
