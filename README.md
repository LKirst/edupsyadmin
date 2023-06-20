# edupsy_admin

This is the edupsy_admin application. It is not functional yet.

The file structure of the project was created using a [cookiecutter
template](https://github.com/mdklatt/cookiecutter-python-app). I will try to
implement most of what the template suggests and delete what I do not need. But
this will take time.

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

- Create tests 

- Encrypt data

- Create a UI 
