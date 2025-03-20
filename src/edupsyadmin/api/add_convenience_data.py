from datetime import date
from importlib.resources import files

from dateutil.parser import parse

from edupsyadmin.api.academic_year import get_this_academic_year_string
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger


def get_subjects(school: str) -> str:
    file_path = files("edupsyadmin.data").joinpath(f"Faecher_{school}.md")
    logger.info(f"trying to read school subjects file: {file_path}")
    if file_path.is_file():
        logger.debug("subjects file exists")
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    else:
        logger.debug("school subjects file does not exist")
        return ""


def add_convenience_data(data: dict) -> dict:
    """Add the information which can be generated from existing key value pairs.

    Parameters
    ----------
    data : dict
        A dictionary of data values. Must contain "last_name", "first_name",
        "street", "city".
    """
    # client address
    data["name"] = data["first_name"] + " " + data["last_name"]
    try:
        data["address"] = data["street"] + ", " + data["city"]
        data["address_multiline"] = (
            data["name"] + "\n" + data["street"] + "\n" + data["city"]
        )
    except TypeError:
        logger.debug("Couldn't add home address because of missing data: {e}")

    # school psychologist address
    for i in ["schoolpsy_name", "schoolpsy_street", "schoolpsy_town"]:
        data[i] = config.schoolpsy[i]
    data["schoolpsy_address_multiline"] = (
        data["schoolpsy_name"]
        + "\n"
        + data["schoolpsy_street"]
        + "\n"
        + data["schoolpsy_town"]
    )
    data["schoolpsy_address_singleline"] = data["schoolpsy_address_multiline"].replace(
        "\n", ", "
    )

    # school address
    schoolconfig = config.school[data["school"]]
    for i in ["school_name", "school_street", "school_head_w_school"]:
        data[i] = schoolconfig[i]

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

    # Notenschutz and Nachteilsausgleich
    if data["nachteilsausgleich"] or data["notenschutz"]:
        school_subjects = get_subjects(data["school"])
        logger.debug(f"\nsubjects:\n{school_subjects}")
    if data["notenschutz"]:
        data["ns_subjects"] = school_subjects
        data["ns_measures"] = "Verzicht auf die Bewertung der Rechtschreibleistung"
    if data["nachteilsausgleich"]:
        data["na_subjects"] = school_subjects
        data["na_measures"] = (
            f"Verlängerung der regulären Arbeitszeit um {data['nta_sprachen']}% "
            "bei schriftlichen Leistungsnachweisen und der "
            "Vorbereitungszeit bei mündlichen Leistungsnachweisen"
        )

    # dates
    # for forms, I use the format dd.mm.YYYY; internally, I use YYYY-mm-dd
    today = date.today()
    data["date_today_de"] = today.strftime("%d.%m.%Y")
    try:
        data["birthday_de"] = parse(data["birthday"], dayfirst=False).strftime(
            "%d.%m.%Y"
        )
    except ValueError:
        logger.error("The birthday could not be parsed: {e}")
        data["birthday_de"] = ""
    data["school_year"] = get_this_academic_year_string()
    data["document_shredding_date_de"] = data["document_shredding_date"].strftime(
        "%d.%m.%Y"
    )

    return data
