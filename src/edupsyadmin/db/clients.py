from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, validates

from edupsyadmin.core.academic_year import (
    get_date_destroy_records,
    get_estimated_end_of_academic_year,
)
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import Encryption
from edupsyadmin.core.int_from_str import extract_number
from edupsyadmin.core.logger import logger
from edupsyadmin.core.taetigkeitsbericht_check_key import check_keyword

from . import Base

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
        String, doc="Verschlüsseltes Geschlecht des Klienten (m/f/x)"
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
    entry_date: Mapped[date | None] = mapped_column(
        Date, doc="Eintrittsdatum des Klienten in das System"
    )
    class_name: Mapped[str | None] = mapped_column(
        String,
        doc=(
            "Klassenname des Klienten (einschließlich Buchstaben). "
            "Muss eine Zahl für die Jahrgangsstufe enthalten, wenn ein "
            "document_shredding_date berechnet werden soll."
        ),
    )
    class_int: Mapped[int | None] = mapped_column(
        Integer,
        doc=(
            "Numerische Darstellung der Klasse des Klienten. "
            "Diese Variable wird abgeleitet aus class_name."
        ),
    )
    estimated_graduation_date: Mapped[date | None] = mapped_column(
        Date, doc="Voraussichtliches Abschlussdatum des Klienten"
    )
    document_shredding_date: Mapped[date | None] = mapped_column(
        Date,
        doc="Datum für die Dokumentenvernichtung im Zusammenhang mit dem Klienten",
    )
    keyword_taetigkeitsbericht: Mapped[str | None] = mapped_column(
        String, doc="Schlüsselwort für die Kategorie des Klienten im Tätigkeitsbericht"
    )
    # I need lrst_diagnosis as a variable separate from keyword_taetigkeitsbericht,
    # because LRSt can be present even if it is not the most important topic
    lrst_diagnosis: Mapped[str | None] = mapped_column(
        String,
        CheckConstraint(
            "lrst_diagnosis IN ('lrst', 'iLst', 'iRst') OR lrst_diagnosis IS NULL"
        ),
        doc="Diagnose im Zusammenhang mit LRSt, iLst oder iRst",
    )
    lrst_last_test_date: Mapped[date | None] = mapped_column(
        Date,
        doc=(
            "Datum (YYYY-MM-DD) der letzten Testung im Zusammenhang "
            "einer Überprüfung von LRSt"
        ),
    )
    lrst_last_test_by: Mapped[str | None] = mapped_column(
        String,
        CheckConstraint(
            "lrst_last_test_by IN "
            "('schpsy', 'psychia', 'psychoth', 'spz') "
            "OR lrst_diagnosis IS NULL"
        ),
        doc=(
            "Fachperson, von der die letzte Überprüfung von LRSt "
            "durchgeführt wurde; kann nur einer der folgenden Werte sein: "
            "schpsy, psychia, psychoth, spz"
        ),
    )
    datetime_created: Mapped[datetime] = mapped_column(
        DateTime, doc="Zeitstempel, wann der Klienten-Datensatz erstellt wurde"
    )
    datetime_lastmodified: Mapped[datetime] = mapped_column(
        DateTime, doc="Zeitstempel, wann der Klienten-Datensatz zuletzt geändert wurde"
    )

    # Notenschutz
    notenschutz: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient Notenschutz hat. "
            "Diese Variable wird abgeleitet aus "
            "nos_rs, nos_les und nos_other_details."
        ),
    )
    nos_rs: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient Notenschutz für die Rechtschreibung hat",
    )
    nos_rs_ausn: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob einige Fächer vom Notenschutz (Rechtschreibung) "
            "ausgenommen sind"
        ),
    )
    nos_rs_ausn_faecher: Mapped[str | None] = mapped_column(
        String,
        doc="Fächer, die vom Notenschutz (Rechtschreibung) ausgenommen sind",
    )
    nos_les: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Gibt an, ob der Klient Notenschutz für das Lesen hat",
    )
    nos_other: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient andere Formen des Notenschutzes hat."
            "Diese Variable wird abgeleitet aus nos_other_details."
        ),
    )
    nos_other_details: Mapped[str | None] = mapped_column(
        String,
        doc="Details zu anderen Formen des Notenschutzes für den Klienten",
    )

    # Nachteilsausgleich
    nachteilsausgleich: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient Nachteilsausgleich (NTA) hat. "
            "Diese Variable wird abgeleitet aus den Variablen zur spezifischen "
            "Form des Nachteilsausgleichs z.B. nta_zeitv_vieltext "
            "oder nta_other_details."
        ),
    )
    nta_zeitv: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient eine Zeitverlängerung als NTA hat. "
            "Diese Variable wird abgeleitet aus nta_zeitv_vieltext und"
            "nta_zeitv_wenigtext."
        ),
    )
    nta_zeitv_vieltext: Mapped[int | None] = mapped_column(
        Integer,
        doc=(
            "Zeitverlängerung in Fächern mit längeren Lesetexten bzw. "
            "Schreibaufgaben (z.B. in den Sprachen) in Prozent der regulär "
            "angesetzten Zeit"
        ),
    )
    nta_zeitv_wenigtext: Mapped[int | None] = mapped_column(
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
        doc=(
            "Gibt an, ob der Klient andere Formen des NTAs hat. "
            "Diese Variable wird abgeleitet aus nta_other_details."
        ),
    )
    nta_other_details: Mapped[str | None] = mapped_column(
        String,
        doc="Details zu anderen Formen des NTAs für den Klienten",
    )
    nta_notes: Mapped[str | None] = mapped_column(String, doc="Notizen zu NTA")
    nta_nos_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Nachteilsasugleich und Notenschutzmaßnahmen "
            "zeitlich begrenzt sind (Default: False, auch bei "
            "keinem Nachteilsausgleich oder Notenschutz). "
            "Diese Variable wird abgeleitet aus nta_nos_end_grade."
        ),
    )
    nta_nos_end_grade: Mapped[int | None] = mapped_column(
        String,
        doc=(
            "Jahrgangsstufe bis deren Ende Nachteilsausgleich- und "
            "Notenschutzmaßnahmen zeitlich begrenzt sind"
        ),
    )

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
        entry_date: date,
        class_name: str,
        first_name: str,
        last_name: str,
        birthday: date,
        client_id: int | None = None,
        street: str = "",
        city: str = "",
        parent: str = "",
        telephone1: str = "",
        telephone2: str = "",
        email: str = "",
        notes: str = "",
        nos_rs: bool = False,
        nos_rs_ausn_faecher: str | None = None,
        nos_les: bool = False,
        nos_other_details: str | None = None,
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
        nta_nos_end_grade: int | None = None,
        lrst_diagnosis: str | None = None,
        lrst_last_test_date: date | None = None,
        lrst_last_test_by: str | None = None,
        keyword_taetigkeitsbericht: str | None = "",
        n_sessions: int = 1,
    ) -> None:
        if client_id:
            self.client_id = client_id

        self.first_name_encr = encr.encrypt(first_name)
        self.last_name_encr = encr.encrypt(last_name)
        self.birthday_encr = encr.encrypt(str(birthday))
        self.street_encr = encr.encrypt(street)
        self.city_encr = encr.encrypt(city)
        self.parent_encr = encr.encrypt(parent)
        self.telephone1_encr = encr.encrypt(telephone1)
        self.telephone2_encr = encr.encrypt(telephone2)
        self.email_encr = encr.encrypt(email)
        self.notes_encr = encr.encrypt(notes)

        if gender == "w":  # convert German 'w' to 'f'
            gender = "f"
        elif gender == "d":  # convert German 'd' to 'x'
            gender = "x"
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
            self.estimated_graduation_date = get_estimated_end_of_academic_year(
                grade_current=self.class_int,
                grade_target=config.school[self.school]["end"],
            )
            self.document_shredding_date = get_date_destroy_records(
                self.estimated_graduation_date
            )

        self.keyword_taetigkeitsbericht = check_keyword(keyword_taetigkeitsbericht)

        self.lrst_diagnosis = lrst_diagnosis
        self.lrst_last_test_date = lrst_last_test_date
        self.lrst_last_test_by = lrst_last_test_by

        # Notenschutz
        self.nos_rs = nos_rs
        self.nos_rs_ausn_faecher = nos_rs_ausn_faecher
        if nos_rs_ausn_faecher:
            self.nos_rs_ausn = True
        else:
            self.nos_rs_ausn = False
        self.nos_les = nos_les
        self.nos_other_details = nos_other_details
        if self.nos_other_details:
            self.nos_other = True
        self.notenschutz = self.nos_rs or self.nos_les or self.nos_other

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
        self.nta_nos_end_grade = nta_nos_end_grade
        self.nta_nos_end = self.nta_nos_end_grade is not None

        self._update_nachteilsausgleich()

        self.n_sessions = n_sessions

        self.datetime_created = datetime.now()
        self.datetime_lastmodified = self.datetime_created

    def _update_nachteilsausgleich(
        self, key: str | None = None, value: bool = False
    ) -> None:
        """
        If this method is used inside a validate method, you can pass key and value
        to account for the change that will take place after the value has been
        validated.
        """
        nta_dict = {
            "nta_zeitv": self.nta_zeitv,
            "nta_font": self.nta_font,
            "nta_aufg": self.nta_aufg,
            "nta_arbeitsm": self.nta_arbeitsm,
            "nta_ersgew": self.nta_ersgew,
            "nta_vorlesen": self.nta_vorlesen,
            "nta_other": self.nta_other,
        }
        if key:
            nta_dict[key] = value
        self.nachteilsausgleich = any(nta_dict.values())

    @validates("keyword_taetigkeitsbericht")
    def validate_keyword_taetigkeitsbericht(self, key: str, value: str) -> str | None:
        return check_keyword(value)

    @validates("nos_rs_ausn_faecher")
    def validate_nos_rs_ausn_faecher(self, key: str, value: str | None) -> str | None:
        # set nos_rs_ausn to True if the value of nos_rs_ausn_faecher is
        # neither None nor an empty string
        self.nos_rs_ausn = (value is not None) and bool(value.strip())
        return value

    @validates("nos_rs")
    def validate_nos_rs(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)
        self.notenschutz = value or self.nos_les or self.nos_other
        return boolvalue

    @validates("nos_les")
    def validate_nos_les(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self.notenschutz = self.nos_rs or value or self.nos_other
        return boolvalue

    @validates("nos_other")
    def validate_nos_other(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self.notenschutz = self.nos_rs or self.nos_les or value
        return boolvalue

    @validates("nos_other_details")
    def validate_nos_other_details(self, key: str, value: str) -> str:
        self.nos_other = (value is not None) and value != ""
        self.notenschutz = self.nos_rs or self.nos_les or self.nos_other
        return value

    @validates("nta_zeitv_vieltext")
    def validate_nta_zeitv_vieltext(
        self, key: str, value: str | int | None
    ) -> int | None:
        if isinstance(value, str):
            value = int(value)
        self.nta_zeitv = (value is not None) and (value > 0)
        self._update_nachteilsausgleich()
        return value

    @validates("nta_zeitv_wenigtext")
    def validate_nta_zeitv_wenigtext(
        self, key: str, value: str | int | None
    ) -> int | None:
        if isinstance(value, str):
            value = int(value)
        self.nta_zeitv = (value is not None) and (value > 0)
        self._update_nachteilsausgleich()
        return value

    @validates("nta_font")
    def validate_nta_font(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_aufg")
    def validate_nta_aufg(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_arbeitsm")
    def validate_nta_arbeitsm(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_ersgew")
    def validate_nta_ersgew(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_vorlesen")
    def validate_nta_vorlesen(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_other")
    def validate_nta_other(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)

        self._update_nachteilsausgleich(key, value)
        return boolvalue

    @validates("nta_other_details")
    def validate_nta_other_details(self, key: str, value: str) -> str:
        self.nta_other = (value is not None) and value != ""
        self._update_nachteilsausgleich()
        return value

    @validates("nta_nos_end_grade")
    def validate_nta_nos_end_grade(self, key: str, value: int | None) -> int | None:
        self.nta_nos_end = value is not None
        return value

    def __repr__(self) -> str:
        return (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}'"
            f")>"
        )


def str_to_bool(value):
    """
    Convert a string of an int or an int to a boolean
    """
    if not isinstance(value, bool):
        try:
            boolvalue = bool(int(value))
        except ValueError:
            raise ValueError(f"The value {value} cannot be converted to a boolean.")
    else:
        boolvalue = value
    return boolvalue
