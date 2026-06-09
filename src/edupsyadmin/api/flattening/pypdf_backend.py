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
from dataclasses import dataclass
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

_Rect = tuple[float, float, float, float]  # x0, y0, x1, y1

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


@dataclass(frozen=True, slots=True)
class _FieldContext:
    """Immutable bundle of document-level flattening parameters.

    Parsed once from the reader at the start of :func:`flatten_with_pypdf`
    and threaded read-only through every page and annotation helper.

    :param writer: The :class:`~pypdf.PdfWriter` accumulating output pages.
    :param need_ap: Value of ``/NeedAppearances`` (default *False*).
    :param dr: Default resource dictionary (``/DR``), or *None*.
    :param da: Default appearance string (``/DA``), or empty string.
    """

    writer: PdfWriter
    need_ap: bool
    dr: DictionaryObject | None
    da: str

    @classmethod
    def _default(cls, writer: PdfWriter) -> _FieldContext:
        return cls(writer=writer, need_ap=False, dr=None, da="")

    @classmethod
    def from_reader(cls, reader: PdfReader, writer: PdfWriter) -> _FieldContext:
        """Build a :class:`_FieldContext` from an open reader and writer.

        Walks ``/Root → /AcroForm`` exactly once and snapshots the three
        entries needed for flattening.  Returns safe defaults when any
        part of the chain is absent or malformed.

        :param reader: An open :class:`~pypdf.PdfReader`.
        :param writer: The :class:`~pypdf.PdfWriter` that will receive pages.
        :return: Populated context object.
        """
        root_obj = reader.trailer["/Root"].get_object()
        if not isinstance(root_obj, DictionaryObject):
            return cls._default(writer)

        acroform_raw = root_obj.get("/AcroForm")
        if acroform_raw is None:
            return cls._default(writer)

        acroform = acroform_raw.get_object()
        if not isinstance(acroform, DictionaryObject):
            return cls._default(writer)

        flag_raw = acroform.get("/NeedAppearances")
        need_ap = bool(flag_raw) if flag_raw is not None else False

        dr_raw = acroform.get("/DR")
        dr = dr_raw.get_object() if dr_raw is not None else None

        da_raw = acroform.get("/DA")
        da = str(da_raw) if da_raw is not None else ""

        return cls(writer=writer, need_ap=need_ap, dr=dr, da=da)


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
        auto_size = field_height * _AUTO_SIZE_RATIO
        # Cap for readability
        return min(auto_size, _MAX_AUTO_FONT_SIZE)


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

    resources = n_obj.get("/Resources") if isinstance(n_obj, DictionaryObject) else None
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
    if n_obj is None or not isinstance(n_obj, DictionaryObject):
        return None

    bbox_raw = n_obj.get("/BBox")
    if bbox_raw is None:
        return None

    result = bbox_raw.get_object()
    return result if isinstance(result, ArrayObject) else None


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


def _is_stream_object(obj: object) -> bool:
    """Check if an object is a stream object.

    :param obj: Object to check.
    :return: True if the object is a stream.
    """
    return isinstance(obj, StreamObject | EncodedStreamObject | DecodedStreamObject)


def _clone_object(
    obj: PdfObject,
    writer: PdfWriter,
    *,
    indirect: bool = False,
) -> PdfObject:
    """Recursively clone a PDF object, registering indirect objects with *writer*.

    The *indirect* flag controls whether container types (dict, array) are
    registered as indirect objects in the writer (``True``) or returned as
    inline direct objects (``False``).  Streams are always registered as
    indirect objects regardless of the flag.

    When *obj* is an :class:`~pypdf.generic.IndirectObject` the referent is
    dereferenced first and the result is always registered as an indirect
    object (equivalent to the old ``_clone_indirect_object`` behaviour).

    :param obj: PDF object to clone.
    :param writer: Target :class:`~pypdf.PdfWriter` that will own any new
        indirect objects.
    :param indirect: If *True*, register cloned dicts and arrays as indirect
        objects in *writer* (equivalent to the old ``_clone_dictionary`` /
        ``_clone_array`` helpers).  Defaults to *False*.
    :return: Cloned object, possibly an
        :class:`~pypdf.generic.IndirectObject` reference when registered.
    :raises ValueError: If an :class:`~pypdf.generic.IndirectObject`
        dereferences to *None*.
    """
    # IndirectObject: dereference, then clone the referent as indirect.
    if isinstance(obj, IndirectObject):
        referent = obj.get_object()
        if referent is None:
            raise ValueError("IndirectObject dereferenced to None")
        return _clone_object(referent, writer, indirect=True)

    # Streams: always registered as indirect objects.
    if _is_stream_object(obj):
        return writer._add_object(obj)

    # DictionaryObject: clone entries, optionally register as indirect.
    if isinstance(obj, DictionaryObject):
        cloned: DictionaryObject = DictionaryObject()
        for key, value in obj.items():
            cloned[NameObject(key)] = _clone_object(value, writer)
        return writer._add_object(cloned) if indirect else cloned

    # ArrayObject: clone items, optionally register as indirect.
    if isinstance(obj, ArrayObject):
        cloned_array = ArrayObject(_clone_object(item, writer) for item in obj)
        return writer._add_object(cloned_array) if indirect else cloned_array

    # Primitives (NameObject, NumberObject, …): return as-is.
    return obj


def _clone_resources_for_writer(
    resources: DictionaryObject | IndirectObject | None,
    writer: PdfWriter,
) -> DictionaryObject | None:
    """Deep-clone a resources dictionary, copying all indirect objects to *writer*.

    :param resources: Original resources dictionary from the reader, or *None*.
    :param writer: Target :class:`~pypdf.PdfWriter`.
    :return: Cloned resources dictionary with writer-owned references, or
        *None* if *resources* is *None* or not a dictionary.
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
    xobj_index: int,
    writer_page: DictionaryObject,
    ctx: _FieldContext,
) -> None:
    """Process a single widget annotation, stamping its appearance if possible.

    :param annot: Widget annotation dictionary.
    :param page_index: Current page index.
    :param xobj_index: Unique index for XObject naming on this page.
    :param writer_page: Writer's page object.
    :param ctx: Document-level flattening context.
    """
    rect = _get_annotation_rect(annot)
    if rect is None:
        return

    xobj_name = f"/Fm{page_index}_{xobj_index}"
    field_type = str(_resolve_field_attribute(annot, "/FT") or "")

    ap_result = _ap_stream_bytes_and_resources(annot)
    if ap_result is not None and _should_use_existing_appearance(
        ap_result, ctx.need_ap, field_type
    ):
        xobj = _process_existing_appearance(annot, ap_result, rect, ctx.dr, ctx.writer)
        _stamp_xobject_onto_page(writer_page, ctx.writer, xobj_name, xobj, rect)
        return

    # Synthesise appearance only for text fields
    if field_type != "/Tx":
        return

    value = _get_field_value(annot)
    if value is None:
        return

    xobj = _synthesise_text_field_appearance(
        annot, value, rect, ctx.da, ctx.dr, ctx.writer
    )
    _stamp_xobject_onto_page(writer_page, ctx.writer, xobj_name, xobj, rect)


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


def _is_widget(annot_obj: object) -> bool:
    """Return *True* if *annot_obj* is a widget annotation dictionary.

    :param annot_obj: Dereferenced annotation object.
    :return: Boolean predicate result.
    """
    return isinstance(annot_obj, DictionaryObject) and annot_obj.get(
        "/Subtype"
    ) == NameObject("/Widget")


def _process_page_annotations(
    page: DictionaryObject,
    page_index: int,
    writer_page: DictionaryObject,
    ctx: _FieldContext,
) -> None:
    """Stamp all widget appearances on page and strip interactive annotations.

    :param page: Reader's page object.
    :param page_index: Zero-based page index.
    :param writer_page: Writer's copy of the page (modified in-place).
    :param ctx: Document-level flattening context.
    """
    annots = _get_page_annotations(page)
    if annots is None:
        return

    xobj_index = 0
    for annot_ref in annots:
        annot = annot_ref.get_object()
        if not _is_widget(annot):
            continue
        _process_widget_annotation(annot, page_index, xobj_index, writer_page, ctx)
        xobj_index += 1

    writer_page.pop(NameObject("/Annots"), None)


def flatten_with_pypdf(fn_in: Path, fn_out: Path, password: str | None = None) -> None:
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
    :param password: Password to decrypt the input PDF and encrypt the output.
    :raises FileNotFoundError: If *fn_in* does not exist.
    """
    if not fn_in.exists():
        raise FileNotFoundError(f"Input file not found: {fn_in}")

    reader = PdfReader(str(fn_in), strict=False)
    if reader.is_encrypted:
        if password:
            reader.decrypt(password)
        else:
            # We don't raise an error here because some PDFs might be
            # "encrypted" but still readable without a password (empty password)
            # but usually pypdf handles that.
            # If it's really locked, subsequent operations will fail.
            pass

    writer = PdfWriter()

    ctx = _FieldContext.from_reader(reader, writer)

    for page_index, page in enumerate(reader.pages):
        writer.add_page(page)
        _process_page_annotations(page, page_index, writer.pages[page_index], ctx)

    writer._root_object.pop(NameObject("/AcroForm"), None)

    if password:
        writer.encrypt(password, algorithm="AES-256")

    with fn_out.open("wb") as fh:
        writer.write(fh)
