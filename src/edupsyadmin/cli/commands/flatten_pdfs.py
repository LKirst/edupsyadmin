import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Flatten pdf forms"
COMMAND_HELP = "Flatten pdf forms"
COMMAND_EPILOG = textwrap.dedent(
    r"""         Examples:
          # Flatten a single PDF form using the default library
          edupsyadmin flatten-pdfs "./path/to/filled_form.pdf"

          # Flatten multiple PDF forms in the current folder
          edupsyadmin flatten-pdfs *.pdf
          """,
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the flatten-pdfs command."""
    parser.set_defaults(command=execute)
    parser.add_argument("form_paths", nargs="+", type=Path)
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        default=None,
        help="password to decrypt input PDF(s) and encrypt output PDF(s)",
    )


def execute(args: Namespace) -> None:
    """Execute the flatten-pdfs command."""
    from pypdf import PdfReader

    password = args.password
    if not password:
        # Check if any PDF is encrypted
        for p in args.form_paths:
            if p.exists() and p.suffix.lower() == ".pdf":
                try:
                    reader = PdfReader(str(p))
                    if reader.is_encrypted:
                        import getpass

                        password = getpass.getpass(
                            f"Passwort für verschlüsselte PDF '{p.name}': ",
                        )
                        break
                except Exception:
                    continue

    flatten_pdfs = lazy_import("edupsyadmin.api.flatten_pdf").flatten_pdfs
    flatten_pdfs(args.form_paths, password=password)
