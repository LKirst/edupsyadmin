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
    #birthday_encr = Column(String)
    #street_encr = Column(String)
    #city_encr = Column(String)
    #parent_encr = Column(String)
    #telephone_encr = Column(String)
    #email_encr = Column(String)
    #notes_encr = Column(String)

    # Unencrypted variables
    client_id = Column(Integer, primary_key=True)
    school = Column(String)
    gender = Column(String)
    date_of_graduation = Column(
        String
    )  # this variable allows me to calculate the class
    datetime_created = Column(DateTime)
    datetime_lastmodified = Column(DateTime)

    def __init__(
        self,
        first_name_encr:str,
        last_name_encr:str,
        #birthday_encr:str,
        #street_encr:str,
        #city_encr:str,
        #parent_encr:str,
        #telephone_encr:str,
        #email_encr:str,
        #notes_encr:str,
        school:str,
        gender:str,
        date_of_graduation:str,
        username:str,
        configpath:str,
        uid:str,
        datetime_created=None,
        datetime_lastmodified=None,
    ):
        encr.set_fernet(username, configpath, uid)
        self.first_name_encr = encr.encrypt(first_name_encr.encode())
        self.last_name_encr = encr.encrypt(last_name_encr.encode())
        #self.birthday_encr = encr.encrypt(birthday_encr.encode())
        #self.street_encr = encr.encrypt(street_encr.encode())
        #self.city_encr = encr.encrypt(city_encr.encode())
        #self.parent_encr = encr.encrypt(parent_encr.encode())
        #self.telephone_encr = encr.encrypt(telephone_encr.encode())
        #self.email_encr = encr.encrypt(email_encr.encode())
        #self.notes_encr = encr.encrypt(notes_encr.encode())
        self.school = school
        self.gender = gender
        self.date_of_graduation = date_of_graduation
        self.datetime_created = datetime_created or datetime.now()
        self.datetime_lastmodified = datetime_lastmodified or datetime.now()

    def __repr__(self):
        representation = (
                f"<Client(name='{encr.decrypt(self.first_name_encr)}' "
                f"'{encr.decrypt(self.last_name_encr)}', "
                f"id='{self.client_id}', "
                f"school='{self.school}')>")
        return representation


class ClientsManager:
    def __init__(self, database_url: str, uid: str, username: str, configpath: str):
        self.engine = create_engine(database_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.uid = uid
        self.username = username
        self.configpath = configpath

        Base.metadata.create_all(self.engine) # create the table if it doesn't exist
        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, client_data):
        logger.debug("trying to add client")
        session = self.Session()
        new_client = Client(
            **client_data,
            uid=self.uid,
            username=self.username,
            configpath=self.configpath,
            datetime_created=datetime.now(),
            datetime_lastmodified=datetime.now(),
        )
        session.add(new_client)
        session.commit()
        client_id = new_client.client_id
        logger.debug(f"added client (id = {client_id})")
        session.close()
        return client_id

    def get_decrypted_client(self, client_id: int):
        logger.debug("trying to access client")
        session = self.Session()
        client = session.query(Client).filter_by(client_id=client_id).first()
        client_vars = vars(client)
        for attributekey in client_vars.keys():
            if attributekey.endswith('_encr'):
                client_vars[attributekey]=encr.decrypt(client_vars[attributekey])
        return client

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

    def close(self):
        self.engine.dispose()


def collect_client_data_cli():
    first_name_encr = input("First Name: ")
    last_name_encr = input("Last Name: ")
    #birthday_encr = input("Birthday (YYYY-MM-DD): ")
    #street_encr = input("Street: ")
    #city_encr = input("City: ")
    #parent_encr = input("Parent: ")
    #telephone_encr = input("Telephone: ")
    #email_encr = input("Email: ")
    #notes_encr = input("Notes: ")
    gender = input("Gender (f/m): ")
    school = input("School: ")
    date_of_graduation = input("Date of graduation (YYYY-MM-DD): ")

    return Client(
        first_name_encr=first_name_encr,
        last_name_encr=last_name_encr,
        #birthday_encr=birthday_encr,
        #street_encr=street_encr,
        #city_encr=city_encr,
        #parent_encr=parent_encr,
        #telephone_encr=telephone_encr,
        #email_encr=email_encr,
        #notes_encr=notes_encr,
        school=school,
        gender=gender,
        date_of_graduation=date_of_graduation,
    )
