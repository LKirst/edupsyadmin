import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from liquid import parse
from liquid.exceptions import LiquidError

from edupsyadmin.api.types import ClientData
from edupsyadmin.core.logger import logger


def _ensure_output_not_exists(out_fn: Path) -> None:
    if out_fn.exists():
        raise FileExistsError(f"Output file already exists: {out_fn}")


def _add_aliases(data: ClientData | dict[str, Any]) -> dict[str, Any]:
    """
    For every key ending in '_encr', create an alias without that suffix.

    :param data: original dictionary
    :return: modified dictionary with aliases
    """
    aliased_data: dict[str, Any] = {**data}
    for key, value in data.items():
        if key.endswith("_encr"):
            alias = key.removesuffix("_encr")
            if alias not in aliased_data:
                aliased_data[alias] = value
    return aliased_data


def _modify_bool_and_none_for_pdf_form(
    data: ClientData | dict[str, Any],
) -> dict[str, Any]:
    """
    Replace every boolean True with 'Yes' and False with 'Off', which are the
    values checkboxes accept in most PDF forms. Replace None with empty
    strings.

    :param data: a dictionary of data
    :return: a modified dictionary where booleans are replaced
        with string values and None values are replaced with an empty string
    """
    updated_data: dict[str, Any] = {}
    logger.debug("Replacing True with 'Yes' and False with 'Off'")
    for key, value in data.items():
        if isinstance(value, bool):
            updated_data[key] = "Yes" if value else "Off"
        elif value is None:
            updated_data[key] = ""
        else:
            updated_data[key] = value
    return updated_data


def write_form_pypdf(fn: Path, out_fn: Path, data: ClientData | dict[str, Any]) -> None:
    """
    Fill a pdf form with data using pypdf.

    :param fn: filename of the empty pdf form
    :param out_fn: filename for the output
    :param data: the data to fill the pdf with
    :raises FileExistsError: FileExistsError
    """
    from pypdf import PdfReader, PdfWriter

    _ensure_output_not_exists(out_fn)

    data_wo_bool = _modify_bool_and_none_for_pdf_form(data)

    writer = PdfWriter()

    with fn.open("rb") as pdf_file:
        reader = PdfReader(pdf_file, strict=False)

        for page in reader.pages:
            writer.add_page(page)

        fields = reader.get_fields()
        if not fields:
            logger.debug(f"The file {fn} is not a form.")
        else:
            logger.debug(f"\nForm fields:\n{fields.keys()}")
            logger.debug(f"\nData keys:\n{data_wo_bool.keys()}")

            fields_to_update: dict[str, Any] = {}
            for key in fields:
                if key in data_wo_bool:
                    value = data_wo_bool[key]
                    if value:
                        fields_to_update[key] = value

            # update all fields at once for each page
            if fields_to_update:
                for i, page in enumerate(writer.pages):
                    try:
                        writer.update_page_form_field_values(page, fields_to_update)
                    except KeyError as e:
                        raise KeyError(
                            f"Bulk update of fields failed on p. {i + 1} of {fn.name}",
                        ) from e

    with out_fn.open("wb") as output_stream:
        writer.write(output_stream)


def write_form_fillpdf(
    fn: Path,
    out_fn: Path,
    data: ClientData | dict[str, Any],
) -> None:
    """
    Fill a pdf form with data using fillpdf.

    :param fn: filename of the empty pdf form
    :param out_fn: filename for the output
    :param data: the data to fill the pdf with
    """
    from fillpdf import fillpdfs

    _ensure_output_not_exists(out_fn)

    data_wo_bool = _modify_bool_and_none_for_pdf_form(data)

    fields = fillpdfs.get_form_fields(fn)
    logger.debug(f"\nForm fields:\n{fields}")
    logger.debug(f"\nData keys:\n{data_wo_bool.keys()}")
    if fields:
        fillpdfs.write_fillable_pdf(fn, out_fn, data_wo_bool)
    else:
        logger.info(
            f"The pdf {fn} has no form fields. Copying the file without any changes",
        )
        shutil.copyfile(fn, out_fn)


def write_form_md(fn: Path, out_fn: Path, data: ClientData | dict[str, Any]) -> None:
    """
    Render a liquid template with data passed to the function.

    :param fn: filename of a text file with the liquid template
    :param out_fn: filename for the output
    :param data: the data to fill the liquid template with
    :raises LiquidError: LiquidError
    """

    _ensure_output_not_exists(out_fn)

    with fn.open("r", encoding="utf8") as text_file:
        txt = text_file.read()
        try:
            template = parse(txt)
        except LiquidError as e:
            e.add_note(
                "There is an issue with your template "
                "(not related to the data you're trying to fill in).",
            )
            raise

        try:
            msg = template.render(**data)
        except LiquidError as e:
            e.add_note(
                "The template could be parsed, but there was an issue with "
                "rendering the template with the provided field values.",
            )
            raise

    with out_fn.open("w", encoding="utf8") as out_file:
        out_file.write(msg)


def fill_form(
    client_data: ClientData,
    form_paths: Sequence[Path],
    out_dir: Path | None = None,
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
    if out_dir is None:
        out_dir = Path()

    aliased_data = _add_aliases(client_data)

    for fp in form_paths:
        logger.info(f"Using the template {fp}")
        if not fp.is_file():
            raise FileNotFoundError(
                f"The template file does not exist: {fp}; cwd is: {Path.cwd()}",
            )
        out_fp = Path(out_dir, f"{client_data.get('client_id')}_{fp.name}")
        logger.info(f"Writing to {out_fp.resolve()}")
        if fp.suffix == ".md":
            write_form_md(fp, out_fp, aliased_data)
        elif use_fillpdf:
            write_form_fillpdf(fp, out_fp, aliased_data)
        else:
            write_form_pypdf(fp, out_fp, aliased_data)
