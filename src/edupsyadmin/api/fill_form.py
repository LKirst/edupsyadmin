import os
import shutil
from itertools import product
from pathlib import Path

from liquid import Template, exceptions

from edupsyadmin.core.logger import logger


def modify_bool_for_pdf_form(data: dict) -> dict:
    """
    Replace every boolean True with 'Yes' and False with 'Off', which are
    the values checkboxes accept in most PDF forms.

    :param data: a dictionary of data
    :return: a modified dictionary where booleans are replaced
        with string values
    """
    updated_data = {}
    logger.debug("Replacing True with 'Yes' and False with 'Off'")
    for key, value in data.items():
        if isinstance(value, bool):
            updated_data[key] = "Yes" if value else "Off"
        else:
            updated_data[key] = value
    return updated_data


def write_form_pdf(fn: Path, out_fn: Path, data: dict) -> None:
    """
    Fill a pdf form with data using pypdf.

    :param fn: filename of the empty pdf form
    :param out_fn: filename for the output
    :param data: the data to fill the pdf with
    :raises FileExistsError: FileExistsError
    """
    from pypdf import PdfReader, PdfWriter

    data_wo_bool = modify_bool_for_pdf_form(data)

    reader = PdfReader(open(fn, "rb"), strict=False)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields()
    if not fields:
        logger.debug(f"The file {fn} is not a form.")
    else:
        logger.debug("\nForm fields:\n{fields.keys()}")
        logger.debug(f"\nData keys:\n{data_wo_bool.keys()}")
        comb_key_fields = product(range(len(reader.pages)), fields.keys())
        for i, key in comb_key_fields:
            if key in data_wo_bool.keys():
                try:
                    if data_wo_bool[key]:
                        writer.update_page_form_field_values(
                            writer.pages[i], {key: data_wo_bool[key]}
                        )
                except:
                    logger.debug(f"Couldn't fill in {key} on p. {i+1} of {fn.name}")
    if out_fn.exists():
        raise FileExistsError
    with open(out_fn, "wb") as output_stream:
        writer.write(output_stream)


def write_form_pdf2(fn: Path, out_fn: Path, data: dict) -> None:
    """
    Fill a pdf form with data using fillpdf.

    :param fn: filename of the empty pdf form
    :param out_fn: filename for the output
    :param data: the data to fill the pdf with
    """
    from fillpdf import fillpdfs

    data_wo_bool = modify_bool_for_pdf_form(data)

    fields = fillpdfs.get_form_fields(fn)
    logger.debug(f"\nForm fields:\n{fields}")
    logger.debug(f"\nData keys:\n{data_wo_bool.keys()}")
    if fields:
        fillpdfs.write_fillable_pdf(fn, out_fn, data_wo_bool)
    else:
        logger.info(
            (
                f"The pdf {fn} has no form fields. "
                "Copying the file without any changes"
            )
        )
        shutil.copyfile(fn, out_fn)


def write_form_md(fn: Path, out_fn: Path, data: dict) -> None:
    """
    Render a liquid template with data passed to the function.

    :param fn: filename of a text file with the liquid template
    :param out_fn: filename for the output
    :param data: the data to fill the liquid template with
    :raises [TODO:name]: [TODO:description]
    """
    with open(fn, "r", encoding="utf8") as text_file:
        txt = text_file.read()
        try:
            template = Template(txt)
        except exceptions.Error as e:
            logger.error(txt)
            raise e
        try:
            msg = template.render(**data)
        except exceptions.Error as e:
            logger.error(e)
            msg = ""
    with open(out_fn, "w", encoding="utf8") as out_file:
        out_file.writelines(msg)


def fill_form(
    client_data: dict,
    form_paths: list[str],
    out_dir: str = ".",
    use_fillpdf: bool = True,
) -> None:
    """
    A wrapper function for different functions to fill out forms and
    templates based on client data.

    :param client_data: value key pairs where the key is the name of the form
        field or liquid variable
    :param form_paths: a list of paths to pdf forms or liquid templates
    :param use_fillpdf: there are two options for pdf-forms - either a function
        that uses the library fillpdf or a function that uses pypdf2, defaults
        to True
    """
    for fn in form_paths:
        fp = Path(fn)
        logger.info(f"Using the template {fp}")
        if not fp.is_file():
            raise FileNotFoundError(
                (f"The template file does not exist: {fp}; " f"cwd is: {os.getcwd()}")
            )
        out_fp = Path(out_dir, f"{client_data['client_id']}_{fp.name}")
        logger.info(f"Writing to {out_fp}")
        if fp.suffix == ".md":
            write_form_md(fp, out_fp, client_data)
        elif use_fillpdf:
            write_form_pdf2(fp, out_fp, client_data)
        else:
            write_form_pdf(fp, out_fp, client_data)
