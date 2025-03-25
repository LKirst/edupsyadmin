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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates

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
    first_name_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselter Vorname des Klienten"
    )
    last_name_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselter Nachname des Klienten"
    )
    gender_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsseltes Geschlecht des Klienten"
    )
    birthday_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsseltes Geburtsdatum des Klienten (JJJJ-MM-TT)"
    )
    street_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselte Straßenadresse und Hausnummer des Klienten"
    )
    city_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselter Postleitzahl und Stadt des Klienten"
    )
    parent_encr: Mapped[str] = mapped_column(
        String,
        doc="Verschlüsselter Name des Elternteils/Erziehungsberechtigten des Klienten",
    )
    telephone1_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselte primäre Telefonnummer des Klienten"
    )
    telephone2_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselte sekundäre Telefonnummer des Klienten"
    )
    email_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselte E-Mail-Adresse des Klienten"
    )
    notes_encr: Mapped[str] = mapped_column(
        String, doc="Verschlüsselte Notizen zum Klienten"
    )

    # Unencrypted variables
    client_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, doc="ID des Klienten"
    )
    school: Mapped[str] = mapped_column(
        String,
        doc=(
            "Schule, die der Klient besucht "
            "(Kurzname wie in der Konfiguration festgelegt)"
        ),
    )
    entry_date: Mapped[Optional[str]] = mapped_column(
        String, doc="Eintrittsdatum des Klienten in das System"
    )
    class_name: Mapped[Optional[str]] = mapped_column(
        String, doc="Klassenname des Klienten (einschließlich Buchstaben)"
    )
    class_int: Mapped[Optional[int]] = mapped_column(
        Integer, doc="Numerische Darstellung der Klasse des Klienten"
    )
    estimated_date_of_graduation: Mapped[Optional[date]] = mapped_column(
        DateTime, doc="Voraussichtliches Abschlussdatum des Klienten"
    )
    document_shredding_date: Mapped[Optional[date]] = mapped_column(
        DateTime,
        doc="Datum für die Dokumentenvernichtung im Zusammenhang mit dem Klienten",
    )
    keyword_taetigkeitsbericht: Mapped[Optional[str]] = mapped_column(
        String, doc="Schlüsselwort für die Kategorie des Klienten im Tätigkeitsbericht"
    )
    # I need lrst_diagnosis as a variable separate from keyword_taetigkeitsbericht,
    # because LRSt can be present even if it is not the most important topic
    lrst_diagnosis: Mapped[Optional[str]] = mapped_column(
        String,
        CheckConstraint(
            ("lrst_diagnosis IN ('lrst', 'iLst', 'iRst') OR " "lrst_diagnosis IS NULL")
        ),
        doc="Diagnose im Zusammenhang mit LRSt, iLst oder iRst",
    )
    datetime_created: Mapped[datetime] = mapped_column(
        DateTime, doc="Zeitstempel, wann der Klienten-Datensatz erstellt wurde"
    )
    datetime_lastmodified: Mapped[datetime] = mapped_column(
        DateTime, doc="Zeitstempel, wann der Klienten-Datensatz zuletzt geändert wurde"
    )

    # Notenschutz
    notenschutz: Mapped[bool] = mapped_column(
        Boolean, default=False, doc="Gibt an, ob der Klient Notenschutz hat"
    )
    # TODO: Add nos_rs
    nos_rs_ausn: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob einige Fächer vom Notenschutz ausgenommen sind",
    )
    nos_rs_ausn_faecher: Mapped[Optional[str]] = mapped_column(
        String,
        doc="Fächer, die vom Notenschutz ausgenommen sind",
    )
    nos_les: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient Notenschutz für das Lesen hat",
    )

    # Nachteilsausgleich
    nachteilsausgleich: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient Nachteilsausgleich (NTA) hat",
    )
    nta_zeitv: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient eine Zeitverlängerung als NTA hat",
    )
    nta_zeitv_vieltext: Mapped[Optional[int]] = mapped_column(
        Integer,
        doc=(
            "Zeitverlängerung in Fächern mit längeren Lesetexten bzw. "
            "Schreibaufgaben (z.B. in den Sprachen) in Prozent der regulär "
            "angesetzten Zeit"
        ),
    )
    nta_zeitv_wenigtext: Mapped[Optional[int]] = mapped_column(
        Integer,
        doc=(
            "Zeitverlängerung in Fächern mit kürzeren Lesetexten bzw. "
            "Schreibaufgaben (z.B. in Mathematik) in Prozent der regulär angesetzen "
            "Zeit"
        ),
    )
    nta_font: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient eine Schriftanpassung als NTA hat",
    )
    nta_aufg: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient eine Aufgabenanpassung als NTA hat",
    )
    nta_struktur: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient eine Strukturanpassung als NTA hat",
    )
    nta_arbeitsm: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient eine Arbeitsmittelanpassung als NTA hat",
    )
    nta_ersgew: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient einen Ersatz schriftlicher durch "
            "mündliche Leistungsnachweise oder eine alternative Gewichtung als NTA hat"
        ),
    )
    nta_vorlesen: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient Vorlesen als NTA hat",
    )
    nta_other: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient andere Formen des NTAs hat",
    )
    nta_other_details: Mapped[Optional[str]] = mapped_column(
        String,
        doc="Details zu anderen Formen des NTAs für den Klienten",
    )
    nta_notes: Mapped[Optional[str]] = mapped_column(String, doc="Notizen zu NTA")

    n_sessions: Mapped[float] = mapped_column(
        Float,
        doc=(
            "Anzahl der mit dem Klienten verbundenen Zeitstunden "
            "(einschließlich Vorbereitung und Auswertung von Tests); eine "
            "Unterrichtsstunde entspricht 0,75 Zeitstunden."
        ),
    )

    def __init__(
        self,
        encr: Encryption,
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
        nos_rs_ausn_faecher: str | None = None,
        nos_les: bool = False,
        nta_zeitv_vieltext: int | None = None,
        nta_zeitv_wenigtext: int | None = None,
        nta_font: bool = False,
        nta_aufg: bool = False,
        nta_struktur: bool = False,
        nta_arbeitsm: bool = False,
        nta_ersgew: bool = False,
        nta_vorlesen: bool = False,
        nta_other_details: str | None = None,
        nta_notes: str | None = None,
        nachteilsausgleich: bool | None = None,
        lrst_diagnosis: str | None = None,
        keyword_taetigkeitsbericht: str | None = "",
        n_sessions: int = 1,
    ) -> None:
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

        # Notenschutz
        self.notenschutz = notenschutz
        self.nos_rs_ausn_faecher = nos_rs_ausn_faecher
        if nos_rs_ausn_faecher:
            self.nos_rs_ausn = True
        else:
            self.nos_rs_ausn = False
        self.nos_les = nos_les

        # Nachteilsausgleich
        self.nta_zeitv_vieltext = nta_zeitv_vieltext
        self.nta_zeitv_wenigtext = nta_zeitv_wenigtext
        if self.nta_zeitv_vieltext or self.nta_zeitv_wenigtext:
            self.nta_zeitv = True
        else:
            self.nta_zeitv = False
        self.nta_font = nta_font
        self.nta_aufg = nta_aufg
        self.nta_struktur = nta_struktur
        self.nta_arbeitsm = nta_arbeitsm
        self.nta_ersgew = nta_ersgew
        self.nta_vorlesen = nta_vorlesen
        self.nta_other_details = nta_other_details
        if self.nta_other_details:
            self.nta_other = True
        else:
            self.nta_other = False
        self.nta_notes = nta_notes
        if nachteilsausgleich is None:
            self.nachteilsausgleich = self._update_nachteilsausgleich()
        else:
            # TODO: remove nachteilsausgleich as an argument in init
            self.nachteilsausgleich = nachteilsausgleich

        self.n_sessions = n_sessions

        self.datetime_created = datetime.now()
        self.datetime_lastmodified = self.datetime_created

    def _update_nachteilsausgleich(self) -> None:
        self.nachteilsausgleich = any(
            (
                self.nta_zeitv,
                self.nta_font,
                self.nta_aufg,
                self.nta_arbeitsm,
                self.nta_ersgew,
                self.nta_vorlesen,
                self.nta_other,
            )
        )

    @validates("nos_rs_ausn_faecher")
    def validate_nos_rs_ausn_faecher(self, key: str, value: str | None) -> str | None:
        self.nos_rs_ausn = (value is not None) and (value > 0)
        return value

    @validates("nta_zeitv_vieltext")
    def validate_nta_zeitv_vieltext(self, key: str, value: int | None) -> int | None:
        self.nta_zeitv = (value is not None) and (value > 0)
        self._update_nachteilsausgleich()
        return value

    @validates("nta_zeitv_wenigtext")
    def validate_nta_zeitv_wenigtext(self, key: str, value: int | None) -> int | None:
        self.nta_zeitv = (value is not None) and (value > 0)
        self._update_nachteilsausgleich()
        return value

    @validates("nta_zeitv")
    def validate_nta_zeitv(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_font")
    def validate_nta_font(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_aufg")
    def validate_nta_aufg(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_arbeitsm")
    def validate_nta_arbeitsm(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_ersgew")
    def validate_nta_ersgew(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_vorlesen")
    def validate_nta_vorlesen(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_other")
    def validate_nta_other(self, key: str, value: bool) -> bool:
        self._update_nachteilsausgleich()
        return value

    @validates("nta_other_details")
    def validate_nta_other_details(self, key: str, value: str) -> str:
        self.nta_other = (value is not None) and value != ""
        self._update_nachteilsausgleich()
        return value

    def __repr__(self):
        representation = (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}'"
            f")>"
        )
        return representation
