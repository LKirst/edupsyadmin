#!/bin/bash

# Define the directory path for profiling
profiling_directory="profiling"
if [ ! -d "$profiling_directory" ]; then
  # If the directory is missing, create it
  mkdir -p "$profiling_directory"
  echo "Directory created: $profiling_directory"
fi

# Define the output file path with a timestamp
outfile="$profiling_directory/$(date +'%Y-%m-%d_%H-%M-%S')_profile_output.prof"
echo "Output file: $outfile"

# Run the Python script with cProfile and save the output to the file
python -m cProfile -o "$outfile" src/edupsyadmin/cli.py info

# Visualize the profiling output using snakeviz
snakeviz "$outfile"
