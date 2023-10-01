#!/usr/bin/env python
import argparse
from itertools import product
from msilib.schema import Error
from operator import index
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from datetime import date
import pandas as pd
from fillpdf import fillpdfs
import shutil

DATA_KEYS = [
    "first_name",
    "last_name",
    "parent_name",
    "street",
    "city",
    "class",
    "school",
    "birthday",
]

def add_convenience_data(data):
    """Add the information which can be generated from existing key value pairs.

    Parameters
    ----------
    data : dict
        A dictionary of data values. Must contain "last_name", "first_name",
        "street", "city", "parent_name"
    """
    data["name"] = data["last_name"] + ", " + data["first_name"]

    try:
        data["address"] = data["street"] + ", " + data["city"]
        data["address_parent_multiline"] = (
            data["parent_name"] + "\n" + data["street"] + "\n" + data["city"]
        )
    except:
        print("Couldn't add home address.")

    # school address
    ## USE THE CONFIG! ###
    try:
        if data["school"] == "SOMENAME":
            data["school_street"] = "XYZ"
            data["school_genitive_with_article"] = "XYZ"
        elif data["school"] == "SOMEOTHERNAME":
            data["school_street"] = "XYZ2"
            data["school_genitive_with_article"] = "XYZ2"
        else:
            print(
                "The school is not in the config file."
            )
            data["school_street"] = None
            data["school_genitive_with_article"] = None
    except:
        print("Couldn't add school address.")

    today = date.today()
    data["date_today"] = today.strftime("%d/%m/%Y")  # dd/mm/YY

    data["school_year"] = "2023/24"

    return data

def write_form(fn, data, verbose=False):
    fn = Path(fn)
    reader = PdfReader(open(fn, "rb"), strict=False)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields()
    if not fields:
        print(f"The file {fn} is not a form.")
    else:
        print("\nForm fields:")
        print(fields.keys())
        comb_key_fields=product(range(len(reader.pages)), fields.keys())
        for i, key in comb_key_fields:
            if key in data.keys():
                try:
                    if data[key]:
                        writer.update_page_form_field_values(
                            writer.pages[i], {key: data[key]}
                        )
                except:
                    print(f"Couldn't fill in {key} on p. {i+1} of {fn.name}")

    out_fn = Path(data["code"] + "_" + str(fn.name))
    if out_fn.exists():
        raise FileExistsError
    with open(out_fn, "wb") as output_stream:
        writer.write(output_stream)

def write_form2(fn, data, verbose=False):
    fn = Path(fn)
    fields=fillpdfs.get_form_fields(fn)
    print("Form fields:")
    print(fields)
    out_fn = Path(data["code"] + "_" + str(fn.name))
    if fields:
        fillpdfs.write_fillable_pdf(fn, out_fn, data)
    else:
        print(f"The pdf {fn} has no form fields. Copying the file without any changes")
        shutil.copyfile(fn, out_fn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Extract data from a csv-file or enter the data from the commandline and use the text to fill a form."
        )
    )
    parser.add_argument(
        "--path", "-p", help="The path to a csv file"
    )
    parser.add_argument(
        "--csv", action="store_true", help="The path is a csv file with the data."
    )
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument(
        "--forms",
        "-f",
        nargs="*",
        default=None,
        help="The paths of the PDF forms you want to fill.",
    )
    parser.add_argument("--use_fillpdf", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.csv:
        try:
            data = pd.read_csv(args.path, index_col=False).to_dict("records")[0]
            print(f"Data read from the csv: {data}")
            data = add_convenience_data(data)
        except:
            print(
                "Couldn't read the data from file. Creating an empty file you can use."
            )
            df = pd.DataFrame([dict.fromkeys(DATA_KEYS)])
            template_fn = Path("template_data.csv")
            if template_fn.exists():
                raise FileExistsError
            else:
                df.to_csv("template_data.csv", index=False, header=True)
    elif args.interactive:
        data = dict.fromkeys(DATA_KEYS)
        for key in data.keys():
            data[key] = input(key + ": ")
        data = add_convenience_data(data)
    else:
        text = get_text(args.path, args.verbose)
        data = extract_data_infoportal(text)
        data = add_convenience_data(data)
        print("")
        print(text, end="\n")
    print(data, end="\n")

    if args.forms:
        for fn in args.forms:
            print(f"\n\nFilling the form {fn}")
            if args.use_fillpdf:
                write_form2(fn, data, verbose=args.verbose)
            else:
                write_form(fn, data, verbose=args.verbose)
