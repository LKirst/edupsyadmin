from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..core.logger import logger
from ..core.encrypt import get_encryption_key


Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    # Variables of StringEncryptedType
    args_encryption = {
        "type_in": String,
        "key": get_encryption_key,
        "engine": FernetEngine,
        "padding": None,
    }
    first_name = Column(StringEncryptedType(**args_encryption))
    last_name = Column(StringEncryptedType(**args_encryption))
    birthday = Column(StringEncryptedType(**args_encryption))
    street = Column(StringEncryptedType(**args_encryption))
    city = Column(StringEncryptedType(**args_encryption))
    parent = Column(StringEncryptedType(**args_encryption))
    telephone = Column(StringEncryptedType(**args_encryption))
    email = Column(StringEncryptedType(**args_encryption))
    gender = Column(StringEncryptedType(**args_encryption))
    notes = Column(StringEncryptedType(**args_encryption))

    # Unencrypted variables
    client_id = Column(Integer, primary_key=True)
    school = Column(String)
    date_of_graduation = Column(
        String
    )  # this variable allows me to calculate the class
    datetime_created = Column(DateTime)
    datetime_lastmodified = Column(DateTime)

    def __init__(
        self,
        first_name,
        last_name,
        birthday,
        street,
        city,
        parent,
        telephone,
        email,
        gender,
        notes,
        school,
        date_of_graduation,
        datetime_created=None,
        datetime_lastmodified=None,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.birthday = birthday
        self.street = street
        self.city = city
        self.parent = parent
        self.telephone = telephone
        self.email = email
        self.gender = gender
        self.notes = notes
        self.school = school
        self.date_of_graduation = date_of_graduation
        self.datetime_created = datetime_created or datetime.now()
        self.datetime_lastmodified = datetime_lastmodified or datetime.now()


class ClientsManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        logger.debug(f"Created connection to database at {database_url}")

    def add_client(self, client_data):
        logger.debug("trying to add client")
        session = self.Session()
        new_client = Client(
            **client_data,
            datetime_created=datetime.now(),
            datetime_lastmodified=datetime.now(),
        )
        session.add(new_client)
        session.commit()
        session.close()
        logger.debug("added client")

    def edit_client(self, client_id: int, new_data):
        logger.debug("editing client")
        session = self.Session()
        client = session.query(Client).filter_by(client_id=client_id).first()
        if client:
            for key, value in new_data.items():
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

    def get_all_clients(self):
        logger.debug("getting all clients")
        session = self.Session()
        clients = session.query(Client).all()
        session.close()
        return clients

    def close(self):
        self.engine.dispose()


def collect_client_data_cli():
    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    birthday = input("Birthday (YYYY-MM-DD): ")
    street = input("Street: ")
    city = input("City: ")
    parent = input("Parent: ")
    telephone = input("Telephone: ")
    email = input("Email: ")
    gender = input("Gender (f/m): ")
    notes = input("Notes: ")
    school = input("School: ")
    date_of_graduation = input("Date of graduation (YYYY-MM-DD): ")

    return Client(
        first_name=first_name,
        last_name=last_name,
        birthday=birthday,
        street=street,
        city=city,
        parent=parent,
        telephone=telephone,
        email=email,
        gender=gender,
        notes=notes,
        school=school,
        date_of_graduation=date_of_graduation,
    )
