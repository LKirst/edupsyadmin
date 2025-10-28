import argparse
import importlib.resources
import importlib.util
import os
import pathlib
import shutil
import sys
import textwrap
import types
from argparse import ArgumentParser, RawDescriptionHelpFormatter, _SubParsersAction
from datetime import datetime
from inspect import signature
from typing import TYPE_CHECKING, Any

from platformdirs import user_config_dir, user_data_path
from sqlalchemy import inspect as sa_inspect

from edupsyadmin.__version__ import __version__
from edupsyadmin.api.managers import ClientNotFoundError
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager

__all__ = ("main",)

APP_UID = "liebermann-schulpsychologie.github.io"
USER_DATA_DIR = user_data_path(
    appname="edupsyadmin", version=__version__, ensure_exists=True
)
DEFAULT_DB_URL = "sqlite:///" + os.path.join(USER_DATA_DIR, "edupsyadmin.db")
DEFAULT_CONFIG_PATH = os.path.join(
    user_config_dir(appname="edupsyadmin", version=__version__, ensure_exists=True),
    "config.yml",
)
DEFAULT_SALT_PATH = os.path.join(
    user_config_dir(appname="edupsyadmin", version=__version__, ensure_exists=True),
    "salt.txt",
)


# Lazy import utility function
def lazy_import(name: str) -> types.ModuleType:
    """
    Lazy import utility function. This function is from the Python
    documentation
    (https://docs.python.org/3/library/importlib.html#implementing-lazy-imports).

    :param name: The name of the module to be lazily imported.
    :return: The lazily imported module.
    """
    spec = importlib.util.find_spec(name)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find module '{name}'")

    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    """Execute the application CLI.

    :param argv: argument list to parse (sys.argv by default)
    :return: exit status
    """
    args = _args(argv)

    # start logging
    logger.start(args.warn or "DEBUG")  # can't use default from config yet

    # config
    # if the (first) config file doesn't exist, copy a sample config
    if not os.path.exists(args.config_path):
        template_path = str(
            importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
        )
        shutil.copy(template_path, args.config_path)
        logger.info(
            "Could not find the specified config file. "
            f"Created a sample config at {args.config_path}. "
            "Fill it with your values."
        )
    config.load(args.config_path)
    config.core.config = args.config_path
    if args.warn:
        config.core.logging = args.warn

    # restart logging based on config
    logger.stop()  # clear handlers to prevent duplicate records
    logger.start(config.core.logging)

    if not args.app_username:
        logger.debug(f"using config.core.app_username: '{config.core.app_username}'")
        try:
            args.app_username = config.core.app_username
        except KeyError as exc:
            logger.error(
                "Either pass app_username from the "
                "commandline or set app_username in the config.yml"
            )
            raise exc
    else:
        logger.debug(f"using username passed as cli argument: '{args.app_username}'")

    # handle commandline args
    command = args.command
    logger.debug(f"commandline arguments: {vars(args)}")
    argsdict = vars(args)

    # Filter arguments based on the function signature
    func_sig = signature(command)
    filtered_args = {
        key: argsdict[key] for key in func_sig.parameters if key in argsdict
    }

    try:
        command(**filtered_args)
    except (RuntimeError, ClientNotFoundError) as err:
        logger.critical(err)
        return 1
    logger.debug("successful completion")
    return 0


# Command Functions
def command_info(
    app_uid: str | os.PathLike[str],
    app_username: str,
    database_url: str,
    config_path: str | os.PathLike[str],
    salt_path: str | os.PathLike[str],
) -> None:
    info = lazy_import("edupsyadmin.info").info
    info(app_uid, app_username, database_url, config_path, salt_path)


def command_edit_config(
    config_path: str | os.PathLike[str],
) -> None:
    config_editor_app_cls = lazy_import("edupsyadmin.tui.editconfig").ConfigEditorApp
    config_editor_app_cls(config_path).run()


def _enter_client_csv(
    clients_manager: ClientsManager,
    csv_path: str | os.PathLike[str],
    school: str | None,
    name: str,
    import_config_name: str | None = None,
) -> int:
    """
    Read client from a csv file.

    :param clients_manager: a ClientsManager instance used to add the client to the db
    :param csv_path: path to a csv file
    :param school: short name of the school as set in the config file
    :param name: name of the client as specified in the "name" column of the csv
    :param import_config_name: name of the csv import configuration from the config
    return: client_id
    """
    pd = lazy_import("pandas")
    from edupsyadmin.db import clients

    client_cls = clients.Client

    if import_config_name:
        import_conf = config.csv_import[import_config_name]
        separator = import_conf.separator
        column_mapping = import_conf.column_mapping
    else:
        # Default to original hardcoded behavior
        separator = "\t"
        column_mapping = {
            "gender": "gender_encr",
            "entryDate": "entry_date",
            "klasse.name": "class_name",
            "foreName": "first_name_encr",
            "longName": "last_name_encr",
            "birthDate": "birthday_encr",
            "address.street": "street_encr",
            "address.postCode": "postCode",
            "address.city": "city",
            "address.mobile": "telephone1_encr",
            "address.phone": "telephone2_encr",
            "address.email": "email_encr",
        }

    df = pd.read_csv(csv_path, sep=separator, encoding="utf-8", dtype=str)
    df = df.rename(columns=column_mapping)

    # this is necessary so that telephone numbers are strings that can be encrypted
    df["telephone1_encr"] = df["telephone1_encr"].fillna("").astype(str)
    df["telephone2_encr"] = df["telephone2_encr"].fillna("").astype(str)

    # The 'name' column is not in the mapping, it's used for lookup
    if "name" not in df.columns:
        # If the original 'name' column was mapped, find its new name
        lookup_col = next(
            (
                new_name
                for old_name, new_name in column_mapping.items()
                if old_name == "name"
            ),
            "name",
        )
    else:
        lookup_col = "name"

    client_series = df[df[lookup_col] == name]

    if client_series.empty:
        raise ValueError(
            f"The name '{name}' was not found in the CSV file '{csv_path}'."
        )

    client_data = client_series.iloc[0].to_dict()

    # Combine address fields if they exist
    if "postCode" in client_data and "city" in client_data:
        client_data["city_encr"] = (
            str(client_data.pop("postCode", ""))
            + " "
            + str(client_data.pop("city", ""))
        )

    # Handle date formatting
    for date_col in ["entry_date", "birthday_encr"]:
        if date_col in client_data and isinstance(client_data[date_col], str):
            try:
                client_data[date_col] = datetime.strptime(
                    client_data[date_col], "%d.%m.%Y"
                ).date()
            except ValueError:
                logger.error(
                    f"Could not parse date '{client_data[date_col]}' "
                    f"for column '{date_col}'. "
                    "Please ensure the format is DD.MM.YYYY."
                )
                client_data[date_col] = None

    # check if school was passed and if not use the first from the config
    if school is None:
        school = next(iter(config.school.keys()))
    client_data["school"] = school

    # Filter data to only include valid columns for the Client model
    valid_keys = {c.key for c in sa_inspect(client_cls).column_attrs}
    init_sig = signature(client_cls.__init__)
    valid_init_keys = set(init_sig.parameters.keys())

    final_client_data = {
        k: v for k, v in client_data.items() if k in valid_keys or k in valid_init_keys
    }

    return clients_manager.add_client(**final_client_data)


def _enter_client_tui(clients_manager: ClientsManager) -> int | None:
    student_entry_app_cls = lazy_import("edupsyadmin.tui.editclient").StudentEntryApp
    app = student_entry_app_cls(data=None)
    data = app.run()

    if data:
        return clients_manager.add_client(**data)
    return None


def command_new_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    csv: str | os.PathLike[str] | None,
    school: str | None,
    name: str | None,
    keepfile: bool | None,
    import_config: str | None,
) -> None:
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if csv:
        if name is None:
            raise ValueError("Pass a name to read a client from a csv.")
        _enter_client_csv(clients_manager, csv, school, name, import_config)
        if not keepfile:
            os.remove(csv)
    else:
        _enter_client_tui(clients_manager)


def _tui_get_modified_values(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
) -> dict[str, Any]:
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    student_entry_app_cls = lazy_import("edupsyadmin.tui.editclient").StudentEntryApp
    # retrieve current values
    manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    current_data = manager.get_decrypted_client(client_id=client_id)

    # display a form with current values filled in
    app = student_entry_app_cls(client_id, data=current_data)
    modified_data = app.run()

    return modified_data or {}


def command_set_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: list[int],
    key_value_pairs: list[str] | None,
) -> None:
    """
    Set the value for a key given one or multiple client_ids
    """
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )

    if not key_value_pairs:
        assert len(client_id) == 1, (
            "When no key-value pairs are passed, "
            "only one client_id can be edited at a time"
        )
        key_value_pairs_dict = _tui_get_modified_values(
            database_url=database_url,
            app_uid=app_uid,
            app_username=app_username,
            salt_path=salt_path,
            client_id=client_id[0],
        )
    else:
        key_value_pairs_dict = dict(pair.split("=", 1) for pair in key_value_pairs)

    clients_manager.edit_client(client_ids=client_id, new_data=key_value_pairs_dict)


def command_delete_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
) -> None:
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    clients_manager.delete_client(client_id)


def command_get_clients(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    nta_nos: bool,
    school: list[str] | None,
    client_id: int | None,
    out: str | os.PathLike[str] | None,
    show_notes: bool = False,
    tui: bool = False,
) -> None:
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    display_client_details = lazy_import(
        "edupsyadmin.api.display_client_details"
    ).display_client_details
    pd = lazy_import("pandas")
    clients_overview_cls = lazy_import(
        "edupsyadmin.tui.clientsoverview"
    ).ClientsOverview

    clients_manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if client_id:
        client_data = clients_manager.get_decrypted_client(client_id)
        display_client_details(client_data)
        df = pd.DataFrame([client_data]).T
    else:
        df = clients_manager.get_clients_overview(
            nta_nos=nta_nos,
            schools=school,
            show_notes=show_notes,
        )

        if tui:
            # Convert DataFrame to list-of-lists for the TUI
            list_of_tuples = [df.columns.to_list(), *df.values.tolist()]
            app = clients_overview_cls(list_of_tuples)
            app.run()
            return  # Exit after TUI session

        original_df = df.sort_values(["school", "last_name_encr"])
        df = original_df.set_index("client_id")

        if not tui:
            with pd.option_context(
                "display.max_columns",
                None,
                "display.width",
                None,
                "display.max_colwidth",
                None,
                "display.expand_frame_repr",
                False,
            ):
                print(df)

    if out:
        df.to_csv(out)


def _normalize_path(path_str: str) -> str:
    path = pathlib.Path(os.path.expanduser(path_str))
    return str(path.resolve())


def command_create_documentation(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: list[int],
    form_set: str | None,
    form_paths: list[str] | None,
    inject_data: dict[str, Any] | None,
) -> None:
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    add_convenience_data = lazy_import(
        "edupsyadmin.api.add_convenience_data"
    ).add_convenience_data
    fill_form = lazy_import("edupsyadmin.api.fill_form").fill_form

    clients_manager = clients_manager_cls(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if form_paths is None:
        form_paths = []
    if form_set:
        try:
            form_paths.extend(config.form_set[form_set])
        except KeyError:
            raise KeyError(
                f"Es ist in der Konfigurationsdatei kein Form Set mit dem"
                f"Namen {form_set} angelegt."
            )
    elif not form_paths:
        raise ValueError("At least one of 'form_set' or 'form_paths' must be non-empty")
    form_paths_normalized: list[str | os.PathLike[str]] = [
        _normalize_path(p) for p in form_paths
    ]
    logger.debug(f"Trying to fill the files: {form_paths_normalized}")
    for cid in client_id:
        client_dict = clients_manager.get_decrypted_client(cid)
        client_dict_w_convdat = add_convenience_data(client_dict)
        if inject_data:
            inject_dict = dict(pair.split("=", 1) for pair in inject_data)
            client_dict_w_convdat = client_dict_w_convdat | inject_dict
        fill_form(client_dict_w_convdat, form_paths_normalized)


def command_mk_report(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
    test_date: str,
    test_type: str,
    version: str | None = None,
) -> None:
    mk_report = lazy_import("edupsyadmin.api.lgvt").mk_report
    mk_report(
        app_username,
        app_uid,
        database_url,
        salt_path,
        client_id,
        test_date,
        test_type,
        version=version,
    )


def command_flatten_pdfs(
    form_paths: list[str | os.PathLike[str]], library: str
) -> None:
    flatten_pdfs = lazy_import("edupsyadmin.api.flatten_pdf").flatten_pdfs
    flatten_pdfs(form_paths, library)


def command_taetigkeitsbericht(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    wstd_psy: float,
    out_basename: str | os.PathLike[str],
    wstd_total: float,
    name: str,
) -> None:
    taetigkeitsbericht = lazy_import(
        "edupsyadmin.api.taetigkeitsbericht_from_db"
    ).taetigkeitsbericht
    taetigkeitsbericht(
        app_username=app_username,
        app_uid=app_uid,
        database_url=database_url,
        salt_path=salt_path,
        wstd_psy=wstd_psy,
        out_basename=out_basename,
        wstd_total=wstd_total,
        name=name,
    )


def _args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command line arguments.

    :param argv: argument list to parse
    """
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)
    # append allows multiple instances of the same object
    # args.config_path will therefore be a list!
    parser.add_argument("-c", "--config_path", help=argparse.SUPPRESS)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"edupsyadmin {__version__}",
        help="print version and exit",
    )
    # default must be None, otherwise the value from the config for logging
    # level will be overwritten
    parser.add_argument(
        "-w", "--warn", default=None, help="logger warning level [WARN]"
    )
    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(title="subcommands")

    # TODO: Remove common arguments? I read them all from config.
    common = ArgumentParser(add_help=False)  # common subcommand arguments
    common.add_argument("--app_username", help=argparse.SUPPRESS)
    common.add_argument("--app_uid", default=APP_UID, help=argparse.SUPPRESS)
    common.add_argument(
        "--database_url", default=DEFAULT_DB_URL, help=argparse.SUPPRESS
    )
    common.add_argument(
        "--salt_path", default=DEFAULT_SALT_PATH, help=argparse.SUPPRESS
    )

    _info(subparsers, common)
    _edit_config(subparsers, common)
    _new_client(subparsers, common)
    _set_client(subparsers, common)
    _create_documentation(subparsers, common)
    _get_clients(subparsers, common)
    _flatten_pdfs(subparsers, common)
    _mk_report(subparsers, common)
    _taetigkeitsbericht(subparsers, common)
    _delete_client(subparsers, common)

    args = parser.parse_args(argv)
    if not args.command:
        # No sucommand was specified.
        parser.print_help()
        raise SystemExit(1)
    if not args.config_path:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config_path = DEFAULT_CONFIG_PATH
    if not args.salt_path:
        args.salt_path = DEFAULT_SALT_PATH
    return args


def _info(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the info command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Example:
          # Show app version, paths and other info
          edupsyadmin info
    """)
    parser = subparsers.add_parser(
        "info",
        parents=[common],
        description="Show app version and what paths the app uses",
        help="Get useful information for debugging",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_info)


def _edit_config(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the editconfig command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Example:
          # Open the configuration file in a TUI
          edupsyadmin edit_config
    """)
    parser = subparsers.add_parser(
        "edit_config",
        parents=[common],
        description="Edit app configuration",
        help="Edit app configuration",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_edit_config)


def _new_client(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the new_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Examples:
          # Add a new client interactively using the TUI
          edupsyadmin new_client

          # Add a new client from a CSV file
          edupsyadmin new_client --csv "./path/to/sample.csv" --name "ClientName" --school MySchool

          # Add from CSV and keep the file
          edupsyadmin new_client --csv "./path/to/sample.csv" --name "ClientName" --school MySchool --keepfile
    """)
    parser = subparsers.add_parser(
        "new_client",
        parents=[common],
        help="Add a new client",
        description="Add a new client",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_new_client)
    parser.add_argument(
        "--csv",
        help=(
            "An untis tab separated values file. If you pass no csv path, you can "
            "interactively enter the data."
        ),
    )
    parser.add_argument(
        "--name",
        help=(
            "Only relevant if --csv is set. "
            "Name of the client from the name column of the csv."
        ),
    )
    parser.add_argument(
        "--school",
        help=(
            "Only relevant if --csv is set. The label of the school as you "
            "use it in the config file. If no label is passed, the first "
            "school from the config will be used."
        ),
    )
    parser.add_argument(
        "--import-config",
        help=(
            "Only relevant if --csv is set. The name of the csv import configuration "
            "from the config file to use."
        ),
    )
    parser.add_argument(
        "--keepfile",
        action="store_true",
        help=(
            "Only relevant if --csv is set. "
            "Don't delete the csv after adding it to the db."
        ),
    )


def _set_client(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the set_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Examples:
          # Edit a client with ID 2 interactively in the TUI
          edupsyadmin set_client 2

          # Set 'nta_font' to '1' (true) and 'nta_zeitv_vieltext' to '20' for clients with ID 1 and 2
          edupsyadmin set_client 1 2 --key_value_pairs "nta_font=1" "nta_zeitv_vieltext=20"
    """)
    parser = subparsers.add_parser(
        "set_client",
        parents=[common],
        help="Change values for one or more clients",
        description="Change values for one or more clients",
        usage=(
            "edupsyadmin set_client [-h] client_id [client_id ...] "
            "[--key_value_pairs [KEY_VALUE_PAIRS ...]]"
        ),
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_set_client)
    parser.add_argument("client_id", type=int, nargs="+")
    parser.add_argument(
        "--key_value_pairs",
        type=str,
        nargs="*",
        default=None,
        help=(
            "key-value pairs in the format key=value; "
            "if no key-value pairs are passed, the TUI will be used to collect "
            "values."
        ),
    )


def _delete_client(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the delete_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Example:
          # Delete client with ID 1
          edupsyadmin delete_client 1
    """)
    parser = subparsers.add_parser(
        "delete_client",
        parents=[common],
        help="Delete a client in the database",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_delete_client)
    parser.add_argument("client_id", type=int, help="id of the client to delete")


def _get_clients(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the get_clients command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Examples:
          # Show an overview of all clients
          edupsyadmin get_clients

          # Show an overview in an interactive TUI
          edupsyadmin get_clients --tui

          # Show clients from 'TutorialSchule' who have 'NTA' or 'NOS'
          edupsyadmin get_clients --nta_nos --school TutorialSchule

          # Show all details for client with ID 2
          edupsyadmin get_clients --client_id 2
    """)
    parser = subparsers.add_parser(
        "get_clients",
        parents=[common],
        help="Show clients overview or single client",
        description="Show clients overview or single client",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_get_clients)
    parser.add_argument(
        "--nta_nos",
        action="store_true",
        help="show only students with Nachteilsausgleich or Notenschutz",
    )
    parser.add_argument(
        "--school", nargs="*", type=str, default=None, help="filter by school name"
    )
    parser.add_argument("--out", help="path for an output file")
    parser.add_argument(
        "--client_id", type=int, help="id for a single client to display"
    )
    parser.add_argument(
        "--show_notes", action="store_true", help="show the column notes_encr"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="show the results in a tui instead of plain text",
    )


def _create_documentation(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the create_documentation command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Examples:
          # Fill a PDF form for client with ID 1 using a form set named 'MyFormSet'
          edupsyadmin create_documentation 1 --form_set MyFormSet

          # Fill a text file for client with ID 2 using a specific form path
          edupsyadmin create_documentation 2 --form_paths "./path/to/template.txt"

          # Fill a form for client with ID 3, injecting custom data
          edupsyadmin create_documentation 3 --form_paths "./path/to/form.pdf" --inject_data "key1=value1" "key2=value2"
    """)
    parser = subparsers.add_parser(
        "create_documentation",
        parents=[common],
        help="Fill a pdf form or a text file with a liquid template",
        description=(
            "Fill a pdf form or a text file with a liquid template. "
            "Either --form_set or --form_paths must be provided."
        ),
        usage=(
            "edupsyadmin create_documentation [-h] client_id [client_id ...] "
            "[--form_set FORM_SET] [--form_paths FORM_PATH ...] "
            "[--inject_data [INJECT_DATA ...]]"
        ),
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_create_documentation)
    parser.add_argument("client_id", type=int, nargs="+")
    parser.add_argument(
        "--form_set",
        type=str,
        default=None,
        help="name of a set of file paths defined in the config file",
    )
    parser.add_argument("--form_paths", nargs="*", help="form file paths")
    parser.add_argument(
        "--inject_data",
        nargs="*",
        default=None,
        help=(
            "key-value pairs in the format 'key=value'; this "
            "option can be used to override existing key=value pairs "
            "or add new key=value pairs"
        ),
    )


def _mk_report(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the api.lgvt.mk_report command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    parser = subparsers.add_parser("mk_report", parents=[common])
    parser.set_defaults(command=command_mk_report)
    parser.add_argument("client_id", type=int)
    parser.add_argument("test_date", type=str, help="Testdatum (YYYY-mm-dd)")
    parser.add_argument("test_type", type=str, choices=["LGVT", "CFT", "RSTARR"])
    parser.add_argument(
        "--version", type=str, choices=["Rosenkohl", "Toechter", "Laufbursche"]
    )


def _flatten_pdfs(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    default_library = lazy_import("edupsyadmin.api.flatten_pdf").DEFAULT_LIBRARY
    epilog = textwrap.dedent("""\
        Examples:
          # Flatten a single PDF form using the default library
          edupsyadmin flatten_pdfs "./path/to/filled_form.pdf"

          # Flatten multiple PDF forms in the current folder
          edupsyadmin flatten_pdfs *.pdf
    """)
    parser = subparsers.add_parser(
        "flatten_pdfs",
        parents=[common],
        help="Flatten pdf forms (experimental)",
        description="Flatten pdf forms (experimental)",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_flatten_pdfs)
    parser.add_argument(
        "--library", type=str, default=default_library, choices=["pdf2image", "fillpdf"]
    )
    parser.add_argument("form_paths", nargs="+")


def _taetigkeitsbericht(
    subparsers: _SubParsersAction[ArgumentParser], common: ArgumentParser
) -> None:
    """CLI adaptor for the api.taetigkeitsbericht_from_db.taetigkeitsbericht command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    epilog = textwrap.dedent("""\
        Example:
          # Generate a Taetigkeitsbericht PDF with 3 Anrechnugnsstunden
          edupsyadmin taetigkeitsbericht 3

          # Generate a report with custom output name and total hours
          edupsyadmin taetigkeitsbericht 10 --out_basename "MyReport" --wstd_total 28
    """)
    parser = subparsers.add_parser(
        "taetigkeitsbericht",
        parents=[common],
        help="Create a PDF output for the Taetigkeitsbericht (experimental)",
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.set_defaults(command=command_taetigkeitsbericht)
    parser.add_argument(
        "wstd_psy", type=int, help="Anrechnungsstunden in Wochenstunden"
    )
    parser.add_argument(
        "--out_basename",
        type=str,
        default="Taetigkeitsbericht_Out",
        help="base name for the output files; default is 'Taetigkeitsbericht_Out'",
    )
    parser.add_argument(
        "--wstd_total",
        type=int,
        default=23,
        help="total Wochstunden (depends on your school); default is 23",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Schulpsychologie",
        help="name for the header of the pdf report",
    )


# Make the module executable.
if __name__ == "__main__":
    try:
        STATUS = main()
    except Exception:
        logger.critical("shutting down due to fatal error")
        raise  # print stack trace
    raise SystemExit(STATUS)
