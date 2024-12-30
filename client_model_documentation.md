| Field Name | Type | Constraints | Default Value |
|------------|------|-------------|---------------|
| first_name_encr | VARCHAR | Not Null | None |
| last_name_encr | VARCHAR | Not Null | None |
| birthday_encr | VARCHAR | Not Null | None |
| street_encr | VARCHAR | Not Null | None |
| city_encr | VARCHAR | Not Null | None |
| parent_encr | VARCHAR | Not Null | None |
| telephone1_encr | VARCHAR | Not Null | None |
| telephone2_encr | VARCHAR | Not Null | None |
| email_encr | VARCHAR | Not Null | None |
| lrst_diagnosis_encr | VARCHAR | Not Null | None |
| notes_encr | VARCHAR | Not Null | None |
| client_id | INTEGER | Primary Key, Not Null | None |
| school | VARCHAR | Not Null | None |
| gender | CHAR(1) | Check: gender IN ('f', 'm') | None |
| entry_date | VARCHAR | None | None |
| class_name | VARCHAR | None | None |
| class_int | INTEGER | None | None |
| estimated_date_of_graduation | DATETIME | None | None |
| document_shredding_date | DATETIME | None | None |
| keyword_taetigkeitsbericht | VARCHAR | None | None |
| datetime_created | DATETIME | Not Null | None |
| datetime_lastmodified | DATETIME | Not Null | None |
| notenschutz | BOOLEAN | None | None |
| nachteilsausgleich | BOOLEAN | None | None |
| nta_sprachen | INTEGER | None | None |
| nta_mathephys | INTEGER | None | None |
| nta_notes | VARCHAR | None | None |
| n_sessions | FLOAT | None | None |
