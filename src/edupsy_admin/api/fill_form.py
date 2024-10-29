from itertools import product
from pypdf import PdfReader, PdfWriter
from pathlib import Path
import shutil

from liquid import Template, exceptions
from fillpdf import fillpdfs

from .add_convenience_data import add_convenience_data
from ..core.logger import logger


def write_form_pdf(fn, out_fn, data, verbose=False):
    """uses pypdf"""
    reader = PdfReader(open(fn, "rb"), strict=False)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields()
    if not fields:
        logger.debug(f"The file {fn} is not a form.")
    else:
        logger.debug("\nForm fields:\n{fields.keys()}")
        logger.debug(f"\nData keys:\n{data.keys()}")
        comb_key_fields = product(range(len(reader.pages)), fields.keys())
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


def write_form_pdf2(fn, out_fn, data, verbose=False):
    """uses the library fillpdf"""
    fields = fillpdfs.get_form_fields(fn)
    logger.debug(f"\nForm fields:\n{fields}")
    logger.debug(f"\nData keys:\n{data.keys()}")
    if fields:
        fillpdfs.write_fillable_pdf(fn, out_fn, data)
    else:
        logger.info(
            (
                f"The pdf {fn} has no form fields. "
                "Copying the file without any changes"
            )
        )
        shutil.copyfile(fn, out_fn)


def write_form_md(fn, out_fn, data):
    with open(fn, "r", encoding="utf8") as text_file:
        txt = text_file.read()
        try:
            template = Template(txt)
        except exceptions.Error as e:
            print(txt)
            raise e
        try:
            msg = template.render(**data)
        except exceptions.Error as e:
            print(e)
            msg = ""
    with open(out_fn, "w", encoding="utf8") as out_file:
        out_file.writelines(msg)


def fill_form(
    client_data: dict,
    form_paths: list[str],
    use_fillpdf: bool = True,
    verbose: bool = False,
):
    data = add_convenience_data(client_data)
    for fn in form_paths:
        fn = Path(fn)
        logger.info(f"Using the template {fn}")
        out_fn = Path(f"{data['client_id']}_{fn.name}")
        logger.info(f"Writing to {out_fn}")
        if fn.suffix == ".md":
            write_form_md(fn, out_fn, data)
        elif use_fillpdf:
            write_form_pdf2(fn, out_fn, data, verbose=verbose)
        else:
            write_form_pdf(fn, out_fn, data, verbose=verbose)
