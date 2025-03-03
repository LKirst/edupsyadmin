## 3.1.0 (2025-03-03)

### Feat

- **clients.py**: add types of nta as new columns to database

### Refactor

- **managers.py**: show lrst_diagnosis in the overview
- expose core and init for imports of edupsyadmin
- remove obsolete shellscripts

## 3.0.0 (2025-02-24)

### BREAKING CHANGE

- the lrst_diagnosis variable is no longer encrypted and the taetigkeitsbericht keyword is now encrypted in the database

### Fix

- **lgvt.py**: change config_path to salt_path

### Refactor

- read taetigkeitsbericht keys from a csv file instead of ods
- encrypt gender and leave lrst_diagnosis unencrypted
- **clients.py**: change todo comment for lrst_diagnosis

## 2.0.1 (2025-02-17)

### Fix

- **cli.py**: use args.config_path[0] to copy the sample config if missing

## 2.0.0 (2025-02-11)

### BREAKING CHANGE

- the salt value will no longer be read from the config.yml file

### Feat

- **encrypt.py**: use a separate salt file instead of the config.yml
- add get_clients to the cli and managers.py

### Fix

- **cli.py**: change the default for --config to a list
- **encrypt.py**: add a missing f before a logging fstring
- use salt_path consistently

### Refactor

- **managers.py**: remove superfluous warning
- move the convert_config_to_dict function removed in the last commit to config.py

## 2.0.0b1 (2025-01-07)

## 2.0.0b0 (2025-01-06)

### Feat

- **add_convenience_data.py**: add schoolpsy_address_multiline to convenience data

### Fix

- handle the fact that config_path is a list not a string
- **sampleconfig.yml**: change the field name for uid from uid to app_uid

### Refactor

- **clients.py**: add nta arguments to the constructor for clients
- **test_encrypt.py**: use the mock_config fixture from conftest.py

## 1.0.0b0 (2025-01-04)

### BREAKING CHANGE

- new_client --csv now requires a --name argument

### Feat

- handle the extraction of a student from a webuntis csv with several rows

### Fix

- **encrypt.py**: don't load the config file in encrypt.py
- **cli.py**: handle config files correctly
- **cli.py**: catch KeyError exception when no app_username is set

### Refactor

- remove redundant scripts
- **fill_form.py**: raise FileNotFoundError
- refactor tests
- mock keyring for testing
- use importlib.resources.files instead of deprecated path
- **pyproject.toml**: change name of dependency group to bwbackend

## 1.0.0 (2025-01-06)

### Fix

- handle the fact that config_path is a list not a string

## 1.0.0b1 (2025-01-06)

### Feat

- **add_convenience_data.py**: add schoolpsy_address_multiline to convenience data

### Fix

- **sampleconfig.yml**: change the field name for uid from uid to app_uid

### Refactor

- **clients.py**: add nta arguments to the constructor for clients
- **test_encrypt.py**: use the mock_config fixture from conftest.py

## 1.0.0b0 (2025-01-04)

### BREAKING CHANGE

- new_client --csv now requires a --name argument

### Feat

- handle the extraction of a student from a webuntis csv with several rows

### Fix

- **encrypt.py**: don't load the config file in encrypt.py
- **cli.py**: handle config files correctly
- **cli.py**: catch KeyError exception when no app_username is set

### Refactor

- remove redundant scripts
- **fill_form.py**: raise FileNotFoundError
- refactor tests
- mock keyring for testing
- use importlib.resources.files instead of deprecated path
- **pyproject.toml**: change name of dependency group to bwbackend

## 1.0.0a2 (2024-12-19)

### Fix

- do input validation for school
- **managers.py**: normalize form paths
- use form_paths variable name consistently
- **cli.py**: make form_paths optional in create documentation
- **taetigkeitsbericht_from_db.py**: set pdflibs_imported when the libraries can be imported
- **add_convenience_data.py**: correct wrong dict key

## 1.0.0a1 (2024-12-16)

### Fix

- **teatigkeitsbericht_from_db.py**: make dataframe_image and fpdf truly optional
- change version in __version__.py back to string

### Refactor

- remove superfluous version from pyproject.toml

## 1.0.0a0 (2024-12-15)

### BREAKING CHANGE

- You will need to add schoolpsy data to your config.yml. See
the sampleconfig.yml in ./data/
- This will break imports and shellscripts that call edupsy_admin instead of edupsyadmin. This also changes the config path and the data path.

### Feat

- **add_convenience_data.py**: set nta_font to True if lrst_diagnosis is lrst or iLst
- accept sets of form files from config and add schoolpsy convenience data
- **cli.py**: copy sample config if config.yml does not exist
- add a flatten_pdfs function

### Fix

- **core**: explicitly set the encoding for config files to UTF-8
- change default and type hint for encrypted variables

### Refactor

- **.gitignore**: ignore .pypirc
- move code for creation of sample pdf to separate file
- update readme with new project name
- change the project name
- move the test.sqlite db to tmp_path
