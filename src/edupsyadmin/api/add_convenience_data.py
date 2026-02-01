from datetime import date
from importlib.resources import files
from typing import Any

from dateutil.parser import parse

from edupsyadmin.core.academic_year import (
    get_academic_year_string,
    get_estimated_end_of_academic_year,
    get_this_academic_year_string,
)
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger


def _get_subjects(school: str) -> str:
    """Get a list of subjects for the given school.

    :param school: The name of the school.
    :return: A string containing the subjects separated by newlines.
    """
    file_path = files("edupsyadmin.data").joinpath(f"Faecher_{school}.md")
    logger.debug(f"trying to read school subjects file: {file_path}")
    if file_path.is_file():
        logger.debug("subjects file exists")
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    else:
        logger.debug("school subjects file does not exist")
        return ""


def _get_addr_mulitline(street: str, city: str, name: str | None = None) -> str:
    """Get a multiline address for the given street and city.

    :param street: The street name.
    :param city: The city name.
    :param name: The name of the person or organization. Defaults to None.
    :return: A multiline string containing the address.
    """
    if name is None:
        return street + "\n" + city
    return name + "\n" + street + "\n" + city


def _date_to_german_string(isodate: date | str | None) -> str:
    if isinstance(isodate, date):
        return isodate.strftime("%d.%m.%Y")
    if (isodate is None) or (isodate == ""):
        return ""
    try:
        return parse(isodate, dayfirst=False).strftime("%d.%m.%Y")
    except ValueError:
        logger.error(f"'{isodate}' could not be parsed as a date")
        raise
    except TypeError:
        logger.error(f"'{isodate}' is neither None, datetime.date, nor str")
        raise


def _add_client_address(data: dict[str, Any]) -> None:
    """Add client's name and address to data."""
    first_name = data.get("first_name_encr", "")
    last_name = data.get("last_name_encr", "")
    data["name"] = f"{first_name} {last_name}"
    try:
        data["addr_s_nname"] = _get_addr_mulitline(
            data["street_encr"], data["city_encr"]
        ).replace("\n", ", ")
        data["addr_m_wname"] = _get_addr_mulitline(
            data["street_encr"], data["city_encr"], data["name"]
        )
    except (TypeError, KeyError) as e:
        logger.debug(f"Couldn't add home address because of missing data: {e}")


def _add_school_psychologist_address(data: dict[str, Any]) -> None:
    """Add school psychologist's address from config to data."""
    data["schoolpsy_name"] = config.schoolpsy.schoolpsy_name
    data["schoolpsy_street"] = config.schoolpsy.schoolpsy_street
    data["schoolpsy_city"] = config.schoolpsy.schoolpsy_city
    data["schoolpsy_addr_m_wname"] = _get_addr_mulitline(
        data["schoolpsy_street"], data["schoolpsy_city"], data["schoolpsy_name"]
    )
    data["schoolpsy_addr_s_wname"] = data["schoolpsy_addr_m_wname"].replace("\n", ", ")


def _add_school_address(data: dict[str, Any]) -> None:
    """Add school address from config to data."""
    school_key = data.get("school")
    if not school_key:
        logger.debug("No school specified for client.")
        return
    schoolconfig = config.school[school_key]
    data["school_name"] = schoolconfig.school_name
    data["school_street"] = schoolconfig.school_street
    data["school_city"] = schoolconfig.school_city
    data["school_head_w_school"] = schoolconfig.school_head_w_school
    data["school_addr_m_wname"] = _get_addr_mulitline(
        data["school_street"], data["school_city"], data["school_name"]
    )
    data["school_addr_s_wname"] = data["school_addr_m_wname"].replace("\n", ", ")


def _add_lrst_diagnosis(data: dict[str, Any]) -> None:
    """Add long version of LRSt diagnosis to data."""
    diagnosis = data.get("lrst_diagnosis_encr")
    if not diagnosis:
        return

    diagnosis_mapping = {
        "lrst": "Lese-Rechtschreib-Störung",
        "iLst": "isolierte Lesestörung",
        "iRst": "isolierte Rechtschreibstörung",
    }
    if diagnosis in diagnosis_mapping:
        data["lrst_diagnosis_long"] = diagnosis_mapping[diagnosis]
    else:
        allowed = list(diagnosis_mapping.keys())
        raise ValueError(
            f"lrst_diagnosis can be only one of {allowed}, but was {diagnosis}"
        )


def _add_dates(data: dict[str, Any]) -> None:
    """Add various formatted dates to data."""
    data["today_date"] = date.today()
    dates_to_convert = [
        "birthday_encr",
        "today_date",
        "lrst_last_test_date_encr",
        "document_shredding_date",
    ]
    for idate in dates_to_convert:
        gdate = idate + "_de"
        data[gdate] = _date_to_german_string(data.get(idate))

    data["school_year"] = get_this_academic_year_string()


def _add_nta_schoolyear(data: dict[str, Any]) -> None:
    """Add NTA/NOS end schoolyear to data."""
    if (
        data.get("nta_nos_end")
        and data.get("class_int")
        and data.get("nta_nos_end_grade")
    ):
        data["nta_nos_end_schoolyear"] = get_academic_year_string(
            get_estimated_end_of_academic_year(
                grade_current=data["class_int"], grade_target=data["nta_nos_end_grade"]
            )
        )


def _convert_lrst_test_by(data: dict[str, Any]) -> None:
    """Convert lrst_last_test_by_encr to numerical value for forms."""
    test_by = data.get("lrst_last_test_by_encr")
    if not test_by:
        return

    test_by_mapping = {
        "schpsy": 1,
        "psychia": 2,
        "psychoth": 3,
        "spz": 4,
        "andere": 5,
    }

    if test_by in test_by_mapping:
        data["lrst_schpsy"] = test_by_mapping[test_by]
    else:
        logger.error(
            f"Value for lrst_last_test_by must be in "
            f"{list(test_by_mapping.keys())} but is "
            f"{test_by}"
        )


def add_convenience_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Füge Daten hinzu, die sich aus einem Eintrag in einer `Client`-Datenbank,
    der Konfigurationsdatei und einer Datei zu den Schulfächern (optional)
    ableiten.

    Der Konfigurationsdatei werden folgende Werte entnommen:
        "school_name",
        "school_street",
        "school_city",
        "school_head_w_school",
        "schoolpy_name",
        "schoolpy_street",
        "schoolpy_city",

    Wenn eine Datei zu den Fächern angelegt ist, wird dieser entnommen:
        "school_subjects"

    :param data: ein Dictionary, mit den Werten eines Eintrags in einer
        `Client`-Datenbank

    :return: das ursprüngliche dict mit den Feldern aus der Konfigurationsdatei
        und folgenden neuen Feldern:

        - **name**: Vor- und Nachname,
        - **addr_s_nname**: Adresse in einer Zeile ohne Name,
        - **addr_m_wname**: Adresse mit Zeilenumbrüchen mit Name,
        - **schoolpsy_addr_s_wname**: Adresse des Nutzers in einer Ziele mit Name,
        - **schoolpsy_addr_m_wname** Adresse des Nutzers mit Zeilenumbrüchen
          mit Name,
        - **school_addr_s_wname**: Adresse der Schule,
        - **school_addr_m_wname**: Adresse der Schule mit Zeilenumbrüchen,
        - **lrst_diagnosis_long**: Ausgeschriebene LRSt-Diagnose,
        - **lrst_last_test_de**: Datum des letzten Tests, im Format DD.MM.YYYY,
        - **today_date_de**: Heutiges Datum, im Format DD.MM.YYYY,
        - **birthday_encr_de**: Geburtsdatum des Schülers im Format DD.MM.YYYY,
        - **document_shredding_date_de**: Datum für Aktenvernichtung im Format
          DD.MM.YYYY,
        - **nta_nos_end_schoolyear**: Schuljahr bis zu dem NTA und Notenschutz
          begrenzt sind
    """
    _add_client_address(data)
    _add_school_psychologist_address(data)
    _add_school_address(data)
    _add_lrst_diagnosis(data)

    school_key = data.get("school")
    if school_key:
        data["school_subjects"] = _get_subjects(school_key)

    _add_dates(data)
    _add_nta_schoolyear(data)
    _convert_lrst_test_by(data)

    return data
