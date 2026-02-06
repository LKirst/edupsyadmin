import os
import textwrap
from argparse import ArgumentParser, Namespace
from datetime import datetime
from inspect import signature
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import inspect as sa_inspect

from edupsyadmin.cli.utils import lazy_import
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager

COMMAND_DESCRIPTION = "Add a new client"
COMMAND_HELP = "Add a new client"
COMMAND_EPILOG = textwrap.dedent(
    """
    Examples:
      # Add a new client interactively using the TUI
      edupsyadmin new-client

      # Add a new client from a CSV file
      edupsyadmin new-client --csv "./path/to/sample.csv" \
        --name "ClientName" --school MySchool

      # Add from CSV and keep the file
      edupsyadmin new-client --csv "./path/to/sample.csv" \
        --name "ClientName" --school MySchool --keepfile
"""
)


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


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the new-client command."""
    parser.set_defaults(command=execute)
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


def execute(args: Namespace) -> None:
    """Execute the new-client command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    if args.csv:
        if args.name is None:
            raise ValueError("Pass a name to read a client from a csv.")
        _enter_client_csv(
            clients_manager, args.csv, args.school, args.name, args.import_config
        )
        if not args.keepfile:
            Path(args.csv).unlink()
    else:
        edit_client_app_cls = lazy_import(
            "edupsyadmin.tui.edit_client_app"
        ).EditClientApp
        edit_client_app_cls(clients_manager=clients_manager).run()
