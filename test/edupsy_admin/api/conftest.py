import pytest

from edupsy_admin.core.config import config

conf_content = """
core:
  logging: WARN
  uid: liebermann-schulpsychologie.github.io
school:
  test_school:
    school_name: Test School
    school_street: 123 Test St
    school_head_w_school: Principal of Test School
    end: 12
"""

# ruff: noqa: E501
webuntis_content = """
name,longName,foreName,gender,birthDate,klasse.name,entryDate,exitDate,text,id,externKey,medicalReportDuty,schulpflicht,majority,address.email,address.mobile,address.phone,address.city,address.postCode,address.street,attribute.Notenschutz,attribute.Nachteilsausgleich
MustermMax1,Mustermann,Max,m,01.01.2000,11TKKG,12.09.2023,,,12345,4321,False,False,False,max.mustermann@example.de,491713920000,02214710000,München,80331,Beispiel Str. 55B,,
"""


@pytest.fixture
def mock_config(tmp_path):
    conf_path = tmp_path / "conf.yml"
    conf_path.write_text(conf_content.strip())
    print(f"conf_path: {conf_path}")
    config.load(str(conf_path))
    yield conf_path


@pytest.fixture
def mock_webuntis(tmp_path):
    webuntis_path = tmp_path / "webuntis.csv"
    webuntis_path.write_text(webuntis_content.strip())
    print(f"webuntis_path: {webuntis_path}")
    yield webuntis_path
