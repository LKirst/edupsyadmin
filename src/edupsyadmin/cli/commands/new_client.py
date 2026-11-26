import os
import textwrap
from argparse import ArgumentParser, Namespace
from inspect import signature

from sqlalchemy import inspect as sa_inspect
lazy import pandas as pd

from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.db import clients
from edupsyadmin.utils.path_utils import normalize_path
lazy from edupsyadmin.api.managers import ClientsManager
lazy from edupsyadmin.tui.edit_client_app import EditClientApp

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
_CITY_COLUMNS = frozenset({"postCode", "city"})


def _get_import_config(import_config_name: str | None) -> tuple[str, dict[str, str]]:
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
    return separator, column_mapping


def _allowed_client_keys() -> set[str]:
    client_cls = clients.Client
    valid_keys = {c.key for c in sa_inspect(client_cls).column_attrs}
    valid_init_keys = set(signature(client_cls.__init__).parameters)
    return valid_keys | valid_init_keys


def _read_clients_csv(
    csv_path: str | os.PathLike[str],
    import_config_name: str | None,
) -> tuple[str, pd.DataFrame]:
    """Read a client csv and apply the column mapping."""
    separator, column_mapping = _get_import_config(import_config_name)

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

    # The 'name' column is used for lookup; it may itself have been renamed.
    lookup_col = "name" if "name" in df.columns else column_mapping.get("name", "name")
    if lookup_col not in df.columns:
        raise ValueError(
            f"Lookup column '{lookup_col}' not found in '{csv_path}' after applying "
            f"the column mapping. Available columns: {list(df.columns)}",
        )

    allowed_keys = _allowed_client_keys()

    # postCode/city (_CITY_COLUMNS) are merged into city_encr later, so
    # they are valid targets.
    unknown_targets = sorted(
        target
        for target in set(column_mapping.values())
        if target not in allowed_keys and target not in _CITY_COLUMNS
    )
    if unknown_targets:
        logger.debug(
            "Column mapping targets are not Client fields and will be dropped: %s",
            unknown_targets,
        )

    keep = allowed_keys | _CITY_COLUMNS | {lookup_col}
    return lookup_col, df[[col for col in df.columns if col in keep]]


def _resolve_school(school: str | None) -> str:
    """Return the specified school or the first one defined in the config."""
    if school is not None:
        return school
    try:
        return next(iter(config.school))
    except StopIteration:
        raise ValueError("No school passed and none defined in the config.") from None


def _enter_client_csv(
    clients_manager: ClientsManager,
    csv_path: str | os.PathLike[str],
    school: str | None,
    name: list[str],
    import_config_name: str | None = None,
) -> list[int]:
    """
    Read client(s) from a csv file and add them to the database.

    :param clients_manager: a ClientsManager instance used to add the client to the db
    :param csv_path: path to a csv file
    :param school: short name of the school as set in the config file
    :param name: name(s) of the client(s) as specified in the "name" column of the csv
    :param import_config_name: name of the csv import configuration from the config
    :raises ValueError: if the import config is unknown, the lookup column is
        missing, a name is not found, or no school/name is available
    :return: list of client_ids that were created
    """
    if not name:
        raise ValueError("No client names were given; nothing was added.")

    lookup_col, df = _read_clients_csv(csv_path, import_config_name)

    # Telephone numbers must be strings so that they can be encrypted.
    for phone_col in ("telephone1_encr", "telephone2_encr"):
        if phone_col in df.columns:
            df[phone_col] = df[phone_col].fillna("").astype(str)
        else:
            logger.warning(
                "No column was mapped to '%s'; it will be left empty.", phone_col
            )

    school_name = _resolve_school(school)

    # Resolve every name first so a typo in the last name does not leave
    # the earlier clients half-imported.
    available = set(df[lookup_col])
    missing = [this_name for this_name in name if this_name not in available]
    if missing:
        raise ValueError(
            f"The name(s) {missing} were not found in column '{lookup_col}' "
            f"of the CSV file '{csv_path}'.",
        )

    # drop_duplicates keeps the first match per name;
    # .loc[name] returns the rows in the order the names were given.
    selected = (
        df.drop_duplicates(subset=lookup_col)
        .set_index(lookup_col, drop=False)
        .loc[name]
    )
    records = _preprocess_client_csv_data(selected, school_name).to_dict(
        orient="records"
    )
    return [
        clients_manager.add_client(**{str(k): v for k, v in record.items()})
        for record in records
    ]


def _preprocess_client_csv_data(df: pd.DataFrame, school: str) -> pd.DataFrame:
    """Prepare the selected csv rows for ``ClientsManager.add_client``.

    Merges ``postCode`` and ``city`` into ``city_encr``, parses dates
    (``DD.MM.YYYY``, unparsable values become None), sets the school and drops
    all columns that are not ``Client`` fields.

    :param df: the selected rows of the csv dataframe
    :param school: short name of the school
    :return: dataframe whose columns are valid ``add_client`` keyword arguments
    """
    df = df.copy()

    # Combine address fields if they exist
    if {"postCode", "city"} <= set(df.columns):
        df["city_encr"] = df.pop("postCode") + " " + df.pop("city")

    # Handle date formatting
    for date_col in ("entry_date_encr", "birthday_encr"):
        if date_col not in df.columns:
            continue
        parsed = pd.to_datetime(df[date_col], format="%d.%m.%Y", errors="coerce")
        failed = parsed.isna()
        for bad_value in df.loc[failed, date_col]:
            if bad_value:
                logger.error(
                    "Could not parse date '%s' for column '%s'. "
                    "Please ensure the format is DD.MM.YYYY.",
                    bad_value,
                    date_col,
                )
        df[date_col] = parsed.dt.date.where(~failed, None)

    df["school"] = school

    allowed_keys = _allowed_client_keys()
    return df[[col for col in df.columns if col in allowed_keys]]


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
    clients_manager = ClientsManager(
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
        EditClientApp(clients_manager=clients_manager).run()
