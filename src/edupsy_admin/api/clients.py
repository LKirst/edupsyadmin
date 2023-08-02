from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..core.logger import logger
from ..core.encrypt import Encryption
from ..core.config import config


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
    telephone_encr = Column(String)
    email_encr = Column(String)
    notes_encr = Column(String)

    # Unencrypted variables
    client_id = Column(Integer, primary_key=True)
    school = Column(String)
    gender = Column(String)
    date_of_graduation = Column(
        String
    )  # this variable allows me to calculate the class
    keywordtaetigkeitsbericht = Column(String)
    datetime_created = Column(DateTime)
    datetime_lastmodified = Column(DateTime)

    def __init__(
        self,
        app_username:str,
        app_configpath:str,
        app_uid:str,
        school:str,
        gender:str,
        date_of_graduation:str,
        first_name_encr:str,
        last_name_encr:str,
        birthday_encr:str = "",
        street_encr:str = "",
        city_encr:str = "",
        parent_encr:str = "",
        telephone_encr:str = "",
        email_encr:str = "",
        notes_encr:str = "",
        keyword_taetigkeitsbericht:str = "",
        datetime_created:str=None,
        datetime_lastmodified:str=None,
    ):
        encr.set_fernet(app_username, app_configpath, app_uid)
        self.first_name_encr = encr.encrypt(first_name_encr)
        self.last_name_encr = encr.encrypt(last_name_encr)
        self.birthday_encr = encr.encrypt(birthday_encr)
        self.street_encr = encr.encrypt(street_encr)
        self.city_encr = encr.encrypt(city_encr)
        self.parent_encr = encr.encrypt(parent_encr)
        self.telephone_encr = encr.encrypt(telephone_encr)
        self.email_encr = encr.encrypt(email_encr)
        self.notes_encr = encr.encrypt(notes_encr)
        self.school = school
        self.gender = gender
        self.date_of_graduation = date_of_graduation
        self.keyword_taetigkeitsbericht = keyword_taetigkeitsbericht
        self.datetime_created = datetime_created or datetime.now()
        self.datetime_lastmodified = datetime_lastmodified or datetime.now()

    def __repr__(self):
        representation = (
                f"<Client(id='{self.client_id}', "
                f"school='{self.school}')>")
        return representation


class ClientsManager:
    def __init__(self, database_url: str, app_uid: str, app_username: str, app_configpath: str):
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.app_uid = app_uid
        self.app_username = app_username
        self.app_configpath = app_configpath

        Base.metadata.create_all(self.engine) # create the table if it doesn't exist
        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, client_data):
        logger.debug("trying to add client")
        session = self.Session()
        new_client = Client(
            **client_data,
            app_uid=self.app_uid,
            app_username=self.app_username,
            app_configpath=self.app_configpath,
        )
        session.add(new_client)
        session.commit()
        logger.debug(f"added client: {new_client}")
        client_id = new_client.client_id
        session.close()
        return client_id

    def get_decrypted_client(self, client_id: int):
        logger.debug(f"trying to access client (id = {client_id})")
        session = self.Session()
        client = session.query(Client).filter_by(client_id=client_id).first()
        client_vars = vars(client)
        for attributekey in client_vars.keys():
            if attributekey.endswith("_encr"):
                client_vars[attributekey]=encr.decrypt(client_vars[attributekey])
        return client

    def edit_client(self, client_id: int, new_data):
        logger.debug(f"editing client (id = {client_id})")
        session = self.Session()
        client = session.query(Client).filter_by(client_id=client_id).first()
        if client:
            for key, value in new_data.items():
                if key.endswith('_encr'):
                    setattr(client, key, encr.encrypt(value))
                else:
                    setattr(client, key, value)
            client.datetime_lastmodified = datetime.now()
            session.commit()
        session.close()

    def delete_client(self, client_id: int):
        logger.debug("deleting client")
        session = self.Session()
        client = session.query(Client).filter_by(client_id=client_id).first()
        if client:
            session.delete(client)
            session.commit()
        session.close()

    def close(self):
        self.engine.dispose()


def collect_client_data_cli():
    first_name_encr = input("First Name: ")
    last_name_encr = input("Last Name: ")
    school = input("School: ")
    date_of_graduation = input("Date of graduation (YYYY-MM-DD): ")
    gender = input("Gender (f/m): ")

    birthday_encr = input("Birthday (YYYY-MM-DD): ")
    street_encr = input("Street: ")
    city_encr = input("City: ")
    parent_encr = input("Parent: ")
    telephone_encr = input("Telephone: ")
    email_encr = input("Email: ")
    notes_encr = input("Notes: ")

    return Client(
        first_name_encr=first_name_encr,
        last_name_encr=last_name_encr,
        birthday_encr=birthday_encr,
        street_encr=street_encr,
        city_encr=city_encr,
        parent_encr=parent_encr,
        telephone_encr=telephone_encr,
        email_encr=email_encr,
        notes_encr=notes_encr,
        school=school,
        gender=gender,
        date_of_graduation=date_of_graduation,
    )
