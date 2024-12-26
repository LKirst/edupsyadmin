# edupsyadmin

edupsyadmin provides tools to help school psychologists with their
documentation

## Basic Setup

You can install the CLI using pip or
[uv](https://docs.astral.sh/uv/getting-started/installation).

Install with uv:

    $ uv tool install edupsyadmin

If you use uv, add the bin directory to your **environment path** permanently or just for the current session.
To get the bin directory, run 

    $ echo $UV_TOOL_BIN_DIR

To add the bin directory to the path for your current session, run

    $ uv tool update-shell

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
    end: 11
  ```

5. Reapeat step 3 and 4 for each school you work at.

6. Change the paths under filesets to point to the (sets of) files you want to
   use.

  ```
  fileset:
    name_of_my_fileset:
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

## Examples

Get information about the path to the config file and the path to the database:

    $ edupsyadmin info

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

    $ .venv/bin/python -m pytest -v -n auto --cov=src test/

Build documentation:

    $ .venv/bin/python -m sphinx -M html doc doc/_build

## License

This project is licensed under the terms of the MIT License. Portions of this
project are derived from the python application project cookiecutter template
by Michael Klatt, which is also licensed under the MIT license. See the
LICENSE.txt file for details.
