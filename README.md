# edupsyadmin

edupsyadmin provides tools to help school psychologists with their
documentation

## Basic Setup

You can install the CLI using pip or
[uv](https://docs.astral.sh/uv/getting-started/installation).

Install with uv:

    $ uv tool install edupsyadmin

You may get a warning that the `bin` directory is not on your environment path.
If that is the case, copy the path from the warning and add it directory to
your **environment path** permanently or just for the current session.

Run the application:

    $ edupsyadmin --help

## Getting started

### Modify the config file

First, you have to update the config file with your data. To
find the config file, run:

`edupsyadmin info`

In the output, you will see your `config_path`. Open the file
using an editor that does not add formatting (for example
Notepad on Windows). Change all values to the data that you
want to appear in your documentation:

1. First replace YOUR.USER.NAME with your user name (no spaces and no special
   characters):

   `  app_username: YOUR.USER.NAME`

2. Then change your data under `schoolpsy`

  ```
    schoolpsy_name: "Write out your name here"
    schoolpsy_street: "Your street and house number"
    schoolpsy_town: "Postecode and town"
  ```

3. Under `school`, change the short name for your school to something more
   memorable than `FirstSchool`. Do not use spaces or special characters:

   `  MyMemorableSchoolName:`

4. Add the data for your school. The `end` variable will be used to estimate
   the date for the destruction of records (3 years after the estimated
   graduation date).

  ```
    school_head_w_school: "Title of your head of school"
    school_name: "Name of your school written out"
    school_street: "Street and house number of your school"
    school_town: "Postecode and town"
    end: 11
  ```

5. Reapeat step 3 and 4 for each school you work at.

6. Change the paths under filesets to point to the (sets of) files you want to
   use.

  ```
  form_set:
    name_of_my_form_set:
      - "path/to/my/first_file.pdf"
      - "path/to/my/second_file.pdf"
  ```

### Storing credentials

edupsyadmin uses `keyring` for the encryption credentials. `keyring` has
several backends.

- On Windows the default is the Windows Credential Manager (German:
  Anmeldeinformationsverwaltung).

- On macOS, the default is Keychain (German: Schlüsselbund)

For the keychain backend you want to use, add an entry using the username from
your config.yaml.

- Internet or network address: `liebermann-schulpsychologie.github.io`
- User name: `the_user_name_from_your_config_file`
- Password: `a_secure_password`

## The database

The information you enter, is stored in an SQLite database with the fields
described [in the documentation for
edupsyadmin](https://edupsyadmin.readthedocs.io/en/latest/clients_model.html#)

## Examples

Get information about the path to the config file and the path to the database:

    $ edupsyadmin info

Add a client interactively:

    $ edupsyadmin new_client

Add a client to the database from a Webuntis csv export:

    $ edupsyadmin new_client --csv ./path/to/your/file.csv --name "short_name_of_client"

Change values for the database entry with `client_id=42`:

```
$ edupsyadmin set_client 2 \
  "nta_font=1" \
  "nta_zeitverl_vieltext=20" \
  "nos_rs=0" \
  "lrst_diagnosis=iLst"
```

See an overview of all clients in the database:

    $ edupsyadmin get_clients

Fill a PDF form for the database entry with `client_id=42`:

    $ edupsyadmin create_documentation 42 ./path/to/your/file.pdf

Fill all files that belong to the form_set `lrst` (as defined in the
config.yml) with the data for `client_id=42`:

    $ edupsyadmin create_documentation 42 --form_set lrst

## Development

Create the development enviroment:

    $ uv v
    $ uv pip install -e .

Run the test suite:

    $ .venv/bin/python -m pytest -v -n auto --cov=src test/

Build documentation:

    $ .venv/bin/python -m sphinx -M html docs docs/_build

## License

This project is licensed under the terms of the MIT License. Portions of this
project are derived from the python application project cookiecutter template
by Michael Klatt, which is also licensed under the MIT license. See the
LICENSE.txt file for details.
