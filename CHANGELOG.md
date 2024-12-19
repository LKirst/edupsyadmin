## 1.0.0 (2024-12-19)

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
