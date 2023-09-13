# edupsy_admin

edupsy_admin provides tools to help school psychologists with their
documentation.

## Minimum Requirements

- Python 3.5+

## Optional Requirements

- `pytest`\_ (for running the test suite)
- `Sphinx`\_ (for generating documentation)

## Basic Setup

Install for the current user (NOT POSSIBLE YET):

    $ python -m pip install . --user

NOTE TO SELF: I have installed the package using the following command at the
top level of my package

    $ pip install -e .

    Then, I can run it with:

    $ edupsy_admin -w INFO -c "/c/literatur/code/edupsy_admin/etc/config.yml" hello

Run the application:

    $ python -m edupsy_admin --help

Run the test suite:

    $ pytest test/

Build documentation:

    $ sphinx-build -b html doc doc/_build/html

## TODO

- Create a function for an LRSt report

- Create a function for a waiting list

- Create a UI

- Rename the package to schoolpsych - one word, no underscores
