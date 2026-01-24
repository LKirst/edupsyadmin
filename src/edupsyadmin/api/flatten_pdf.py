#!/usr/bin/env python
import argparse
import warnings
from pathlib import Path

try:
    from pdf2image import convert_from_path

    installed_pdf2image = True
except ModuleNotFoundError:
    installed_pdf2image = False
try:
    from fillpdf import fillpdfs

    installed_fillpdf = True
except ModuleNotFoundError:
    installed_fillpdf = False

DEFAULT_LIBRARY = "pdf2image"


def flatten_pdf(fn_in: str | Path, library: str = DEFAULT_LIBRARY) -> None:
    """Flatten a PDF form, making form fields non-editable.

    This function takes an input PDF file with editable form fields and
    creates a "flattened" version where the fields are part of the content
    and can no longer be edited. This is useful for archiving or sharing
    completed forms.

    Two libraries can be used for this process:
    - 'pdf2image': Converts each page to an image and then combines them
      back into a PDF. This perfectly preserves the visual appearance but
      fails for tick-boxes and radio buttons. It also makes text unselectable.
      This library requires 'poppler' to be installed on the system.
    - 'fillpdf': Manipulates the PDF structure directly. It preserves
      selectable text but may fail for multiline text fields.

    A new file is created with the prefix "print_".

    :param fn_in: Path to the input PDF file.
    :param library: The library to use for flattening ('pdf2image' or 'fillpdf').
                    Defaults to DEFAULT_LIBRARY.
    :raises Exception: If the chosen library is not installed.
    """
    fn_out = add_prefix(fn_in)
    if library == "pdf2image" and installed_pdf2image:
        images = convert_from_path(fn_in)
        im1 = images[0]
        images.pop(0)
        im1.save(fn_out, "PDF", resolution=100.0, save_all=True, append_images=images)
        warnings.warn("pdf2image fails for tick-boxes and radio buttons.")
        # TODO: find solution for radio buttons
    elif library == "fillpdf" and installed_fillpdf:
        fillpdfs.flatten_pdf(fn_in, fn_out, as_images=False)
        warnings.warn("fillpdf fails for multiline text fields.")
        # TODO: find solution for multiline text fields
    else:
        raise Exception("The library you want to use is not installed.")
    print(f"Flattened {fn_in} to {fn_out}.")


def flatten_pdfs(form_paths: list[str | Path], library: str = DEFAULT_LIBRARY) -> None:
    for fn_in in form_paths:
        flatten_pdf(fn_in, library)


def add_prefix(file_path: str | Path, prefix: str = "print_") -> Path:
    file_path = Path(file_path)
    return file_path.parent / f"{prefix}{file_path.name}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inpaths", nargs="+", help="The paths of the pdf which you want to flatten."
    )
    parser.add_argument(
        "--library", default=DEFAULT_LIBRARY, choices=["fillpdf", "pdf2image"]
    )
    args = parser.parse_args()
    flatten_pdfs(args.impaths, args.library)
