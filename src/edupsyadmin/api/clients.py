from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..core.config import config
from ..core.encrypt import Encryption
from ..core.logger import logger
from .academic_year import get_date_destroy_records, get_estimated_end_of_academic_year
from .int_from_str import extract_number
from .taetigkeitsbericht_check_key import check_keyword


class Base(DeclarativeBase):
    pass


encr = Encryption()


class Client(Base):
    __tablename__ = "clients"

    # Variables of StringEncryptedType
    # These variables cannot be optional (i.e. cannot be None) because if
    # they were, the encryption functions would raise an exception.
    first_name_encr: Mapped[str] = mapped_column(String)
    last_name_encr: Mapped[str] = mapped_column(String)
    gender_encr: Mapped[str] = mapped_column(String)
    birthday_encr: Mapped[str] = mapped_column(String)
    street_encr: Mapped[str] = mapped_column(String)
    city_encr: Mapped[str] = mapped_column(String)
    parent_encr: Mapped[str] = mapped_column(String)
    telephone1_encr: Mapped[str] = mapped_column(String)
    telephone2_encr: Mapped[str] = mapped_column(String)
    email_encr: Mapped[str] = mapped_column(String)
    notes_encr: Mapped[str] = mapped_column(String)

    # Unencrypted variables
    client_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school: Mapped[str] = mapped_column(String)
    entry_date: Mapped[Optional[str]] = mapped_column(String)
    class_name: Mapped[Optional[str]] = mapped_column(String)
    class_int: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_date_of_graduation: Mapped[Optional[date]] = mapped_column(DateTime)
    document_shredding_date: Mapped[Optional[date]] = mapped_column(DateTime)
    keyword_taetigkeitsbericht: Mapped[Optional[str]] = mapped_column(String)
    # I need lrst_diagnosis as a variable separate from keyword_taetigkeitsbericht,
    # because LRSt can be present even if it is not the most important topic
    lrst_diagnosis: Mapped[Optional[str]] = mapped_column(
        String,
        CheckConstraint(
            ("lrst_diagnosis IN ('lrst', 'iLst', 'iRst') OR " "lrst_diagnosis IS NULL")
        ),
    )
    datetime_created: Mapped[datetime] = mapped_column(DateTime)
    datetime_lastmodified: Mapped[datetime] = mapped_column(DateTime)
    notenschutz: Mapped[Optional[bool]] = mapped_column(Boolean)
    nachteilsausgleich: Mapped[Optional[bool]] = mapped_column(Boolean)
    nta_sprachen: Mapped[Optional[int]] = mapped_column(Integer)
    nta_mathephys: Mapped[Optional[int]] = mapped_column(Integer)
    nta_notes: Mapped[Optional[str]] = mapped_column(String)
    n_sessions: Mapped[Optional[float]] = mapped_column(Float)

    def __init__(
        self,
        encr,
        school: str,
        gender: str,
        entry_date: str,
        class_name: str,
        first_name: str,
        last_name: str,
        client_id: int | None = None,
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
        keyword_taetigkeitsbericht: str | None = "",
        lrst_diagnosis: str | None = None,
        nta_sprachen: int | None = None,
        nta_mathephys: int | None = None,
        nta_notes: int | None = None,
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

        if gender == "w":  # convert German 'w' to 'f'
            gender = "f"
        self.gender_encr = encr.encrypt(gender)

        self.school = school
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
        self.lrst_diagnosis = lrst_diagnosis
        self.notenschutz = notenschutz
        self.nachteilsausgleich = nachteilsausgleich
        self.nta_sprachen = nta_sprachen
        self.nta_mathephys = nta_mathephys
        self.nta_notes = nta_notes
        self.n_sessions = n_sessions

        self.datetime_created = datetime.now()
        self.datetime_lastmodified = self.datetime_created

    def __repr__(self):
        representation = (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}'"
            f")>"
        )
        return representation
