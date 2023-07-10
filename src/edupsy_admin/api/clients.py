from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import EncryptedType
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..core.logger import logger
from ..core.encrypt import get_encryption_key


Base = declarative_base()


class Clients(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    first_name = Column(EncryptedType(String))
    last_name = Column(EncryptedType(String))
    birthday = Column(EncryptedType(String))
    street = Column(EncryptedType(String))
    city = Column(EncryptedType(String))
    parent = Column(EncryptedType(String))
    telephone = Column(EncryptedType(String))
    email = Column(EncryptedType(String))
    gender = Column(EncryptedType(String))
    notes = Column(EncryptedType(String))
    school = Column(String)
    date_of_graduation = Column(String)
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
        secret_key,
        datetime_created=None,
        datetime_lastmodified=None,
    ):
        self.first_name = EncryptedType(String, secret_key)(first_name)
        self.last_name = EncryptedType(String, secret_key)(last_name)
        self.birthday = EncryptedType(String, secret_key)(birthday)
        self.street = EncryptedType(String, secret_key)(street)
        self.city = EncryptedType(String, secret_key)(city)
        self.parent = EncryptedType(String, secret_key)(parent)
        self.telephone = EncryptedType(String, secret_key)(telephone)
        self.email = EncryptedType(String, secret_key)(email)
        self.gender = EncryptedType(String, secret_key)(gender)
        self.notes = EncryptedType(String, secret_key)(notes)
        self.school = school
        self.date_of_graduation = date_of_graduation
        self.datetime_created = datetime_created or datetime.now()
        self.datetime_lastmodified = datetime_lastmodified or datetime.now()


class ClientsManager:
    def __init__(self, database_url, encryption_key):
        self.encryption = Encryption()
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        logger.debug(f"Created connection to database at {database_url}")

    def add_client(self, client_data):
        logger.debug("Adding client")
        session = self.Session()
        new_client = Clients(
            **client_data,
            datetime_created=datetime.now(),
            datetime_lastmodified=datetime.now(),
        )
        session.add(new_client)
        session.commit()
        session.close()

    def edit_client(self, client_id, new_data):
        logger.debug("Editing client")
        session = self.Session()
        client = session.query(Clients).filter_by(id=client_id).first()
        if client:
            for key, value in new_data.items():
                setattr(client, key, value)
            client.datetime_lastmodified = datetime.now()
            session.commit()
        session.close()

    def delete_client(self, client_id):
        logger.debug("Deleting client")
        session = self.Session()
        client = session.query(Clients).filter_by(id=client_id).first()
        if client:
            session.delete(client)
            session.commit()
        session.close()

    def get_all_clients(self):
        logger.debug("Getting all clients")
        session = self.Session()
        clients = session.query(Clients).all()
        decrypted_data = []
        for client in clients:
            decrypted_client_data = {}
            for column in Clients.__table__.columns:
                if isinstance(column.type, EncryptedType):
                    decrypted_client_data[column.name] = self.encryption.decrypt(
                        getattr(client, column.name)
                    )
                else:
                    decrypted_client_data[column.name] = getattr(client, column.name)
            decrypted_data.append(decrypted_client_data)
        session.close()
        return decrypted_data

    def close(self):
        self.engine.dispose()


def collect_client_data_cli(username: str, configpath: str):
    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    birthday = input("Birthday: ")
    street = input("Street: ")
    city = input("City: ")
    parent = input("Parent: ")
    telephone = input("Telephone: ")
    email = input("Email: ")
    gender = input("Gender: ")
    notes = input("Notes: ")
    school = input("School: ")
    date_of_graduation = input("Date of Graduation: ")

    encryption_key = get_encryption_key(username, configpath)

    return Clients(
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
        secret_key=encryption_key,
    )
