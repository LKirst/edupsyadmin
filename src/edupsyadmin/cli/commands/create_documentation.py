import os
import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = (
    "Fill a pdf form or a text file with a liquid template. "
    "Use --tui for interactive mode, or provide client_id and form "
    "details for direct creation."
)
COMMAND_HELP = "Fill a pdf form or a text file with a liquid template"
COMMAND_EPILOG = textwrap.dedent(
    r"""         Examples:
          # Open the TUI to interactively fill a form
          edupsyadmin create_documentation --tui

          # Fill a PDF form for client with ID 1 using a form set named 'MyFormSet'
          edupsyadmin create_documentation 1 --form_set MyFormSet

          # Fill a text file for client with ID 2 using a specific form path
          edupsyadmin create_documentation 2 --form_paths "./path/to/template.txt"

          # Fill a form for client with ID 3, injecting custom data
          edupsyadmin create_documentation 3 --form_paths "./path/to/form.pdf" \
            --inject_data "key1=value1" "key2=value2"
          """
)


def _normalize_path(path: str | os.PathLike[str]) -> Path:
    if not path:
        raise ValueError("Path cannot be empty")
    return Path(path).expanduser().resolve()


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the create_documentation command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--tui", action="store_true", help="Open TUI for interactive form filling."
    )
    parser.add_argument("client_id", type=int, nargs="*", default=[])
    parser.add_argument(
        "--form_set",
        type=str,
        default=None,
        help="name of a set of file paths defined in the config file",
    )
    parser.add_argument(
        "--form_paths", nargs="*", type=Path, default=[], help="form file paths"
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


def execute(args: Namespace) -> None:
    """Execute the create_documentation command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )
    if args.tui:
        fill_form_app_cls = lazy_import("edupsyadmin.tui.fill_form_app").FillFormApp
        fill_form_app_cls(clients_manager=clients_manager).run()
        return

    if not args.client_id:
        raise ValueError(
            "At least one 'client_id' must be provided when not using --tui."
        )

    add_convenience_data = lazy_import(
        "edupsyadmin.api.add_convenience_data"
    ).add_convenience_data
    fill_form = lazy_import("edupsyadmin.api.fill_form").fill_form

    form_paths = args.form_paths if args.form_paths is not None else []
    if args.form_set:
        try:
            form_paths.extend(config.form_set[args.form_set])
        except KeyError:
            available_sets = ", ".join(config.form_set.keys())
            raise KeyError(
                "Es ist in der Konfigurationsdatei kein Form Set mit dem "
                f"Namen '{args.form_set}' angelegt. Verfügbare Sets sind: "
                f"{available_sets}"
            )
    elif not form_paths and not args.tui:
        raise ValueError("At least one of 'form_set' or 'form_paths' must be non-empty")

    form_paths_normalized: list[Path] = [_normalize_path(p) for p in form_paths]
    logger.debug(f"Trying to fill the files: {form_paths_normalized}")
    for cid in args.client_id:
        client_dict = clients_manager.get_decrypted_client(cid)
        client_dict_w_convdat = add_convenience_data(client_dict)
        if args.inject_data:
            inject_dict = dict(pair.split("=", 1) for pair in args.inject_data)
            client_dict_w_convdat = client_dict_w_convdat | inject_dict
        fill_form(client_dict_w_convdat, form_paths_normalized)
