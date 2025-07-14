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
    logger.info(f"trying to read school subjects file: {file_path}")
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


def _date_to_german_string(isodate: date | str) -> str:
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
        `Client` Datenbank

    :return: das ursprüngliche dict mit den Feldern aus der Konfigurationsdatei
        und folgenden neuen Feldern:

        - **name**: Vor- und Nachname,
        - **addr_s_nname**: Adresse in einer Zeile ohne Name,
        - **addr_m_wname**: Adresse mit Zeilenumbrüchen mit Name,
        - **schoolpsy_addr_s_wname**: Adresse des Nutzers in einer Ziele mit
          Name,
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
    # client address
    data["name"] = data["first_name_encr"] + " " + data["last_name_encr"]
    try:
        data["addr_s_nname"] = _get_addr_mulitline(
            data["street_encr"], data["city_encr"]
        ).replace("\n", ", ")
        data["addr_m_wname"] = _get_addr_mulitline(
            data["street_encr"], data["city_encr"], data["name"]
        )
    except TypeError:
        logger.debug("Couldn't add home address because of missing data: {e}")

    # school psychologist address
    for i in ["schoolpsy_name", "schoolpsy_street", "schoolpsy_city"]:
        data[i] = config.schoolpsy[i]
    data["schoolpsy_addr_m_wname"] = _get_addr_mulitline(
        data["schoolpsy_street"], data["schoolpsy_city"], data["schoolpsy_name"]
    )
    data["schoolpsy_addr_s_wname"] = data["schoolpsy_addr_m_wname"].replace("\n", ", ")

    # school address
    schoolconfig = config.school[data["school"]]
    for i in ["school_name", "school_street", "school_city", "school_head_w_school"]:
        data[i] = schoolconfig[i]
    data["school_addr_m_wname"] = _get_addr_mulitline(
        data["school_street"], data["school_city"], data["school_name"]
    )
    data["school_addr_s_wname"] = data["school_addr_m_wname"].replace("\n", ", ")

    # lrst_diagnosis
    diagnosis = data["lrst_diagnosis"]
    if diagnosis == "lrst":
        data["lrst_diagnosis_long"] = "Lese-Rechtschreib-Störung"
    elif diagnosis == "iLst":
        data["lrst_diagnosis_long"] = "isolierte Lesestörung"
    elif diagnosis == "iRst":
        data["lrst_diagnosis_long"] = "isolierte Rechtschreibstörung"
    elif diagnosis is not None:
        raise ValueError(
            f"lrst_diagnosis can be only lrst, iLst or iRst, but was {diagnosis}"
        )

    # subjects
    data["school_subjects"] = _get_subjects(data["school"])

    # dates: for forms, I use the format dd.mm.YYYY; internally,
    # I use date objects or strings in the format "YYYY-mm-dd"
    data["today_date"] = date.today()
    dates = [
        "birthday_encr",
        "today_date",
        "lrst_last_test_date",
        "document_shredding_date",
    ]
    for idate in dates:
        gdate = idate + "_de"
        data[gdate] = _date_to_german_string(data[idate])

    data["school_year"] = get_this_academic_year_string()
    if data["nta_nos_end"]:
        data["nta_nos_end_schoolyear"] = get_academic_year_string(
            get_estimated_end_of_academic_year(
                grade_current=data["class_int"], grade_target=data["nta_nos_end_grade"]
            )
        )

    return data
