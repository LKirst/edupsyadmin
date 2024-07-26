#!/usr/bin/env python
import argparse
from itertools import product
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from datetime import date, datetime
from dateutil.parser import parse
import pandas as pd
from fillpdf import fillpdfs
import shutil

from ..core.logger import logger
from ..core.encrypt import Encryption
from ..core.config import config


def add_convenience_data(data:dict) -> dict:
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
            data["name"] +
            "\n" + data["street"] + "\n" + data["city"]
        )
    except:
        logger.debug("Couldn't add home address.")

    # school address
    schoolconfig = config.school[data["school"]]
    data["school_name"]=schoolconfig["school_name"]
    data["school_street"]=schoolconfig["school_street"]
    data["school_head_w_school"]=schoolconfig["school_head_w_school"]

    # for forms, I use the format dd/mm/YYYY; internally, I use YYYY-mm-dd
    today = date.today()
    data["date_today"] = today.strftime("%d/%m/%Y")
    try:
        data["birthday"] = parse(data["birthday"], dayfirst=False).strftime('%d/%m/%Y')
    except:
        logger.error("The birthday could not be parsed.")
        data["birthday"] = ""
    data["school_year"] = "2023/24"

    return data

def write_form(fn, out_fn, data, verbose=False):
    reader = PdfReader(open(fn, "rb"), strict=False)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields()
    if not fields:
        logger.debug(f"The file {fn} is not a form.")
    else:
        logger.debug("\nForm fields:")
        logger.debug(fields.keys())
        comb_key_fields=product(range(len(reader.pages)), fields.keys())
        for i, key in comb_key_fields:
            if key in data.keys():
                try:
                    if data[key]:
                        writer.update_page_form_field_values(
                            writer.pages[i], {key: data[key]}
                        )
                except:
                    logger.debug(f"Couldn't fill in {key} on p. {i+1} of {fn.name}")
    if out_fn.exists():
        raise FileExistsError
    with open(out_fn, "wb") as output_stream:
        writer.write(output_stream)

def write_form2(fn, out_fn, data, verbose=False):
    fields=fillpdfs.get_form_fields(fn)
    logger.debug("Form fields:")
    logger.debug(fields)
    if fields:
        fillpdfs.write_fillable_pdf(fn, out_fn, data)
    else:
        logger.info((
            f"The pdf {fn} has no form fields. "
            "Copying the file without any changes"
            ))
        shutil.copyfile(fn, out_fn)


def fill_form(
        client_data:dict,
        form_paths:list[str],
        use_fillpdf:bool=True,
        verbose:bool=False):
    data = add_convenience_data(client_data)
    for fn in form_paths:
        fn = Path(fn)
        logger.info(f"Using the template {fn}")
        out_fn = Path(f"{data['client_id']}_{fn.name}")
        logger.info(f"Writing to {out_fn}")
        if use_fillpdf:
            write_form2(fn, out_fn, data, verbose=verbose)
        else:
            write_form(fn, out_fn, data, verbose=verbose)
