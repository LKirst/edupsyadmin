from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    CheckConstraint,
    CHAR,
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

from ..core.logger import logger
from ..core.config import config
from .taetigkeitsbericht_check_key import check_keyword
from .int_from_str import extract_number
from .academic_year import get_estimated_end_of_academic_year, get_date_destroy_records


Base = declarative_base()


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
    gender = Column(CHAR(1), CheckConstraint("gender IN ('f', 'm')"))
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
    nta_notes = Column(String)
    n_sessions = Column(Float)

    def __init__(
        self,
        encr,
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
                grade_current=self.class_int,
                grade_target=config.school[self.school]["end"],
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
