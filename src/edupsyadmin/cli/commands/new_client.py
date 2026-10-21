import os
import textwrap
from argparse import ArgumentParser, Namespace
from datetime import datetime
from inspect import signature
from typing import TYPE_CHECKING

from sqlalchemy import inspect as sa_inspect

from edupsyadmin.cli.utils import lazy_import
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.db import clients
from edupsyadmin.utils.path_utils import normalize_path

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
        --names "ClientName" --school MySchool

      # Add from CSV and keep the file
      edupsyadmin new-client --csv "./path/to/sample.csv" \
        --names "Client1Name" "Client2Name" --school MySchool --keep-file
""",
)


def _enter_client_csv(
    clients_manager: ClientsManager,
    csv_path: str | os.PathLike[str],
    school: str | None,
    name: list[str],
    import_config_name: str | None = None,
) -> int:
    """
    Read client(s) from a csv file and add them to the database.

    :param clients_manager: a ClientsManager instance used to add the client to the db
    :param csv_path: path to a csv file
    :param school: short name of the school as set in the config file
    :param name: name(s) of the client(s) as specified in the "name" column of the csv
    :param import_config_name: name of the csv import configuration from the config
    :raises ValueError: if the import config is unknown, the lookup column is
        missing, a name is not found, or no school/name is available
    :return: client_id of the last client that was created
    """
    pd = lazy_import("pandas")

    client_cls = clients.Client

    if import_config_name:
        try:
            import_conf = config.csv_import[import_config_name]
        except KeyError:
            raise ValueError(
                f"Unknown csv import config '{import_config_name}'. "
                f"Available configs: {sorted(config.csv_import)}",
            ) from None
        separator = import_conf.separator
        column_mapping = import_conf.column_mapping
    else:
        # Default to original hardcoded behavior
        separator = "\t"
        column_mapping = {
            "gender": "gender_encr",
            "entryDate": "entry_date_encr",
            "klasse.name": "class_name_encr",
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

    # keep_default_na: Empty cells become "" (the defaults used by
    # Client.__init__), and values like "NA" or "Null" stay strings.
    raw_df = pd.read_csv(
        csv_path, sep=separator, encoding="utf-8", dtype=str, keep_default_na=False
    )

    # Log a warning if there are unknown keys
    unmatched = sorted(set(column_mapping) - set(raw_df.columns))
    if unmatched:
        logger.warning(
            "Column mapping (import config: %s) refers to columns that are not in "
            "'%s' and will be ignored: %s. Columns found in the file: %s",
            import_config_name or "<default>",
            csv_path,
            unmatched,
            list(raw_df.columns),
        )

    df = raw_df.rename(columns=column_mapping)

    # Telephone numbers must be strings so that they can be encrypted.
    for phone_col in ("telephone1_encr", "telephone2_encr"):
        if phone_col in df.columns:
            df[phone_col] = df[phone_col].fillna("").astype(str)
        else:
            logger.warning(
                "No column was mapped to '%s'; it will be left empty.", phone_col
            )

    # The 'name' column is used for lookup; it may itself have been renamed.
    lookup_col = "name" if "name" in df.columns else column_mapping.get("name", "name")
    if lookup_col not in df.columns:
        raise ValueError(
            f"Lookup column '{lookup_col}' not found in '{csv_path}' after applying "
            f"the column mapping. Available columns: {list(df.columns)}",
        )

    # Use the first school from the config if none was passed.
    if school is None:
        try:
            school = next(iter(config.school))
        except StopIteration:
            raise ValueError(
                "No school passed and none defined in the config."
            ) from None

    # Only keep keys that the Client model accepts.
    valid_keys = {c.key for c in sa_inspect(client_cls).column_attrs}
    valid_init_keys = set(signature(client_cls.__init__).parameters)
    allowed_keys = valid_keys | valid_init_keys
    # postCode/city are merged into city_encr below, so they are valid targets.
    unknown_targets = sorted(
        target
        for target in set(column_mapping.values())
        if target not in allowed_keys and target not in {"postCode", "city"}
    )
    if unknown_targets:
        logger.debug(
            "Column mapping targets are not Client fields and will be dropped: %s",
            unknown_targets,
        )

    client_id: int | None = None
    for this_name in name:
        client_series = df[df[lookup_col] == this_name]

        if client_series.empty:
            raise ValueError(
                f"The name '{this_name}' was not found in column '{lookup_col}' "
                f"of the CSV file '{csv_path}'.",
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
        for date_col in ("entry_date_encr", "birthday_encr"):
            if date_col in client_data and isinstance(client_data[date_col], str):
                try:
                    client_data[date_col] = datetime.strptime(
                        client_data[date_col],
                        "%d.%m.%Y",
                    ).date()
                except ValueError:
                    logger.error(
                        "Could not parse date '%s' for column '%s'. "
                        "Please ensure the format is DD.MM.YYYY.",
                        client_data[date_col],
                        date_col,
                    )
                    client_data[date_col] = None

        client_data["school"] = school

        final_client_data = {k: v for k, v in client_data.items() if k in allowed_keys}
        client_id = clients_manager.add_client(**final_client_data)

    if client_id is None:
        raise ValueError("No client names were given; nothing was added.")
    return client_id


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
        "--names",
        nargs="*",
        help=(
            "Only relevant if --csv is set. "
            "Name(s) of the client from the name column of the csv."
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
        "--keep-file",
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
        if not args.names:
            raise ValueError("Pass a name to read a client from a csv.")

        csv_path = normalize_path(args.csv)
        _enter_client_csv(
            clients_manager,
            csv_path,
            args.school,
            args.names,
            args.import_config,
        )
        if not args.keep_file:
            csv_path.unlink()
    else:
        edit_client_app_cls = lazy_import(
            "edupsyadmin.tui.edit_client_app",
        ).EditClientApp
        edit_client_app_cls(clients_manager=clients_manager).run()
