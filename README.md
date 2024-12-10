# edupsyadmin

edupsyadmin provides tools to help school psychologists with their
documentation.

## Basic Setup

Install with uv:

    $ uv tool install edupsyadmin

Run the application:

    $ edupsyadmin --help

## Examples

Add a client interactively:

    $ edupsyadmin new_client

Add a client to the database from a Webuntis csv export:

    $ edupsyadmin new_client --csv ./path/to/your/file.csv

Change values for the database entry with `client_id=42`:

```
edupsyadmin set_client 42 \
  "nachteilsausgleich=1" \
  "notenschutz=0" \
  "lrst_diagnosis_encr=iLst"
```

Fill a PDF form for the database entry with `client_id=42`:

    $ edupsyadmin create_documentation 42 ./path/to/your/file.pdf

## Development

Create the development enviroment:

    $ uv v
    $ uv pip install -e .

Run the test suite:

    $ .venv/bin/python -m pytest -v test/

Build documentation:

    $ .venv/bin/python -m sphinx -M html doc doc/_build

## License

This project is licensed under the terms of the MIT License. Portions of this
project are derived from the python application project cookiecutter template
by Michael Klatt, which is also licensed under the MIT license. See the
LICENSE.txt file for details.
