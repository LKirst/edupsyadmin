# edupsy_admin

edupsy_admin provides tools to help school psychologists with their
documentation.

## Minimum Requirements

- Python 3.11+

## License

This project is licensed under the terms of the MIT License. Portions of this
project are derived from the python application project cookiecutter template
by Michael Klatt, which is also licensed under the MIT license. See the
LICENSE.txt file for details.

## Optional Requirements

- `pytest`\_ (for running the test suite)
- `Sphinx`\_ (for generating documentation)

## Basic Setup

Install for the current user:

    $ pip install . --user

Run the application:

    $ edupsy_admin --help

Run the test suite:

    $ pytest test/

Build documentation:

    $ sphinx-build -b html doc doc/_build/html
