import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import, parse_key_value_pairs
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.utils.path_utils import normalize_path

COMMAND_DESCRIPTION = (
    "Fill a pdf form or a text file with a liquid template. "
    "Use --tui for interactive mode, or provide client_id and form "
    "details for direct creation."
)
COMMAND_HELP = "Fill a pdf form or a text file with a liquid template"
COMMAND_EPILOG = textwrap.dedent(
    r"""         Examples:
          # Open the TUI to interactively fill a form for client with ID 1
          edupsyadmin create-documentation 1 --tui

          # Fill a PDF form for client with ID 1 using a form set named 'MyFormSet'
          edupsyadmin create-documentation 1 --form_set MyFormSet

          # Fill a text file for client with ID 2 using a specific form path
          edupsyadmin create-documentation 2 --form_paths "./path/to/template.txt"

          # Fill a form for client with ID 3, injecting custom data
          edupsyadmin create-documentation 3 --form_paths "./path/to/form.pdf" \
            --inject_data "key1=value1" "key2=value2"

          # Process multiple forms for client with ID 3 with different form paths
          edupsyadmin create-documentation 2 --form_paths "./path/to/form1.pdf" \
            "./path/to/form2.pdf"
          """,
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the create-documentation command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Open TUI for interactive form filling.",
    )
    parser.add_argument("client_id", type=int, nargs="+")
    parser.add_argument(
        "--form_set",
        type=str,
        default=None,
        help="name of a set of file paths defined in the config file",
    )
    parser.add_argument(
        "--form_paths",
        nargs="*",
        type=Path,
        default=[],
        help="form file paths",
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=None,
        help=(
            "output directory for filled forms "
            "(overrides the default from the config file)"
        ),
    )
    parser.add_argument(
        "--inject_data",
        nargs="*",
        default=[],
        help=(
            "key-value pairs in the format 'key=value'; this "
            "option can be used to override existing key=value pairs "
            "or add new key=value pairs"
        ),
    )
    encryption_group = parser.add_mutually_exclusive_group()
    encryption_group.add_argument(
        "--password",
        type=str,
        default=None,
        help="password to encrypt filled PDF forms",
    )
    encryption_group.add_argument(
        "--no-encryption",
        action="store_true",
        help="do not encrypt the output PDF(s)",
    )


def _get_pdf_password(args: Namespace) -> str | None:
    """Determine the password for PDF encryption based on CLI arguments."""
    if args.no_encryption:
        return None
    if args.password:
        return args.password
    if not args.tui:
        import getpass

        return getpass.getpass("Passwort für die PDF-Verschlüsselung: ")
    return None


def execute(args: Namespace) -> None:
    """Execute the create-documentation command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    password = _get_pdf_password(args)

    if args.tui:
        fill_form_app_cls = lazy_import("edupsyadmin.tui.fill_form_app").FillFormApp
        fill_form_app_cls(
            clients_manager=clients_manager,
            client_ids=args.client_id,
        ).run()
        return

    fill_form = lazy_import("edupsyadmin.api.fill_form").fill_form

    form_paths: list[Path] = []
    if args.form_paths:
        form_paths.extend(args.form_paths)

    if args.form_set:
        try:
            form_paths.extend(config.form_set[args.form_set])
        except KeyError as e:
            available_sets = ", ".join(config.form_set.keys())
            raise KeyError(
                "Es ist in der Konfigurationsdatei kein Form Set mit dem "
                f"Namen '{args.form_set}' angelegt. Verfügbare Sets sind: "
                f"{available_sets}",
            ) from e
    elif not form_paths and not args.tui:
        raise ValueError("At least one of 'form_set' or 'form_paths' must be non-empty")

    form_paths_normalized: list[Path] = [normalize_path(p) for p in form_paths]
    logger.debug(f"Trying to fill the files: {form_paths_normalized}")

    out_dir = args.out_dir or config.core.output_directory

    for cid in args.client_id:
        client_view = clients_manager.get_client_view(cid)
        client_data = client_view.model_dump()
        if args.inject_data:
            inject_dict = parse_key_value_pairs(
                args.inject_data,
                option_name="--inject_data",
            )
            client_data.update(inject_dict)
        fill_form(
            client_data,
            form_paths_normalized,
            out_dir=out_dir,
            password=password,
        )
