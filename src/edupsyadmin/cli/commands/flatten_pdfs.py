import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Flatten pdf forms (experimental)"
COMMAND_HELP = "Flatten pdf forms (experimental)"
COMMAND_EPILOG = textwrap.dedent(
    r"""         Examples:
          # Flatten a single PDF form using the default library
          edupsyadmin flatten_pdfs "./path/to/filled_form.pdf"

          # Flatten multiple PDF forms in the current folder
          edupsyadmin flatten_pdfs *.pdf
          """
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the flatten_pdfs command."""
    default_library = lazy_import("edupsyadmin.api.flatten_pdf").DEFAULT_LIBRARY
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--library", type=str, default=default_library, choices=["pdf2image", "fillpdf"]
    )
    parser.add_argument("form_paths", nargs="+", type=Path)


def execute(args: Namespace) -> None:
    """Execute the flatten_pdfs command."""
    flatten_pdfs = lazy_import("edupsyadmin.api.flatten_pdf").flatten_pdfs
    flatten_pdfs(args.form_paths, args.library)
