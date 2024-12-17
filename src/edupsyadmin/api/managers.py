import os
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from ..core.config import config
from ..core.encrypt import Encryption
from ..core.logger import logger
from .add_convenience_data import add_convenience_data
from .clients import Client
from .fill_form import fill_form
from .taetigkeitsbericht_check_key import check_keyword


class Base(DeclarativeBase):
    pass


encr = Encryption()


class ClientNotFound(Exception):
    def __init__(self, client_id: int):
        self.client_id = client_id
        super().__init__(f"Client with ID {client_id} not found.")


class ClientsManager:
    def __init__(
        self, database_url: str, app_uid: str, app_username: str, config_path: str
    ):
        logger.info(f"trying to connect to database at {database_url}")
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        encr.set_fernet(app_username, config_path, app_uid)

        # create the table if it doesn't exist
        Base.metadata.create_all(self.engine, tables=[Client.__table__])
        logger.info(f"created connection to database at {database_url}")

    def add_client(self, **client_data):
        logger.debug("trying to add client")
        with self.Session() as session:
            new_client = Client(encr, **client_data)
            session.add(new_client)
            session.commit()
            logger.debug(f"added client: {new_client}")
            client_id = new_client.client_id
            return client_id

    def get_decrypted_client(self, client_id: int) -> dict:
        logger.debug(f"trying to access client (id = {client_id})")
        with self.Session() as session:
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client is None:
                raise ClientNotFound(client_id)
            client_dict = client.__dict__
            decr_vars = {}
            for attributekey in client_dict.keys():
                if attributekey.endswith("_encr"):
                    attributekey_decr = attributekey.removesuffix("_encr")
                    try:
                        decr_vars[attributekey_decr] = encr.decrypt(
                            client_dict[attributekey]
                        )
                    except:
                        logger.critical(
                            (
                                f"attribute: {attributekey}; "
                                f"value: {client_dict[attributekey]}"
                            )
                        )
                        raise
            client_dict.update(decr_vars)
            return client_dict

    def get_na_ns(self, school: str) -> pd.DataFrame:
        logger.debug("trying to query nachteilsausgleich and notenschutz")
        with self.Session() as session:
            # TODO: this doesn't filter by school
            results = (
                session.query(Client)
                .filter(
                    (
                        ((Client.notenschutz == 1) or (Client.nachteilsausgleich == 1))
                        and (Client.school == school)
                    )
                )
                .all()
            )
            results_list_of_dict = [
                {
                    "id": entry.client_id,
                    "class_name": entry.class_name,
                    "first_name": encr.decrypt(entry.first_name_encr),
                    "last_name": encr.decrypt(entry.last_name_encr),
                    "notenschutz": entry.notenschutz,
                    "nachteilsausgleich": entry.nachteilsausgleich,
                    "nta_sprachen": entry.nta_sprachen,
                    "nta_mathephys": entry.nta_mathephys,
                }
                for entry in results
            ]
            df = pd.DataFrame.from_dict(results_list_of_dict)
            return df.sort_values("last_name")

    def get_data_raw(self):
        """
        Get the data without decrypting encrypted data.
        """
        logger.debug("trying to query the entire database")
        with self.Session() as session:
            query = session.query(Client).statement
            df = pd.read_sql_query(query, session.bind)
        return df

    def edit_client(self, client_id: int, new_data: dict):
        # TODO: Warn if key does not exist
        # TODO: If key does not exist, check if key + _encr exists and use it
        logger.debug(f"editing client (id = {client_id})")
        with self.Session() as session:
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client:
                for key, value in new_data.items():
                    logger.debug(f"changing value for key: {key}")
                    if key.endswith("_encr"):
                        setattr(client, key, encr.encrypt(value))
                    else:
                        setattr(client, key, value)
                client.datetime_lastmodified = datetime.now()
                session.commit()
            else:
                logger.error("client could not be found!")

    def delete_client(self, client_id: int):
        logger.debug("deleting client")
        with self.Session() as session:
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client:
                session.delete(client)
                session.commit()


def new_client(
    app_username,
    app_uid,
    database_url,
    config_path,
    csv=None,
    school=None,
    keepfile=False,
):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    if csv:
        enter_client_untiscsv(clients_manager, csv, school)
        if not keepfile:
            os.remove(csv)
    else:
        enter_client_cli(clients_manager)


def set_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    config_path: str,
    client_id: int,
    key_value_pairs: list[str],
):
    """
    Set the value for a key given a client_id
    """
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    pairs_list = [pair.split("=") for pair in key_value_pairs]
    for key, value in pairs_list:
        if key in ["notenschutz", "nachteilsausgleich"]:
            value = bool(int(value))
        if key == "keyword_taetigkeitsbericht":
            value = check_keyword(value)
        new_data = {key: value}
        clients_manager.edit_client(client_id, new_data)


def get_na_ns(
    app_username: str,
    app_uid: str,
    database_url: str,
    config_path: str,
    school: str,
    out: str | None = None,
):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    df = clients_manager.get_na_ns(school)
    if out:
        df.to_csv(out, index=False)
    else:
        print(df)


def get_data_raw(app_username: str, app_uid: str, database_url: str, config_path: str):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    df = clients_manager.get_data_raw()
    return df


def enter_client_untiscsv(clients_manager, csv: str | os.PathLike, school: str | None):
    """Read client from a webuntis csv"""
    untis_df = pd.read_csv(csv)

    # check if id is known
    if "client_id" in untis_df.columns:
        client_id = untis_df["client_id"].item()
    else:
        client_id = None

    # check if school was passed and if not use the default from the config
    if school is None:
        school = config.school.default

    client_id_n = clients_manager.add_client(
        school=school,
        gender=untis_df["gender"].item(),
        entry_date=datetime.strptime(untis_df["entryDate"].item(), "%d.%m.%Y").strftime(
            "%Y-%m-%d"
        ),
        class_name=untis_df["klasse.name"].item(),
        first_name=untis_df["foreName"].item(),
        last_name=untis_df["longName"].item(),
        birthday=datetime.strptime(untis_df["birthDate"].item(), "%d.%m.%Y").strftime(
            "%Y-%m-%d"
        ),
        street=untis_df["address.street"].item(),
        city=str(untis_df["address.postCode"].item())
        + " "
        + untis_df["address.city"].item(),
        telephone1=str(
            untis_df["address.mobile"].item() or untis_df["address.phone"].item()
        ),
        email=untis_df["address.email"].item(),
        client_id=client_id,
    )
    return client_id_n


def enter_client_cli(clients_manager):
    """Create an unencrypted csvfile interactively"""

    # check if id is known
    client_id = input("client_id (press ENTER if you don't know): ")
    if client_id:
        client_id = int(client_id)
    else:
        client_id = None

    client_id_n = clients_manager.add_client(
        school=input("School: "),
        gender=input("Gender (f/m): "),
        entry_date=input("Entry date (YYYY-MM-DD): "),
        class_name=input("Class name: "),
        first_name=input("First Name: "),
        last_name=input("Last Name: "),
        birthday=input("Birthday (YYYY-MM-DD): "),
        street=input("Street and house number: "),
        city=input("City (postcode + name): "),
        telephone1=input("Telephone: "),
        email=input("Email: "),
        client_id=client_id,
    )
    return client_id_n


def create_documentation(
    app_username: str,
    app_uid: str,
    database_url: str,
    config_path: str,
    client_id: int,
    form_set: str = None,
    form_paths: list = [],
):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    if form_set:
        form_paths.extend(config.form_set[form_set])
    elif not form_paths:
        raise ValueError("At least one of 'form_set' or 'form_paths' must be non-empty")
    form_paths_normalized = [
        os.path.normpath(os.path.expanduser(p)) for p in form_paths
    ]
    logger.debug(f"Trying to fill the files: {form_paths_normalized}")
    client_dict = clients_manager.get_decrypted_client(client_id)
    client_dict_with_convenience_data = add_convenience_data(client_dict)
    fill_form(client_dict_with_convenience_data, form_paths_normalized)
