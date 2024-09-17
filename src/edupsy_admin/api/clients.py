import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Real
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import pandas as pd

from ..core.logger import logger
from ..core.encrypt import Encryption
from ..core.config import config
from .fill_form import fill_form
from .taetigkeitsbericht_check_key import check_keyword
from .int_from_str import extract_number
from .academic_year import get_estimated_end_of_academic_year, get_date_destroy_records


Base = declarative_base()
encr = Encryption()


class Client(Base):
    __tablename__ = "clients"

    # Variables of StringEncryptedType
    first_name_encr = Column(String)
    last_name_encr = Column(String)
    birthday_encr = Column(String)
    street_encr = Column(String)
    city_encr = Column(String)
    parent_encr = Column(String)
    telephone1_encr = Column(String)
    telephone2_encr = Column(String)
    email_encr = Column(String)
    notes_encr = Column(String)

    # Unencrypted variables
    client_id = Column(Integer, primary_key=True)
    school = Column(String)
    gender = Column(String)
    entry_date = Column(String)
    class_name = Column(String)
    class_int = Column(Integer)
    estimated_date_of_graduation = Column(DateTime)
    document_shredding_date = Column(DateTime)
    keyword_taetigkeitsbericht = Column(String)
    datetime_created = Column(DateTime)
    datetime_lastmodified = Column(DateTime)
    notenschutz = Column(Boolean)
    nachteilsausgleich = Column(Boolean)
    nta_sprachen = Column(Integer)
    nta_mathephys = Column(Integer)
    n_sessions = Column(Real)

    def __init__(
        self,
        school: str,
        gender: str,
        entry_date: str,
        class_name: str,
        first_name: str,
        last_name: str,
        client_id: id = None,
        birthday: str = "",
        street: str = "",
        city: str = "",
        parent: str = "",
        telephone1: str = "",
        telephone2: str = "",
        email: str = "",
        notes: str = "",
        notenschutz: bool = False,
        nachteilsausgleich: bool = False,
        keyword_taetigkeitsbericht: str = "",
        n_sessions: int = 1,
    ):
        if client_id:
            self.client_id = client_id

        self.first_name_encr = encr.encrypt(first_name)
        self.last_name_encr = encr.encrypt(last_name)
        self.birthday_encr = encr.encrypt(birthday)
        self.street_encr = encr.encrypt(street)
        self.city_encr = encr.encrypt(city)
        self.parent_encr = encr.encrypt(parent)
        self.telephone1_encr = encr.encrypt(telephone1)
        self.telephone2_encr = encr.encrypt(telephone2)
        self.email_encr = encr.encrypt(email)
        self.notes_encr = encr.encrypt(notes)

        self.school = school
        self.gender = gender
        self.entry_date = entry_date
        self.class_name = class_name

        try:
            self.class_int = extract_number(class_name)
        except TypeError:
            self.class_int = None

        if self.class_int is None:
            logger.error("could not extract integer from class name")
        else:
            self.estimated_date_of_graduation = get_estimated_end_of_academic_year(
                grade_current=self.class_int, grade_target=config[self.school]["end"]
            )
            self.document_shredding_date = get_date_destroy_records(
                self.estimated_date_of_graduation
            )

        self.keyword_taetigkeitsbericht = check_keyword(keyword_taetigkeitsbericht)
        self.notenschutz = notenschutz
        self.Nachteilsausgleich = nachteilsausgleich
        self.n_sessions = n_sessions

        self.datetime_created = datetime.now()
        self.datetime_lastmodified = self.datetime_created

    def __repr__(self):
        representation = (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}', "
            f"ge='{self.gender}'"
            f")>"
        )
        return representation


class ClientsManager:
    def __init__(
        self, database_url: str, app_uid: str, app_username: str, config_path: str
    ):
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        encr.set_fernet(app_username, config_path, app_uid)

        Base.metadata.create_all(self.engine)  # create the table if it doesn't exist
        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, **client_data):
        logger.debug("trying to add client")
        with self.Session() as session:
            new_client = Client(**client_data)
            session.add(new_client)
            session.commit()
            logger.debug(f"added client: {new_client}")
            client_id = new_client.client_id
            return client_id

    def get_decrypted_client(self, client_id: int) -> dict:
        logger.debug(f"trying to access client (id = {client_id})")
        with self.Session() as session:
            client_dict = (
                session.query(Client).filter_by(client_id=client_id).first().__dict__
            )
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
                            f"attribute: {attributekey}; value: {client_dict[attributekey]}"
                        )
                        raise
            client_dict.update(decr_vars)
            return client_dict

    def get_na_ns(self, school: str) -> pd.DataFrame:
        logger.debug(f"trying to query nachteilsausgleich and notenschutz")
        with self.Session() as session:
            results = (
                session.query(Client)
                .filter(
                    (
                        (
                            (Client.notenschutz == True)
                            or (Client.nachteilsausgleich == True)
                        )
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
        logger.debug(f"trying to query the entire database")
        with self.Session() as session:
            query = session.query(Client).statement
            df = pd.read_sql_query(query, session.bind)
        return df

    def edit_client(self, client_id: int, new_data: dict):
        logger.debug(f"editing client (id = {client_id})")
        with self.Session() as session:
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client:
                for key, value in new_data.items():
                    if key.endswith("_encr"):
                        setattr(client, key, encr.encrypt(value))
                    else:
                        setattr(client, key, value)
                client.datetime_lastmodified = datetime.now()
                session.commit()

    def delete_client(self, client_id: int):
        logger.debug("deleting client")
        with self.Session() as session:
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client:
                session.delete(client)
                session.commit()


def new_client(
    app_username, app_uid, database_url, config_path, csv=None, keepfile=False
):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    if csv:
        enter_client_untiscsv(clients_manager, csv)
        if not keepfile:
            os.remove(csv)
    else:
        enter_client_cli(clients_manager)


def set_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    config_path: str,
    client_id: str,
    key: str,
    value: str = None,
):
    """
    Set the value for a key given a client_id; if no client_id is passed,
    print the current value.
    """
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    if value:
        if key in ["notenschutz", "nachteilsausgleich"]:
            value = bool(int(value))
        if key == "keyword_taetigkeitsbericht":
            value = check_keyword(value)
        new_data = {key: value}
        clients_manager.edit_client(client_id, new_data)
    else:
        client_dict = clients_manager.get_decrypted_client(client_id)
        print("")
        print(client_dict[key])
        print("")


def get_na_ns(
    app_username: str,
    app_uid: str,
    database_url: str,
    config_path: str,
    school: str,
    out: str = None,
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


def enter_client_untiscsv(clients_manager, csv):
    """Read client from csv"""
    untis_df = pd.read_csv(csv)

    # check if id is known
    if "client_id" in untis_df.columns:
        client_id = untis_df["client_id"].item()
    else:
        client_id = None

    client_id_n = clients_manager.add_client(
        school="FOSBOS",
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
        street=input("Street: "),
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
    form_paths: list,
):
    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        config_path=config_path,
    )
    client_dict = clients_manager.get_decrypted_client(client_id)
    fill_form(client_dict, form_paths)
