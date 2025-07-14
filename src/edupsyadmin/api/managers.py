import logging  # just for interaction with the sqlalchemy logger
import os
import pathlib
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.api.fill_form import fill_form
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger
from edupsyadmin.db import Base
from edupsyadmin.db.clients import Client
from edupsyadmin.tui.editclient import StudentEntryApp


class ClientNotFoundError(Exception):
    def __init__(self, client_id: int):
        self.client_id = client_id
        super().__init__(f"Client with ID {client_id} not found.")


class ClientsManager:
    def __init__(
        self,
        database_url: str,
        app_uid: str,
        app_username: str,
        salt_path: str | os.PathLike[str],
    ):
        # set up logging for sqlalchemy
        logging.getLogger("sqlalchemy.engine").setLevel(config.core.logging)

        # connect to database
        logger.info(f"trying to connect to database at {database_url}")
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

        # set fernet for encryption
        encr.set_fernet(app_username, salt_path, app_uid)

        # create the table if it doesn't exist
        Base.metadata.create_all(self.engine, tables=[Client.__table__])
        logger.info(f"created connection to database at {database_url}")

    def add_client(self, **client_data: Any) -> int:
        logger.debug("trying to add client")
        with self.Session() as session:
            new_client = Client(encr, **client_data)
            session.add(new_client)
            session.commit()
            logger.info(f"added client: {new_client}")
            return new_client.client_id

    def get_decrypted_client(self, client_id: int) -> dict[str, Any]:
        logger.debug(f"trying to access client (client_id = {client_id})")
        with self.Session() as session:
            client = session.get(Client, client_id)
            if client is None:
                raise ClientNotFoundError(client_id)
            return client.__dict__

    def get_clients_overview(self, nta_nos: bool = True) -> pd.DataFrame:
        logger.debug("trying to query client data")
        stmt = select(Client)
        with self.Session() as session:
            if nta_nos:
                stmt = stmt.where(
                    (Client.notenschutz == 1) or (Client.nachteilsausgleich == 1)
                )
            results = session.scalars(stmt).all()
            results_list_of_dict = [
                {
                    "client_id": entry.client_id,
                    "school": entry.school,
                    "last_name_encr": entry.last_name_encr,
                    "first_name_encr": entry.first_name_encr,
                    "class_name": entry.class_name,
                    "notenschutz": entry.notenschutz,
                    "nachteilsausgleich": entry.nachteilsausgleich,
                    "lrst_diagnosis": entry.lrst_diagnosis,
                    "n_sessions": entry.n_sessions,
                    "keyword_taetigkeitsbericht": entry.keyword_taetigkeitsbericht,
                }
                for entry in results
            ]
            df = pd.DataFrame(results_list_of_dict)
            return df.sort_values(["school", "last_name_encr"])

    def get_data_raw(self) -> pd.DataFrame:
        """
        Get the entire database.
        """
        logger.debug("trying to query the entire database")
        with self.Session() as session:
            query = session.query(Client).statement
            return pd.read_sql_query(query, session.bind)

    def edit_client(self, client_id: int, new_data: dict[str, Any]) -> None:
        # TODO: Warn if key does not exist
        logger.debug(f"editing client (id = {client_id})")
        with self.Session() as session:
            client = session.get(Client, client_id)
            if client:
                for key, value in new_data.items():
                    logger.debug(f"changing value for key: {key}")
                    setattr(client, key, value)
                client.datetime_lastmodified = datetime.now()
                session.commit()
            else:
                logger.error("client could not be found!")

    def delete_client(self, client_id: int) -> None:
        logger.debug("deleting client")
        with self.Session() as session:
            client = session.get(Client, client_id)
            if client:
                session.delete(client)
                session.commit()


def new_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    csv: str | os.PathLike[str] | None = None,
    school: str | None = None,
    name: str | None = None,
    keepfile: bool = False,
) -> None:
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if csv:
        if name is None:
            raise ValueError("Pass a name to read a client from a csv.")
        enter_client_untiscsv(clients_manager, csv, school, name)
        if not keepfile:
            os.remove(csv)
    else:
        enter_client_cli(clients_manager)


def set_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
    key_value_pairs: dict[str, str | bool | None],
) -> None:
    """
    Set the value for a key given a client_id
    """
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )

    if key_value_pairs is None:
        key_value_pairs = _get_modified_values(
            database_url=database_url,
            app_uid=app_uid,
            app_username=app_username,
            salt_path=salt_path,
            client_id=client_id,
        )

    clients_manager.edit_client(client_id, key_value_pairs)


def get_clients(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    nta_nos: bool = False,
    client_id: int | None = None,
    out: str | None = None,
) -> None:
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if client_id:
        original_df = pd.DataFrame([clients_manager.get_decrypted_client(client_id)]).T
        df = original_df[~(original_df.index == "_sa_instance_state")]
    else:
        original_df = clients_manager.get_clients_overview(nta_nos=nta_nos)
        df = original_df.set_index("client_id")
    if out:
        df.to_csv(out)
    else:
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


def get_data_raw(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
) -> pd.DataFrame:
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    return clients_manager.get_data_raw()


def enter_client_untiscsv(
    clients_manager: ClientsManager,
    csv: str | os.PathLike[str],
    school: str | None,
    name: str,
) -> int:
    """
    Read client from a webuntis csv

    :param clients_manager: a ClientsManager instance used to add the client to the db
    :param csv: path to a tab separated webuntis export file
    :param school: short name of the school as set in the config file
    :param name: name of the client as specified in the "name" column of the csv
    return: client_id
    """
    untis_df = pd.read_csv(csv, sep="\t", encoding="utf-8")
    client_series = untis_df[untis_df["name"] == name]

    # check if id is known
    if "client_id" in client_series.columns:
        client_id = client_series["client_id"].item()
    else:
        client_id = None

    # check if school was passed and if not use the first from the config
    if school is None:
        school = next(iter(config.school.keys()))

    return clients_manager.add_client(
        school=school,
        gender_encr=client_series["gender"].item(),
        entry_date=datetime.strptime(
            client_series["entryDate"].item(), "%d.%m.%Y"
        ).date(),
        class_name=client_series["klasse.name"].item(),
        first_name_encr=client_series["foreName"].item(),
        last_name_encr=client_series["longName"].item(),
        birthday_encr=datetime.strptime(
            client_series["birthDate"].item(), "%d.%m.%Y"
        ).date(),
        street_encr=client_series["address.street"].item(),
        city_encr=str(client_series["address.postCode"].item())
        + " "
        + client_series["address.city"].item(),
        telephone1_encr=str(
            client_series["address.mobile"].item()
            or client_series["address.phone"].item()
        ),
        email_encr=client_series["address.email"].item(),
        client_id=client_id,
    )


# TODO: rename to enter_client_tui
def enter_client_cli(clients_manager: ClientsManager) -> int:
    app = StudentEntryApp(data=None)
    app.run()

    data = app.get_data()

    return clients_manager.add_client(**data)


def _get_modified_values(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike,
    client_id: int,
) -> dict:
    # retrieve current values
    manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    current_data = manager.get_decrypted_client(client_id=client_id)

    # display a form with current values filled in
    app = StudentEntryApp(client_id, data=current_data)
    app.run()

    return app.get_data()


# TODO: move to tests (not used here)
def _find_changed_values(original: dict, updates: dict) -> dict:
    changed_values = {}
    for key, new_value in updates.items():
        if key not in original:
            raise KeyError(
                f"Key '{key}' found in updates but not in original dictionary."
            )
        if original[key] != new_value:
            changed_values[key] = new_value
    return changed_values


def create_documentation(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
    form_set: str | None = None,
    form_paths: list[str] = [],
) -> None:
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    if form_set:
        form_paths.extend(config.form_set[form_set])
    elif not form_paths:
        raise ValueError("At least one of 'form_set' or 'form_paths' must be non-empty")
    form_paths_normalized = [_normalize_path(p) for p in form_paths]
    logger.debug(f"Trying to fill the files: {form_paths_normalized}")
    client_dict = clients_manager.get_decrypted_client(client_id)
    client_dict_with_convenience_data = add_convenience_data(client_dict)
    fill_form(client_dict_with_convenience_data, form_paths_normalized)


def _normalize_path(path_str: str) -> str:
    path = pathlib.Path(os.path.expanduser(path_str))
    return str(path.resolve())


def delete_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike[str],
    client_id: int,
) -> None:
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    clients_manager.delete_client(client_id)
