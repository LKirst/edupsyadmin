"""Flatten PDF forms by merging annotation appearance streams into page content.

Strategy
--------
For each widget annotation on each page:

1. If the annotation has a valid, non-empty ``/AP /N`` stream, stamp it as-is
   (same as before, but now also inheriting ``/AcroForm /DR`` resources).
2. If the appearance is absent or the document has ``NeedAppearances = true``,
   synthesise a minimal appearance from the field value (``/V``) and the
   default appearance string (``/DA``).

After all annotations are stamped the ``/Annots`` array and the ``/AcroForm``
dictionary are removed so the result is a plain, non-interactive PDF.

Limitations
-----------
- Synthesised text appearance uses a simple single-line or word-wrapped
  layout.  Complex rich-text (``/RV``) entries are ignored.
- Comb fields and special quadding beyond left/centre/right are not
  implemented.
- If a field has no value and no appearance stream, it is silently skipped.
"""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import wrap

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    EncodedStreamObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NumberObject,
    PdfObject,
    RectangleObject,
    StreamObject,
)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

_Rect = tuple[float, float, float, float]  # x0, y0, x1, y1

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Matches the font-setting operator in a /DA string, e.g. "/Helv 12 Tf"
_DA_FONT_RE = re.compile(r"/(\S+)\s+([\d.]+)\s+Tf")

# Default values for missing appearance data
_DEFAULT_FONT_NAME = "Helv"
_DEFAULT_FONT_SIZE = 12.0
_DEFAULT_COLOR_OPS = "0 g"
_DEFAULT_DA_STRING = "/Helv 12 Tf 0 g"

# Text layout constants
_AUTO_SIZE_RATIO = 0.75
_MAX_AUTO_FONT_SIZE = 14.0
_LINE_HEIGHT_RATIO = 1.2
_CHAR_WIDTH_ESTIMATE = 0.5
_DEFAULT_PAD_RATIO = 0.02
_DEFAULT_PAD_Y_RATIO = 0.05
_MAX_PADDING = 2.0
_VERTICAL_OFFSET_RATIO = 0.2

# Field flags (bit positions)
_MULTILINE_FLAG_BIT = 12

# Text alignment values
_ALIGN_LEFT = 0
_ALIGN_CENTER = 1
_ALIGN_RIGHT = 2


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _rect_to_floats(rect_obj: object) -> _Rect:
    """Convert a PDF rectangle object to a plain float tuple.

    :param rect_obj: A PDF ``ArrayObject`` or ``RectangleObject``.
    :return: ``(x0, y0, x1, y1)`` in user-space units.
    :raises ValueError: If the object cannot be interpreted as a rectangle.
    """
    if isinstance(rect_obj, RectangleObject):
        return (
            float(rect_obj.left),
            float(rect_obj.bottom),
            float(rect_obj.right),
            float(rect_obj.top),
        )
    if isinstance(rect_obj, ArrayObject) and len(rect_obj) == 4:
        floats = [float(v) for v in rect_obj]
        return (floats[0], floats[1], floats[2], floats[3])
    raise ValueError(f"Cannot parse rectangle: {rect_obj!r}")


def _calculate_rect_dimensions(rect: _Rect) -> tuple[float, float]:
    """Calculate width and height from a rectangle.

    :param rect: Rectangle as ``(x0, y0, x1, y1)``.
    :return: ``(width, height)`` tuple.
    """
    x0, y0, x1, y1 = rect
    return x1 - x0, y1 - y0


# ---------------------------------------------------------------------------
# Default appearance parsing
# ---------------------------------------------------------------------------


class _DefaultAppearance:
    """Parsed representation of a PDF ``/DA`` (default appearance) string.

    :param da_string: Raw ``/DA`` value from the field or ``/AcroForm``.
    """

    font_name: str  # resource name, e.g. "Helv"
    font_size: float  # in points; 0 means "auto"
    extra_ops: str  # colour and other operators before/after Tf

    def __init__(self, da_string: str) -> None:
        match = _DA_FONT_RE.search(da_string)
        if match:
            self.font_name = match.group(1)
            self.font_size = float(match.group(2))
            # Capture all operators EXCEPT the font setting itself
            self.extra_ops = (
                da_string[: match.start()].strip()
                + " "
                + da_string[match.end() :].strip()
            ).strip()
        else:
            self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default values when DA string cannot be parsed."""
        self.font_name = _DEFAULT_FONT_NAME
        self.font_size = _DEFAULT_FONT_SIZE
        self.extra_ops = _DEFAULT_COLOR_OPS

    def effective_font_size(self, field_height: float) -> float:
        """Return a usable font size, substituting a sensible default for 0.

        :param field_height: Height of the annotation rectangle in points.
        :return: Font size in points.
        """
        if self.font_size > 0:
            return self.font_size
        # Auto-size: ~75% of the field height, capped for readability
        auto_size = field_height * _AUTO_SIZE_RATIO
        return min(auto_size, _MAX_AUTO_FONT_SIZE)


# ---------------------------------------------------------------------------
# AcroForm helpers
# ---------------------------------------------------------------------------


def _get_acroform(reader: PdfReader) -> DictionaryObject | None:
    """Return the ``/AcroForm`` dictionary from the document catalog.

    :param reader: An open :class:`~pypdf.PdfReader`.
    :return: The ``/AcroForm`` dictionary, or *None* if absent.
    """
    root_obj = reader.trailer["/Root"].get_object()
    if not isinstance(root_obj, DictionaryObject):
        return None
    acroform_raw = root_obj.get("/AcroForm")
    if acroform_raw is None:
        return None
    acroform = acroform_raw.get_object()
    return acroform if isinstance(acroform, DictionaryObject) else None


def _get_acroform_dr(reader: PdfReader) -> DictionaryObject | None:
    """Return the ``/DR`` (default resources) dictionary from ``/AcroForm``.

    :param reader: An open :class:`~pypdf.PdfReader`.
    :return: The ``/DR`` dictionary, or *None* if absent.
    """
    acroform = _get_acroform(reader)
    if acroform is None:
        return None
    dr_raw = acroform.get("/DR")
    if dr_raw is None:
        return None
    return dr_raw.get_object()


def _need_appearances(reader: PdfReader) -> bool:
    """Return *True* if ``/AcroForm /NeedAppearances`` is set.

    :param reader: An open :class:`~pypdf.PdfReader`.
    :return: Boolean flag value.
    """
    acroform = _get_acroform(reader)
    if acroform is None:
        return False
    flag = acroform.get("/NeedAppearances")
    return bool(flag) if flag is not None else False


def _get_acroform_da(reader: PdfReader) -> str:
    """Return the default appearance string from ``/AcroForm /DA``.

    :param reader: An open :class:`~pypdf.PdfReader`.
    :return: The ``/DA`` string, or empty string if absent.
    """
    acroform = _get_acroform(reader)
    if acroform is None:
        return ""
    da_raw = acroform.get("/DA")
    return str(da_raw) if da_raw is not None else ""


# ---------------------------------------------------------------------------
# Resource merging
# ---------------------------------------------------------------------------


def _merge_subdictionaries(
    base_dict: DictionaryObject,
    extra_dict: DictionaryObject,
    key: str,
) -> None:
    """Merge a subdictionary from extra into base (base takes priority).

    :param base_dict: Primary dictionary to merge into (modified in-place).
    :param extra_dict: Secondary dictionary to pull missing keys from.
    :param key: The subdictionary key to merge (e.g., "/Font").
    """
    if key not in base_dict:
        base_dict[NameObject(key)] = extra_dict[key]
        return

    existing = base_dict[key].get_object()
    incoming = extra_dict[key].get_object()

    if not isinstance(existing, DictionaryObject):
        return
    if not isinstance(incoming, DictionaryObject):
        return

    sub = DictionaryObject(existing)
    for sub_key, sub_val in incoming.items():
        if sub_key not in sub:
            sub[NameObject(sub_key)] = sub_val
    base_dict[NameObject(key)] = sub


def _merge_resources(
    base: DictionaryObject | None,
    extra: DictionaryObject | None,
) -> DictionaryObject | None:
    """Shallow-merge two PDF resource dictionaries.

    Sub-dictionaries (``/Font``, ``/XObject``, …) are merged key-by-key;
    *base* values take priority.

    :param base: Primary resource dictionary (may be *None*).
    :param extra: Secondary resource dictionary to pull missing keys from.
    :return: Merged dictionary, or *None* if both inputs are *None*.
    """
    if base is extra is None:
        return None
    if base is None:
        return extra
    if extra is None:
        return base

    merged = DictionaryObject(base)
    for key, value in extra.items():
        if key not in merged:
            merged[NameObject(key)] = value
        else:
            _merge_subdictionaries(merged, extra, key)

    return merged


# ---------------------------------------------------------------------------
# Appearance stream extraction
# ---------------------------------------------------------------------------


def _is_empty_stream(data: bytes) -> bool:
    """Check if stream data is empty or contains only whitespace/q Q.

    :param data: Stream bytes.
    :return: True if the stream is effectively empty.
    """
    return not data or data.strip() in (b"", b"q Q", b"q\nQ")


def _get_appearance_state_stream(
    ap_dict: DictionaryObject,
    annot: DictionaryObject,
) -> PdfObject | None:
    """Get the appropriate appearance stream based on annotation state.

    For choice dicts (checkbox/radio), picks the current state via /AS.

    :param ap_dict: The /AP dictionary.
    :param annot: Widget annotation dictionary.
    :return: The appearance stream object or None.
    """
    n_raw = ap_dict.get("/N")
    if n_raw is None:
        return None

    n_obj = n_raw.get_object()

    # Choice dict (checkbox/radio): pick the current state via /AS
    if isinstance(n_obj, DictionaryObject):
        as_entry = annot.get("/AS")
        if as_entry is None:
            return None
        chosen_raw = n_obj.get(as_entry)
        if chosen_raw is None:
            return None
        return chosen_raw.get_object()

    return n_obj


def _ap_stream_bytes_and_resources(
    annot: DictionaryObject,
) -> tuple[bytes, DictionaryObject | None] | None:
    """Extract appearance stream bytes and its own resource dict.

    Returns *None* if no usable appearance stream is present or if the
    stream is empty (just whitespace / ``q Q``).

    :param annot: Widget annotation dictionary.
    :return: ``(stream_bytes, resources)`` or *None*.
    """
    ap_raw = annot.get("/AP")
    if ap_raw is None:
        return None

    ap = ap_raw.get_object()
    if not isinstance(ap, DictionaryObject):
        # Some malformed PDFs might have /AP as a string. Treat this as having
        # no usable appearance so we synthesise one.
        return None

    n_obj = _get_appearance_state_stream(ap, annot)
    if n_obj is None or not _is_stream_object(n_obj):
        return None

    try:  # because of the checks above, I know that n_obj is a  stream object
        data = n_obj.get_data()  # ty: ignore[unresolved-attribute]
    except Exception:
        return None

    if _is_empty_stream(data):
        return None

    resources = None
    if isinstance(n_obj, DictionaryObject):
        resources = n_obj.get("/Resources")
    return data, resources


def _get_ap_bbox(annot: DictionaryObject) -> ArrayObject | None:
    """Return the ``/BBox`` of the normal appearance stream, if present.

    For choice dicts (checkbox/radio) the currently selected state is
    resolved via ``/AS`` before reading ``/BBox``.

    :param annot: Widget annotation dictionary.
    :return: The ``/BBox`` ``ArrayObject`` or *None*.
    """
    ap_raw = annot.get("/AP")
    if ap_raw is None:
        return None

    ap = ap_raw.get_object()
    if not isinstance(ap, DictionaryObject):
        return None

    n_obj = _get_appearance_state_stream(ap, annot)
    if (n_obj is None) or not isinstance(n_obj, DictionaryObject):
        return None

    bbox_raw = n_obj.get("/BBox")
    if bbox_raw is None:
        return None

    result = bbox_raw.get_object()
    return result if isinstance(result, ArrayObject) else None


# ---------------------------------------------------------------------------
# Text appearance synthesis
# ---------------------------------------------------------------------------


def _word_wrap_to_lines(text: str, chars_per_line: int) -> list[str]:
    """Wrap *text* to a list of lines of at most *chars_per_line* characters.

    Preserves existing newlines.

    :param text: Input string.
    :param chars_per_line: Maximum characters per output line.
    :return: List of strings, one per line.
    """
    result: list[str] = []
    for paragraph in text.splitlines():
        if len(paragraph) <= chars_per_line:
            result.append(paragraph)
        else:
            result.extend(wrap(paragraph, chars_per_line) or [""])
    return result or [""]


def _escape_pdf_string(text: str) -> str:
    """Escape special characters for use inside a PDF literal string ``(...)``.

    Non-ASCII characters are converted to octal escapes using the CP1252
    encoding, which is the standard for most PDF viewers when using
    built-in fonts like Helvetica.

    :param text: Plain text.
    :return: Escaped text safe for embedding between parentheses.
    """
    result = []
    for char in text:
        if char == "\\":
            result.append("\\\\")
        elif char == "(":
            result.append("\\(")
        elif char == ")":
            result.append("\\)")
        elif char == "\r":
            result.append("\\r")
        elif char == "\n":
            result.append("\\n")
        elif ord(char) > 126:
            # Octal escape for WinAnsi (cp1252).
            try:
                # Most standard fonts use an encoding close to CP1252.
                result.extend(f"\\{byte:03o}" for byte in char.encode("cp1252"))
            except UnicodeEncodeError:
                # Fallback for characters not in CP1252
                result.append("?")
        else:
            result.append(char)
    return "".join(result)


def _calculate_padding(width: float, height: float) -> tuple[float, float]:
    """Calculate horizontal and vertical padding for a field.

    :param width: Field width in points.
    :param height: Field height in points.
    :return: ``(pad_x, pad_y)`` tuple.
    """
    pad_x = min(_MAX_PADDING, width * _DEFAULT_PAD_RATIO)
    pad_y = min(_MAX_PADDING, height * _DEFAULT_PAD_Y_RATIO)
    return pad_x, pad_y


def _prepare_text_lines(
    value: str,
    multiline: bool,
    inner_width: float,
    font_size: float,
) -> list[str]:
    """Prepare text lines for rendering, applying word wrap if needed.

    :param value: The text value to render.
    :param multiline: Whether the field is multiline.
    :param inner_width: Available width for text (after padding).
    :param font_size: Font size in points.
    :return: List of text lines.
    """
    if multiline:
        char_width_est = font_size * _CHAR_WIDTH_ESTIMATE
        chars_per_line = max(1, int(inner_width / char_width_est))
        return _word_wrap_to_lines(value, chars_per_line)
    return [value.replace("\n", " ")]


def _calculate_first_line_y(
    height: float,
    pad_y: float,
    font_size: float,
    multiline: bool,
) -> float:
    """Calculate the Y position for the first line of text.

    :param height: Field height in points.
    :param pad_y: Vertical padding in points.
    :param font_size: Font size in points.
    :param multiline: Whether the field is multiline.
    :return: Y coordinate for the first line.
    """
    if multiline:
        return height - pad_y - font_size
    return (height - font_size) / 2.0 + font_size * _VERTICAL_OFFSET_RATIO


def _x_for_quadding(
    quadding: int,
    pad_x: float,
    width: float,
    line: str,
    font_size: float,
) -> float:
    """Return the x starting position for a line given its alignment.

    :param quadding: 0 = left, 1 = centre, 2 = right.
    :param pad_x: Horizontal padding in points.
    :param width: Field width in points.
    :param line: The text of the line (used for width estimation).
    :param font_size: Current font size in points.
    :return: X coordinate in XObject local space.
    """
    approx_text_width = len(line) * font_size * _CHAR_WIDTH_ESTIMATE

    if quadding == _ALIGN_CENTER:
        return max(pad_x, (width - approx_text_width) / 2.0)
    if quadding == _ALIGN_RIGHT:
        return max(pad_x, width - pad_x - approx_text_width)
    return pad_x  # left (default)


def _build_text_stream_header(
    width: float,
    height: float,
    font_name: str,
    font_size: float,
    extra_ops: str,
) -> list[str]:
    """Build the header portion of a text appearance stream.

    :param width: Field width in points.
    :param height: Field height in points.
    :param font_name: Font resource name.
    :param font_size: Font size in points.
    :param extra_ops: Additional PDF operators (e.g., color).
    :return: List of PDF operators as strings.
    """
    parts = [
        "q",
        f"0 0 {width:.4f} {height:.4f} re W n",  # clip to field box
        "BT",
        f"/{font_name} {font_size:.4f} Tf",
    ]
    if extra_ops:
        parts.append(extra_ops)
    return parts


def _should_clip_line(y_position: float, pad_y: float, font_size: float) -> bool:
    """Check if a line should be clipped (falls below visible area).

    :param y_position: Absolute Y position of the line.
    :param pad_y: Vertical padding in points.
    :param font_size: Font size in points.
    :return: True if the line should be clipped.
    """
    return y_position < pad_y - font_size


def _add_text_line(
    parts: list[str],
    line: str,
    line_index: int,
    lines: list[str],
    first_y: float,
    line_height: float,
    quadding: int,
    pad_x: float,
    width: float,
    font_size: float,
    pad_y: float,
) -> None:
    """Add a single text line to the PDF stream parts.

    :param parts: List of PDF operators to append to.
    :param line: The text line to add.
    :param line_index: Index of the current line.
    :param lines: All text lines.
    :param first_y: Y position of the first line.
    :param line_height: Height between lines.
    :param quadding: Text alignment.
    :param pad_x: Horizontal padding.
    :param width: Field width.
    :param font_size: Font size.
    :param pad_y: Vertical padding.
    """
    y_abs = first_y - line_index * line_height
    if _should_clip_line(y_abs, pad_y, font_size):
        return

    if line_index == 0:
        # First line: absolute positioning
        first_x = _x_for_quadding(quadding, pad_x, width, line, font_size)
        parts.append(f"{first_x:.4f} {first_y:.4f} Td")
    else:
        # Subsequent lines: relative positioning
        prev_x = _x_for_quadding(
            quadding, pad_x, width, lines[line_index - 1], font_size
        )
        cur_x = _x_for_quadding(quadding, pad_x, width, line, font_size)
        dx = cur_x - prev_x
        parts.append(f"{dx:.4f} {-line_height:.4f} Td")

    escaped = _escape_pdf_string(line)
    parts.append(f"({escaped}) Tj")


def _synthesise_text_appearance(
    value: str,
    rect: _Rect,
    da: _DefaultAppearance,
    multiline: bool,
    quadding: int,
) -> bytes:
    """Build a minimal PDF content stream that renders *value* inside *rect*.

    The stream uses only operators and resources that already exist in the
    document (via ``/DA`` and ``/DR``), so no new fonts need to be embedded.

    The coordinate system has its origin at the lower-left corner of the
    annotation rectangle (i.e. the XObject's ``/BBox`` starts at ``0 0``).

    :param value: The text to render.
    :param rect: Annotation bounding box as ``(x0, y0, x1, y1)``.  Only the
        width and height are used; the translation to page space is handled
        by the ``cm`` operator in :func:`_stamp_xobject_onto_page`.
    :param da: Parsed default appearance.
    :param multiline: Whether the field is multiline.
    :param quadding: Text alignment: 0 = left, 1 = centre, 2 = right.
    :return: PDF content stream bytes.
    """
    width, height = _calculate_rect_dimensions(rect)
    font_size = da.effective_font_size(height)
    pad_x, pad_y = _calculate_padding(width, height)
    inner_width = width - 2 * pad_x

    lines = _prepare_text_lines(value, multiline, inner_width, font_size)
    line_height = font_size * _LINE_HEIGHT_RATIO
    first_y = _calculate_first_line_y(height, pad_y, font_size, multiline)

    parts = _build_text_stream_header(
        width, height, da.font_name, font_size, da.extra_ops
    )

    for i, line in enumerate(lines):
        _add_text_line(
            parts,
            line,
            i,
            lines,
            first_y,
            line_height,
            quadding,
            pad_x,
            width,
            font_size,
            pad_y,
        )

    parts.extend(["ET", "Q"])
    return "\n".join(parts).encode()


# ---------------------------------------------------------------------------
# XObject construction and page stamping
# ---------------------------------------------------------------------------


def _create_bbox_array(rect: _Rect) -> ArrayObject:
    """Create a PDF BBox array from a rectangle.

    :param rect: Rectangle as ``(x0, y0, x1, y1)``.
    :return: BBox array starting at origin.
    """
    width, height = _calculate_rect_dimensions(rect)
    return ArrayObject(
        [
            FloatObject(0),
            FloatObject(0),
            FloatObject(width),
            FloatObject(height),
        ]
    )


def _build_form_xobject(
    stream_bytes: bytes,
    bbox: _Rect,
    resources: DictionaryObject | None,
    original_bbox: ArrayObject | None = None,
) -> DecodedStreamObject:
    """Wrap *stream_bytes* in a Form XObject dictionary.

    :param stream_bytes: Decoded content stream bytes.
    :param bbox: Annotation rectangle ``(x0, y0, x1, y1)`` in page space,
        used to compute a fallback ``/BBox`` when *original_bbox* is absent.
    :param resources: Resource dictionary to embed, or *None*.
    :param original_bbox: The ``/BBox`` array taken verbatim from the source
        appearance stream.  When supplied it is used as-is so that the
        stream's internal coordinate system is preserved exactly.  Pass
        *None* for synthesised streams (which always use an origin-anchored
        box).
    :return: A :class:`~pypdf.generic.DecodedStreamObject` ready to be
        added to a :class:`~pypdf.PdfWriter`.
    """
    pdf_bbox = original_bbox if original_bbox is not None else _create_bbox_array(bbox)

    xobj = DecodedStreamObject()
    xobj.set_data(stream_bytes)
    xobj.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): pdf_bbox,
        }
    )

    if resources is not None:
        xobj[NameObject("/Resources")] = resources

    return xobj


def _ensure_page_resources(page: DictionaryObject) -> DictionaryObject:
    """Ensure the page has a /Resources dictionary and return it.

    :param page: Page dictionary (modified in-place if needed).
    :return: The page's resources dictionary.
    """
    if "/Resources" not in page:
        page[NameObject("/Resources")] = DictionaryObject()

    resources = page["/Resources"].get_object()
    if not isinstance(resources, DictionaryObject):
        resources = DictionaryObject()
        page[NameObject("/Resources")] = resources

    return resources


def _ensure_xobject_dict(resources: DictionaryObject) -> DictionaryObject:
    """Ensure the resources dictionary has a /XObject subdictionary.

    :param resources: Resources dictionary (modified in-place if needed).
    :return: The /XObject dictionary.
    """
    if "/XObject" not in resources:
        resources[NameObject("/XObject")] = DictionaryObject()
    xobject = resources["/XObject"].get_object()

    # Handle the case where get_object() returns None or non-DictionaryObject
    if not isinstance(xobject, DictionaryObject):
        xobject = DictionaryObject()
        resources[NameObject("/XObject")] = xobject

    return xobject


def _create_draw_command(xobj_name: str, rect: _Rect) -> bytes:
    """Create the PDF operators to draw an XObject at a specific position.

    :param xobj_name: Resource name of the XObject.
    :param rect: Position rectangle ``(x0, y0, x1, y1)``.
    :return: PDF content stream bytes.
    """
    x0, y0 = rect[0], rect[1]
    return f"q\n1 0 0 1 {x0:.4f} {y0:.4f} cm\n{xobj_name} Do\nQ\n".encode()


def _get_existing_page_content(page: DictionaryObject) -> bytes:
    """Extract existing content stream bytes from a page.

    :param page: Page dictionary.
    :return: Existing content bytes, or empty bytes if none.
    """
    existing_raw = page.get("/Contents")
    if existing_raw is None:
        return b""
    return existing_raw.get_object().get_data()


def _stamp_xobject_onto_page(
    page: DictionaryObject,
    writer: PdfWriter,
    xobj_name: str,
    xobj: DecodedStreamObject,
    rect: _Rect,
) -> None:
    """Register *xobj* in the page resource dict and append a draw call.

    :param page: Page dictionary (modified in-place).
    :param writer: Owning :class:`~pypdf.PdfWriter`.
    :param xobj_name: Resource name, e.g. ``/Fm0_3``.
    :param xobj: The Form XObject to register.
    :param rect: Annotation position ``(x0, y0, x1, y1)`` in page space.
    """
    resources = _ensure_page_resources(page)
    xobjects = _ensure_xobject_dict(resources)

    xobj_ref = writer._add_object(xobj)
    xobjects[NameObject(xobj_name)] = xobj_ref

    draw_command = _create_draw_command(xobj_name, rect)
    existing_content = _get_existing_page_content(page)

    new_content = DecodedStreamObject()
    new_content.set_data(existing_content + b"\n" + draw_command)
    page[NameObject("/Contents")] = writer._add_object(new_content)


# ---------------------------------------------------------------------------
# Resource cloning
# ---------------------------------------------------------------------------


def _is_stream_object(obj: object) -> bool:
    """Check if an object is a stream object.

    :param obj: Object to check.
    :return: True if the object is a stream.
    """
    return isinstance(obj, (StreamObject, EncodedStreamObject, DecodedStreamObject))


def _clone_dictionary(obj: DictionaryObject, writer: PdfWriter) -> IndirectObject:
    """Recursively clone a dictionary object.

    :param obj: Dictionary to clone.
    :param writer: Target PdfWriter.
    :return: Cloned dictionary with writer-owned references.
    """
    cloned_dict = DictionaryObject()
    for key, value in obj.items():
        cloned_dict[NameObject(key)] = _clone_object(value, writer)
    return writer._add_object(cloned_dict)


def _clone_array(obj: ArrayObject, writer: PdfWriter) -> IndirectObject:
    """Recursively clone an array object.

    :param obj: Array to clone.
    :param writer: Target PdfWriter.
    :return: Cloned array with writer-owned references.
    """
    cloned_array = ArrayObject(_clone_object(item, writer) for item in obj)
    return writer._add_object(cloned_array)


def _clone_indirect_object(obj: PdfObject, writer: PdfWriter) -> PdfObject:
    """Clone an indirect object by dereferencing and processing it.

    :param obj: Indirect object to clone.
    :param writer: Target PdfWriter.
    :return: Cloned object reference.
    """
    dereferenced = obj.get_object()

    if dereferenced is None:  # cannot clone a None
        raise ValueError("Indirect object dereferenced to None")

    if _is_stream_object(dereferenced):
        return writer._add_object(dereferenced)

    if isinstance(dereferenced, DictionaryObject):
        return _clone_dictionary(dereferenced, writer)

    if isinstance(dereferenced, ArrayObject):
        return _clone_array(dereferenced, writer)

    # Primitive types: return as-is
    return dereferenced


def _clone_object(obj: PdfObject, writer: PdfWriter) -> PdfObject:
    """Recursively clone an object, dereferencing and adding indirect objects.

    :param obj: Object to clone.
    :param writer: Target PdfWriter.
    :return: Cloned object.
    """
    if isinstance(obj, IndirectObject):
        return _clone_indirect_object(obj, writer)

    if _is_stream_object(obj):
        return writer._add_object(obj)

    if isinstance(obj, DictionaryObject):
        # Direct dictionary - clone recursively WITHOUT making it indirect
        cloned = DictionaryObject()
        for key, value in obj.items():
            cloned[NameObject(key)] = _clone_object(value, writer)
        return cloned

    if isinstance(obj, ArrayObject):
        return ArrayObject(_clone_object(item, writer) for item in obj)

    # Primitive types (numbers, names, strings) - return as-is
    return obj


def _clone_resources_for_writer(
    resources: DictionaryObject | IndirectObject | None,
    writer: PdfWriter,
) -> DictionaryObject | None:
    """Deep-clone a resources dictionary, copying all indirect objects to writer.

    :param resources: Original resources dictionary from reader.
    :param writer: Target PdfWriter.
    :return: Cloned resources dictionary with writer-owned references.
    """
    if resources is None:
        return None

    # Dereference to ensure we are working with the actual dictionary content
    obj = resources.get_object() if hasattr(resources, "get_object") else resources

    if not isinstance(obj, DictionaryObject):
        return None

    cloned = _clone_object(obj, writer)
    if not isinstance(cloned, DictionaryObject):
        raise TypeError(f"Expected DictionaryObject, got {type(cloned)}")
    return cloned


# ---------------------------------------------------------------------------
# Field property helpers
# ---------------------------------------------------------------------------


def _field_flags(annot: DictionaryObject) -> int:
    """Return the integer field flags (``/Ff``) for a widget annotation.

    :param annot: Widget annotation or merged field dictionary.
    :return: Integer flag value, or 0 if absent.
    """
    ff = _resolve_field_attribute(annot, "/Ff")
    if ff is None:
        return 0  # no flags are set = basic, editable, optional field
    if isinstance(ff, NumberObject):
        return int(ff)
    # Fallback for unexpected types
    return 0  # no flags are set = basic, editable, optional field


def _is_multiline(annot: DictionaryObject) -> bool:
    """Return *True* if the field has the Multiline flag set (bit 13).

    :param annot: Widget annotation dictionary.
    :return: Multiline flag value.
    """
    return bool(_field_flags(annot) & (1 << _MULTILINE_FLAG_BIT))


def _quadding(annot: DictionaryObject) -> int:
    """Return the text quadding (alignment) value for a text field.

    :param annot: Widget annotation dictionary.
    :return: 0 (left), 1 (centre), or 2 (right).
    """
    q = _resolve_field_attribute(annot, "/Q")
    if q is None:
        return _ALIGN_LEFT
    if isinstance(q, NumberObject):
        return int(q)
    # Fallback for unexpected types
    return _ALIGN_LEFT


def _resolve_field_attribute(
    annot: DictionaryObject, key: str
) -> DictionaryObject | None:
    """Walk the ``/Parent`` chain to find an inherited field attribute.

    PDF forms allow attributes like ``/DA``, ``/V``, and ``/Ff`` to be
    inherited from parent field nodes.

    :param annot: Starting annotation dictionary.
    :param key: The PDF dictionary key to look up, e.g. ``"/DA"``.
    :return: The found DictionaryObject, or *None*.
    """
    node: DictionaryObject | None = annot
    while node is not None:
        val = node.get(key)
        if val is not None:
            return val.get_object()
        parent_raw = node.get("/Parent")
        if parent_raw is None:
            break
        parent = parent_raw.get_object()
        node = parent if isinstance(parent, DictionaryObject) else None
    return None


# ---------------------------------------------------------------------------
# Widget annotation processing
# ---------------------------------------------------------------------------


def _get_annotation_rect(annot: DictionaryObject) -> _Rect | None:
    """Extract and validate the rectangle from an annotation.

    :param annot: Widget annotation dictionary.
    :return: Rectangle tuple or None if invalid.
    """
    rect_raw = annot.get("/Rect")
    if rect_raw is None:
        return None

    try:
        return _rect_to_floats(rect_raw.get_object())
    except ValueError, AttributeError:
        return None


def _should_use_existing_appearance(
    ap_result: tuple[bytes, DictionaryObject | None] | None,
    need_ap: bool,
    field_type: str,
) -> bool:
    """Determine if we should use the existing appearance stream.

    :param ap_result: Result from appearance stream extraction.
    :param need_ap: Whether NeedAppearances flag is set.
    :param field_type: Field type string.
    :return: True if existing appearance should be used.
    """
    if ap_result is None:
        return False
    # Don't use existing appearance for text fields when NeedAppearances is set
    return not (need_ap and field_type == "/Tx")


def _process_existing_appearance(
    annot: DictionaryObject,
    ap_result: tuple[bytes, DictionaryObject | None],
    rect: _Rect,
    dr: DictionaryObject | None,
    writer: PdfWriter,
) -> DecodedStreamObject:
    """Process an existing appearance stream into a Form XObject.

    :param annot: Widget annotation dictionary.
    :param ap_result: Appearance stream bytes and resources.
    :param rect: Annotation rectangle.
    :param dr: Default resources from AcroForm.
    :param writer: PdfWriter instance.
    :return: Form XObject ready to stamp.
    """
    ap_bytes, ap_resources = ap_result
    original_bbox = _get_ap_bbox(annot)

    # Clone resources to ensure all indirect objects are copied to writer
    if ap_resources is not None:
        final_resources = _clone_resources_for_writer(ap_resources, writer)
    else:
        final_resources = _clone_resources_for_writer(dr, writer)

    return _build_form_xobject(ap_bytes, rect, final_resources, original_bbox)


def _get_field_value(annot: DictionaryObject) -> str | None:
    """Get the field value, returning None if empty or absent.

    :param annot: Widget annotation dictionary.
    :return: Field value string or None.
    """
    value_raw = _resolve_field_attribute(annot, "/V")
    if value_raw is None:
        return None
    value = str(value_raw).strip()
    return value or None


def _get_default_appearance_string(
    annot: DictionaryObject,
    acroform_da: str,
) -> str:
    """Get the default appearance string for a field.

    :param annot: Widget annotation dictionary.
    :param acroform_da: Fallback DA string from AcroForm.
    :return: DA string to use.
    """
    da_raw = _resolve_field_attribute(annot, "/DA")
    if da_raw is not None:
        return str(da_raw)
    return acroform_da or _DEFAULT_DA_STRING


def _synthesise_text_field_appearance(
    annot: DictionaryObject,
    value: str,
    rect: _Rect,
    acroform_da: str,
    dr: DictionaryObject | None,
    writer: PdfWriter,
) -> DecodedStreamObject:
    """Synthesise an appearance for a text field.

    :param annot: Widget annotation dictionary.
    :param value: Field value to render.
    :param rect: Annotation rectangle.
    :param acroform_da: Default appearance string from AcroForm.
    :param dr: Default resources from AcroForm.
    :param writer: PdfWriter instance for resource cloning.
    :return: Form XObject with synthesised appearance.
    """
    da_str = _get_default_appearance_string(annot, acroform_da)
    da = _DefaultAppearance(da_str)
    multiline = _is_multiline(annot)
    q = _quadding(annot)

    ap_bytes = _synthesise_text_appearance(value, rect, da, multiline, q)
    final_resources = _clone_resources_for_writer(dr, writer)
    return _build_form_xobject(ap_bytes, rect, final_resources)


def _process_widget_annotation(
    annot: DictionaryObject,
    page_index: int,
    xobj_counter: int,
    writer_page: DictionaryObject,
    writer: PdfWriter,
    need_ap: bool,
    dr: DictionaryObject | None,
    acroform_da: str,
) -> int:
    """Process a single widget annotation, stamping its appearance if possible.

    :param annot: Widget annotation dictionary.
    :param page_index: Current page index.
    :param xobj_counter: Counter for XObject naming.
    :param writer_page: Writer's page object.
    :param writer: PdfWriter instance.
    :param need_ap: Whether NeedAppearances flag is set.
    :param dr: Default resources from AcroForm.
    :param acroform_da: Default appearance string from AcroForm.
    :return: Updated xobj_counter.
    """
    rect = _get_annotation_rect(annot)
    if rect is None:
        return xobj_counter

    xobj_name = f"/Fm{page_index}_{xobj_counter}"
    xobj_counter += 1

    field_type = str(_resolve_field_attribute(annot, "/FT") or "")

    # Try to use existing appearance
    ap_result = _ap_stream_bytes_and_resources(annot)
    if ap_result is not None and _should_use_existing_appearance(
        ap_result, need_ap, field_type
    ):
        xobj = _process_existing_appearance(annot, ap_result, rect, dr, writer)
        _stamp_xobject_onto_page(writer_page, writer, xobj_name, xobj, rect)
        return xobj_counter

    # Synthesise appearance for text fields
    if field_type != "/Tx":
        return xobj_counter

    value = _get_field_value(annot)
    if value is None:
        return xobj_counter

    xobj = _synthesise_text_field_appearance(
        annot, value, rect, acroform_da, dr, writer
    )
    _stamp_xobject_onto_page(writer_page, writer, xobj_name, xobj, rect)
    return xobj_counter


def _get_page_annotations(page: DictionaryObject) -> ArrayObject | None:
    """Get the annotations array from a page.

    :param page: Page dictionary.
    :return: Annotations array or None.
    """
    annots_raw = page.get("/Annots")
    if annots_raw is None:
        return None

    annots = annots_raw.get_object()
    return annots if isinstance(annots, ArrayObject) else None


def _process_page_annotations(
    page: DictionaryObject,
    page_index: int,
    writer_page: DictionaryObject,
    writer: PdfWriter,
    need_ap: bool,
    dr: DictionaryObject | None,
    acroform_da: str,
) -> None:
    """Process all widget annotations on a page.

    :param page: Reader's page object.
    :param page_index: Current page index.
    :param writer_page: Writer's page object.
    :param writer: PdfWriter instance.
    :param need_ap: Whether NeedAppearances flag is set.
    :param dr: Default resources from AcroForm.
    :param acroform_da: Default appearance string from AcroForm.
    """
    annots = _get_page_annotations(page)
    if annots is None:
        return

    xobj_counter = 0
    for annot_ref in annots:
        annot = annot_ref.get_object()
        if not isinstance(annot, DictionaryObject):
            continue
        if annot.get("/Subtype") != NameObject("/Widget"):
            continue

        xobj_counter = _process_widget_annotation(
            annot,
            page_index,
            xobj_counter,
            writer_page,
            writer,
            need_ap,
            dr,
            acroform_da,
        )

    # Remove interactive annotations
    if "/Annots" in writer_page:
        del writer_page[NameObject("/Annots")]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def flatten_with_pypdf(fn_in: Path, fn_out: Path) -> None:
    """Flatten a PDF form using only pypdf (pure Python, no external tools).

    For each widget annotation the function attempts, in order:

    1. **Use the existing appearance stream** (``/AP /N``), supplemented with
       the document-level default resources (``/AcroForm /DR``) so that font
       references are always resolvable.
    2. **Synthesise an appearance** from the field value (``/V``) and the
       default appearance string (``/DA``) when no usable stream exists or
       when the document flag ``NeedAppearances`` is set.

    After stamping all appearances, ``/Annots`` and ``/AcroForm`` are removed
    so the output is a plain, non-interactive PDF.

    :param fn_in: Path to the input PDF with form fields.
    :param fn_out: Path where the flattened PDF is written.
    :raises FileNotFoundError: If *fn_in* does not exist.
    """
    if not fn_in.exists():
        raise FileNotFoundError(f"Input file not found: {fn_in}")

    reader = PdfReader(str(fn_in), strict=False)
    writer = PdfWriter()

    need_ap = _need_appearances(reader)
    dr = _get_acroform_dr(reader)
    acroform_da = _get_acroform_da(reader)

    for page_index, page in enumerate(reader.pages):
        writer.add_page(page)
        writer_page = writer.pages[page_index]

        _process_page_annotations(
            page, page_index, writer_page, writer, need_ap, dr, acroform_da
        )

    # Remove the interactive form catalog entry
    if "/AcroForm" in writer._root_object:
        del writer._root_object[NameObject("/AcroForm")]

    with fn_out.open("wb") as fh:
        writer.write(fh)
