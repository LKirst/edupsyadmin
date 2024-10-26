from datetime import date
from dateutil.parser import parse
from importlib.resources import files

from .academic_year import get_this_academic_year_string
from ..core.logger import logger
from ..core.config import config


def get_subjects(school: str):
    file_path = files("edupsy_admin.data").joinpath(f"Faecher_{school}.md")
    logger.info(f"trying to read school subjects file: {file_path}")
    if file_path.exists() and file_path.is_file():
        logger.debug(f"subjects file exists")
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    else:
        logger.warning(f"school subjects file does not exist!")
        return ""


def add_convenience_data(data: dict) -> dict:
    """Add the information which can be generated from existing key value pairs.

    Parameters
    ----------
    data : dict
        A dictionary of data values. Must contain "last_name", "first_name",
        "street", "city".
    """
    data["name"] = data["first_name"] + " " + data["last_name"]

    try:
        data["address"] = data["street"] + ", " + data["city"]
        data["address_multiline"] = (
            data["name"] + "\n" + data["street"] + "\n" + data["city"]
        )
    except:
        logger.debug("Couldn't add home address.")

    # school address
    schoolconfig = config.school[data["school"]]
    data["school_name"] = schoolconfig["school_name"]
    data["school_street"] = schoolconfig["school_street"]
    data["school_head_w_school"] = schoolconfig["school_head_w_school"]

    # Notenschutz and Nachteilsausgleich
    if data["nachteilsausgleich"] or data["notenschutz"]:
        school_subjects = get_subjects(data["school"])
        logger.debug(f"\nsubjects:\n{school_subjects}")
    if data["notenschutz"]:
        data["ns_subjects"] = school_subjects
        data["ns_zeugnisbemerkung"] = (
            "Auf die Bewertung der Rechtschreibleistung wurde verzichtet."
        )
        data["ns_measures"] = "Verzicht auf die Bewertung der Rechtschreibleistung"
    if data["nachteilsausgleich"]:
        data["na_subjects"] = school_subjects
        data["na_measures"] = (
            f"Verlängerung der Arbeitszeit um {data['nta_sprachen']}% "
            "bei schriftlichen Leistungsnachweisen und der "
            "Vorbereitungszeit bei mündlichen Leistungsnachweisen"
        )

    # for forms, I use the format dd/mm/YYYY; internally, I use YYYY-mm-dd
    today = date.today()
    data["date_today"] = today.strftime("%d/%m/%Y")
    try:
        data["birthday"] = parse(data["birthday"], dayfirst=False).strftime("%d/%m/%Y")
    except:
        logger.error("The birthday could not be parsed.")
        data["birthday"] = ""
    data["school_year"] = get_this_academic_year_string()
    data["document_shredding_date"] = data["document_shredding_date"].strftime(
        "%d/%m/%Y"
    )

    return data
