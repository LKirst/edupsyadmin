import argparse
import csv
from datetime import date
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import update

from edupsyadmin.api import managers
from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.cli import main
from edupsyadmin.cli.commands import check_shredding
from edupsyadmin.cli.commands.check_shredding import _parse_iso_date
from edupsyadmin.core.encrypt import encr
from edupsyadmin.db.clients import Client


@pytest.fixture(autouse=True)
def setup_encryption_globally():
    if not encr.is_initialized:
        dummy_key = Fernet.generate_key()
        encr.set_keys([dummy_key])
    yield


def test_parse_iso_date():
    assert _parse_iso_date("2025-07-31") == date(2025, 7, 31)
    with pytest.raises(ValueError, match="Invalid date format"):
        _parse_iso_date("31.07.2025")


def test_check_shredding_help():
    with pytest.raises(SystemExit) as ex:
        main(["check-shredding", "--help"])
    assert ex.value.code == 0


@pytest.fixture
def shredding_db(tmp_path: Path, mock_config: Path) -> tuple[str, int, int, int]:
    db_path = tmp_path / "shred_test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    cm = managers.ClientsManager(db_url)

    # 1. Past shredding date (due)
    id1 = cm.add_client(
        school="FirstSchool",
        gender_encr="m",
        first_name_encr="Due",
        last_name_encr="User",
        birthday_encr=date(2005, 1, 1),
        class_name_encr="10A",
        record_academic_year="2019/20",
    )
    with cm.Session() as session, session.begin():
        session.execute(
            update(Client)
            .where(Client.client_id == id1)
            .values(document_shredding_date_encr=date(2020, 7, 31))
        )

    # 2. Future shredding date (not due)
    id2 = cm.add_client(
        school="FirstSchool",
        gender_encr="f",
        first_name_encr="Future",
        last_name_encr="User",
        birthday_encr=date(2010, 1, 1),
        class_name_encr="10B",
        record_academic_year="2025/26",
    )
    with cm.Session() as session, session.begin():
        session.execute(
            update(Client)
            .where(Client.client_id == id2)
            .values(document_shredding_date_encr=date(2099, 7, 31))
        )

    # 3. Unset shredding date (class has no integer)
    id3 = cm.add_client(
        school="OtherSchool",
        gender_encr="m",
        first_name_encr="Unset",
        last_name_encr="User",
        birthday_encr=date(2015, 1, 1),
        class_name_encr="Vorklasse",
        record_academic_year="2025/26",
    )

    return db_url, id1, id2, id3


def test_check_shredding_table(capsys, shredding_db):
    db_url, id1, _id2, _id3 = shredding_db

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=False,
        as_of_date=date(2025, 1, 1),
        show_unset=False,
        schools=None,
        out=None,
    )
    check_shredding.execute(args)

    out, _ = capsys.readouterr()
    assert "Clients Due for Document Shredding" in out
    assert str(id1) in out
    assert "2020-07-31" in out
    assert "2099-07-31" not in out
    assert "Notice: 1 client(s) have no document shredding date set" in out


def test_check_shredding_ids_only(capsys, shredding_db):
    db_url, id1, id2, _ = shredding_db

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=True,
        as_of_date=date(2025, 1, 1),
        show_unset=False,
        schools=None,
        out=None,
    )
    check_shredding.execute(args)

    out, _ = capsys.readouterr()
    # Strictly only the ID and newline, no table formatting or notices
    assert out.strip() == str(id1)
    assert str(id2) not in out


def test_check_shredding_show_unset(capsys, shredding_db):
    db_url, id1, _, id3 = shredding_db

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=False,
        as_of_date=date(2025, 1, 1),
        show_unset=True,
        schools=None,
        out=None,
    )
    check_shredding.execute(args)

    out, _ = capsys.readouterr()
    assert "Clients Due for Document Shredding" in out
    assert str(id1) in out
    assert "Clients Without Document Shredding Date" in out
    assert str(id3) in out
    assert "Vorklasse" in out


def test_check_shredding_as_of_future(capsys, shredding_db):
    db_url, id1, id2, _ = shredding_db

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=True,
        as_of_date=date(2100, 1, 1),
        show_unset=False,
        schools=None,
        out=None,
    )
    check_shredding.execute(args)

    out, _ = capsys.readouterr()
    ids = [int(line) for line in out.strip().splitlines()]
    assert id1 in ids
    assert id2 in ids


def test_check_shredding_out_csv(tmp_path: Path, capsys, shredding_db):
    db_url, id1, _, id3 = shredding_db
    csv_file = tmp_path / "shred_output.csv"

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=False,
        as_of_date=date(2025, 1, 1),
        show_unset=True,
        schools=None,
        out=csv_file,
    )
    check_shredding.execute(args)

    assert csv_file.is_file()
    with csv_file.open("r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        expected_rows = 2
        assert len(reader) == expected_rows
        due_row = next(r for r in reader if r["client_id"] == str(id1))
        unset_row = next(r for r in reader if r["client_id"] == str(id3))

        assert due_row["status"] == "due"
        assert due_row["document_shredding_date"] == "2020-07-31"

        assert unset_row["status"] == "unset"
        assert unset_row["document_shredding_date"] == ""


def test_check_shredding_out_csv_empty(tmp_path: Path, shredding_db):
    db_url, _, _, _ = shredding_db
    csv_file = tmp_path / "empty_shred_output.csv"

    args = argparse.Namespace(
        database_url=db_url,
        ids_only=False,
        as_of_date=date(2000, 1, 1),
        show_unset=False,
        schools=["NonExistentSchool"],
        out=csv_file,
    )
    check_shredding.execute(args)

    assert csv_file.is_file()
    with csv_file.open("r", encoding="utf-8") as f:
        dict_reader = csv.DictReader(f)
        reader = list(dict_reader)
        assert len(reader) == 0
        assert dict_reader.fieldnames == [
            "client_id",
            "record_academic_year",
            "school",
            "status",
            "document_shredding_date",
        ]
