# edupsy_admin

edupsy_admin provides tools to help school psychologists with their
documentation.

## Minimum Requirements

- Python 3.10+

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
