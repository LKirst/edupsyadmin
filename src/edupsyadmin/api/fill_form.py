from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from liquid import parse
from liquid.exceptions import LiquidError
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.types import FillFormResult
from edupsyadmin.core.logger import logger
from edupsyadmin.utils.path_utils import normalize_path


def _ensure_output_not_exists(out_fn: Path) -> None:
    if out_fn.exists():
        raise FileExistsError(f"Output file already exists: {out_fn}")


def _add_aliases(data: Mapping[str, Any]) -> dict[str, Any]:
    """
    Create aliases for keys ending in '_encr' by removing the suffix.

    :param data: original mapping
    :return: modified dictionary with aliases
    """
    aliased_data: dict[str, Any] = dict(data)
    for key, value in data.items():
        if key.endswith("_encr"):
            alias = key.removesuffix("_encr")
            aliased_data.setdefault(alias, value)
    return aliased_data


def _transform_value_for_pdf(val: Any, field: dict[str, Any]) -> NameObject | str:
    """
    Transform a value for PDF form compatibility.

    - Radio buttons: convert to NameObject with matching export value
    - Checkboxes: convert to NameObject (/Yes, /Off, or custom export)
    - Text fields: convert to string
    - None/False: convert to empty string or /Off

    :param val: the value to transform
    :param field: the field dictionary from pypdf
    :return: the transformed value
    """
    field_type = field.get("/FT")

    # Handle button fields (checkboxes and radio buttons)
    if field_type == "/Btn":
        if not val:
            return NameObject("/Off")

        exports = _get_export_values(field)
        val_str = str(val)

        # 1. Match explicit export value
        if val_str in exports:
            return NameObject(f"/{val_str}")

        # 2. Handle radio buttons (must match exactly)
        if _is_radio_button(field):
            logger.warning(
                f"Value '{val_str}' not in radio options {exports}. Setting to /Off."
            )
            return NameObject("/Off")

        # 3. Handle checkboxes (truthy fallback)
        # Use first export value (usually 'Yes') or default to 'Yes'
        best_guess = next(iter(exports)) if exports else "Yes"
        return NameObject(f"/{best_guess}")

    # Text and other field types
    return "" if val is None else str(val)


def _is_radio_button(field: dict[str, Any]) -> bool:
    """
    Check if a button field is a radio button (vs checkbox).

    Radio buttons have the /Ff (field flags) bit 15 set (0x8000).

    :param field: field dictionary from pypdf
    :return: True if radio button, False otherwise
    """
    if field.get("/FT") != "/Btn":
        return False

    ff = field.get("/Ff", 0)
    try:
        ff = int(ff)
    except TypeError, ValueError:
        ff = 0

    # Bit 15 (0x8000) indicates radio button
    return (ff & 0x8000) != 0


def _get_export_values(field: dict[str, Any]) -> set[str]:
    """Get all unique valid export values for a button field (radio/checkbox)."""
    values: set[str] = set()

    def extract(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                s = str(item)
                values.add(s.removeprefix("/"))
        elif isinstance(obj, dict):
            for key in obj:
                s = str(key)[1:] if isinstance(key, NameObject) else str(key)
                values.add(s)

    # Strategies for extracting export values from different PDF structures
    extract(field.get("/_States_"))
    extract(field.get("/Opt"))

    ap = field.get("/AP")
    if isinstance(ap, dict):
        extract(ap.get("/N"))

    for kid in field.get("/Kids", []):
        kid_obj = kid.get_object() if hasattr(kid, "get_object") else kid
        if isinstance(kid_obj, dict):
            kid_ap = kid_obj.get("/AP")
            if isinstance(kid_ap, dict):
                extract(kid_ap.get("/N"))

    # Remove 'Off' (case-insensitive) as it represents the de-selected state
    return {v for v in values if v.lower() != "off"}


def _get_fields_to_update(
    fields: dict[str, Any],
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Determine which fields to update and with what values.

    For radio buttons, this ensures only one widget in a group is selected.

    :param fields: dictionary of form fields from pypdf
    :param data: data to fill the form with
    :return: dictionary of fields to update
    """
    fields_to_update: dict[str, Any] = {}

    for key, field in fields.items():
        if key in data:
            val = data[key]
            value = _transform_value_for_pdf(val, field)

            if value:
                fields_to_update[key] = value

    return fields_to_update


def write_form_pypdf(fn: Path, out_fn: Path, data: Mapping[str, Any]) -> None:
    """
    Fill a pdf form with data using pypdf.

    :param fn: filename of the empty pdf form
    :param out_fn: filename for the output
    :param data: the data to fill the pdf with
    :raises FileExistsError: FileExistsError
    """
    _ensure_output_not_exists(out_fn)

    writer = PdfWriter()

    with fn.open("rb") as pdf_file:
        reader = PdfReader(pdf_file, strict=False)
        writer.append(reader)

        fields = reader.get_fields()
        if not fields:
            logger.debug(f"The file {fn} is not a form.")
        else:
            logger.debug(f"Form fields: {fields.keys()}")
            logger.debug(f"Data keys: {data.keys()}")

            fields_to_update = _get_fields_to_update(fields, data)

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


def write_form_md(fn: Path, out_fn: Path, data: Mapping[str, Any]) -> None:
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
    client_data: ClientView | dict[str, Any],
    form_paths: Sequence[Path],
    out_dir: Path | None = None,
) -> None:
    """
    A wrapper function for different functions to fill out forms and
    templates based on client data.

    :param client_data: ClientView instance or value key pairs where the key is
        the name of the form field or liquid variable
    :param form_paths: a list of paths to pdf forms or liquid templates
    :param out_dir: optional output directory
    """
    if out_dir is None:
        out_dir = Path()

    # Convert to dict if it's a ClientView to ensure all dynamic fields are available
    # for the template/form filling logic which might not know the field names.
    data_dict = (
        client_data.model_dump() if isinstance(client_data, ClientView) else client_data
    )

    aliased_data = _add_aliases(data_dict)

    for fp in form_paths:
        logger.info(f"Using the template {fp}")
        if not fp.is_file():
            raise FileNotFoundError(
                f"The template file does not exist: {fp}; cwd is: {Path.cwd()}",
            )
        out_fp = Path(out_dir, f"{data_dict.get('client_id')}_{fp.name}")
        logger.info(f"Writing to {out_fp.resolve()}")
        if fp.suffix == ".md":
            write_form_md(fp, out_fp, aliased_data)
        else:
            write_form_pypdf(fp, out_fp, aliased_data)


def batch_fill_forms(
    clients_manager: ClientsManager,
    client_ids: Sequence[int],
    form_paths: Sequence[str | Path],
    out_dir: Path | None = None,
) -> list[FillFormResult]:
    """
    Fill forms for multiple clients.

    Returns a list of FillFormResult objects.

    :param clients_manager: an instance of ClientsManager
    :param client_ids: a list of client IDs
    :param form_paths: a list of paths to forms or templates
    :param out_dir: optional output directory
    :return: list of FillFormResult
    """
    results: list[FillFormResult] = []
    form_paths_normalized = [normalize_path(p) for p in form_paths]
    out_dir_path = Path(out_dir) if out_dir else None

    for client_id in client_ids:
        try:
            view = clients_manager.get_client_view(client_id)
            fill_form(
                view,
                form_paths_normalized,
                out_dir=out_dir_path,
            )
            results.append(
                {"client_id": client_id, "success": True, "error": None},
            )
        except Exception as e:
            results.append(
                {"client_id": client_id, "success": False, "error": e},
            )
    return results
