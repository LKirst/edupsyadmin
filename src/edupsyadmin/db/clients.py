from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.types import TypeDecorator

from edupsyadmin.core.academic_year import (
    get_date_destroy_records,
    get_estimated_end_of_academic_year,
)
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.int_from_str import extract_number
from edupsyadmin.core.logger import logger
from edupsyadmin.core.taetigkeitsbericht_check_key import check_keyword
from edupsyadmin.db import Base

LRST_DIAG = {"lrst", "iLst", "iRst"}
LRST_TEST_BY = {"schpsy", "psychia", "psychoth", "spz", "andere"}


class EncryptedString(TypeDecorator):
    """Stores base-64 ciphertext in a TEXT/VARCHAR column;
    Presents plain str values to the application."""

    impl = String
    cache_ok = True  # SQLAlchemy 2.0 requirement

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encr.encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return encr.decrypt(value)


class Client(Base):
    __tablename__ = "clients"

    # Variables of StringEncryptedType
    # These variables cannot be optional (i.e. cannot be None) because if
    # they were, the encryption functions would raise an exception.
    first_name_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselter Vorname des Klienten"
    )
    last_name_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselter Nachname des Klienten"
    )
    gender_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsseltes Geschlecht des Klienten (m/f/x)"
    )
    birthday_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsseltes Geburtsdatum des Klienten (JJJJ-MM-TT)"
    )
    street_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselte Straßenadresse und Hausnummer des Klienten"
    )
    city_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselter Postleitzahl und Stadt des Klienten"
    )
    parent_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselter Name des Elternteils/Erziehungsberechtigten des Klienten",
    )
    telephone1_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselte primäre Telefonnummer des Klienten"
    )
    telephone2_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselte sekundäre Telefonnummer des Klienten"
    )
    email_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselte E-Mail-Adresse des Klienten"
    )
    notes_encr: Mapped[str] = mapped_column(
        EncryptedString, doc="Verschlüsselte Notizen zum Klienten"
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
            ":attr:`document_shredding_date` berechnet werden soll."
        ),
    )
    class_int: Mapped[int | None] = mapped_column(
        Integer,
        doc=(
            "Numerische Darstellung der Klasse des Klienten. "
            "Diese Variable wird abgeleitet aus :attr:`class_name`."
        ),
    )
    estimated_graduation_date: Mapped[date | None] = mapped_column(
        Date,
        doc=(
            "Voraussichtliches Abschlussdatum des Klienten. "
            "Diese Variable wird abgeleitet aus der Variable `end` aus "
            "der Konfigurationsdatei und der Variable `class_name`."
        ),
    )
    document_shredding_date: Mapped[date | None] = mapped_column(
        Date,
        doc=(
            "Datum für die Dokumentenvernichtung im Zusammenhang mit dem Klienten."
            "Diese Variable wird abgeleitet aus der Variable "
            ":attr:`estimated_graduation_date`."
        ),
    )
    keyword_taet_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Schlüsselwort für die Kategorie des Klienten im Tätigkeitsbericht",
    )
    # I need lrst_diagnosis as a variable separate from keyword_taet_encr,
    # because LRSt can be present even if it is not the most important topic
    lrst_diagnosis_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc=(
            f"Diagnose im Zusammenhang mit LRSt. Zulässig sind die Werte: "
            f"{', '.join(LRST_DIAG)}"
        ),
    )
    lrst_last_test_date_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc=(
            "Datum (YYYY-MM-DD) der letzten Testung im Zusammenhang "
            "einer Überprüfung von LRSt"
        ),
    )
    lrst_last_test_by_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc=(
            "Fachperson, von der die letzte Überprüfung von LRSt "
            "durchgeführt wurde; kann nur einer der folgenden Werte sein: "
            f"{', '.join(LRST_TEST_BY)}"
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
            ":attr:`nos_rs`, :attr:`nos_les` und :attr:`nos_other_details`."
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
            "Diese Variable wird abgeleitet aus :attr:`nos_other_details`."
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
            "Form des Nachteilsausgleichs z.B. :attr:`nta_zeitv_vieltext` "
            "oder :attr:`nta_other_details`."
        ),
    )
    nta_zeitv: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient eine Zeitverlängerung als NTA hat. "
            "Diese Variable wird abgeleitet aus :attr:`nta_zeitv_vieltext` und "
            ":attr:`nta_zeitv_wenigtext`."
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
            "Diese Variable wird abgeleitet aus :attr:`nta_other_details`."
        ),
    )
    nta_other_details: Mapped[str | None] = mapped_column(
        String,
        doc="Details zu anderen Formen des NTAs für den Klienten",
    )
    nta_nos_notes: Mapped[str | None] = mapped_column(
        String, doc="Notizen zu Notenschutz und Nachteilsausgleich"
    )
    nta_nos_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Nachteilsasugleich und Notenschutzmaßnahmen "
            "zeitlich begrenzt sind (Default: False, auch bei "
            "keinem Nachteilsausgleich oder Notenschutz). "
            "Diese Variable wird abgeleitet aus :attr:`nta_nos_end_grade`."
        ),
    )
    nta_nos_end_grade: Mapped[int | None] = mapped_column(
        Integer,
        doc=(
            "Jahrgangsstufe bis deren Ende Nachteilsausgleich- und "
            "Notenschutzmaßnahmen zeitlich begrenzt sind"
        ),
    )
    min_sessions: Mapped[int] = mapped_column(
        Integer,
        doc=(
            "Anzahl der mit dem Klienten verbundenen Minuten "
            "(einschließlich Vorbereitung und Auswertung von Tests)"
        ),
    )
    n_sessions: Mapped[int] = mapped_column(
        Integer,
        doc=("Anzahl der mit dem Klienten verbundenen Beratungs- und Testsitzungen."),
    )

    def __init__(
        self,
        school: str,
        gender_encr: str,
        class_name: str,
        first_name_encr: str,
        last_name_encr: str,
        birthday_encr: date | str,
        client_id: int | str | None = None,
        street_encr: str = "",
        city_encr: str = "",
        parent_encr: str = "",
        telephone1_encr: str = "",
        telephone2_encr: str = "",
        email_encr: str = "",
        notes_encr: str = "",
        entry_date: date | str | None = None,
        nos_rs: bool | str = False,
        nos_rs_ausn_faecher: str | None = None,
        nos_les: bool | str = False,
        nos_other_details: str | None = None,
        nta_zeitv_vieltext: int | str | None = None,
        nta_zeitv_wenigtext: int | str | None = None,
        nta_font: bool | str = False,
        nta_aufg: bool | str = False,
        nta_struktur: bool | str = False,
        nta_arbeitsm: bool | str = False,
        nta_ersgew: bool | str = False,
        nta_vorlesen: bool | str = False,
        nta_other_details: str | None = None,
        nta_nos_notes: str | None = None,
        nta_nos_end_grade: int | str | None = None,
        lrst_diagnosis_encr: str = "",
        lrst_last_test_date_encr: date | str = "",
        lrst_last_test_by_encr: str = "",
        keyword_taet_encr: str = "",
        min_sessions: int | str = 45,
        n_sessions: int | str = 1,
    ) -> None:
        if client_id and isinstance(client_id, str):
            self.client_id = int(client_id)
        elif client_id:
            self.client_id = client_id

        self.first_name_encr = first_name_encr
        self.last_name_encr = last_name_encr
        self.birthday_encr = birthday_encr
        self.street_encr = street_encr
        self.city_encr = city_encr
        self.parent_encr = parent_encr
        self.telephone1_encr = telephone1_encr
        self.telephone2_encr = telephone2_encr
        self.email_encr = email_encr
        self.notes_encr = notes_encr

        if gender_encr == "w":  # convert German 'w' to 'f'
            gender_encr = "f"
        elif gender_encr == "d":  # convert German 'd' to 'x'
            gender_encr = "x"
        self.gender_encr = gender_encr

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
            # convert grade_target to int to handle configs with a string value
            self.estimated_graduation_date = get_estimated_end_of_academic_year(
                grade_current=self.class_int,
                grade_target=config.school[self.school].end,
            )
            if self.estimated_graduation_date:
                self.document_shredding_date = get_date_destroy_records(
                    self.estimated_graduation_date
                )

        self.lrst_diagnosis_encr = lrst_diagnosis_encr
        self.lrst_last_test_date_encr = lrst_last_test_date_encr
        self.lrst_last_test_by_encr = lrst_last_test_by_encr

        self.keyword_taet_encr = keyword_taet_encr

        # Notenschutz
        self.nos_rs = nos_rs
        self.nos_rs_ausn_faecher = nos_rs_ausn_faecher
        self.nos_les = nos_les
        self.nos_other_details = nos_other_details

        # Nachteilsausgleich
        self.nta_zeitv_vieltext = nta_zeitv_vieltext
        self.nta_zeitv_wenigtext = nta_zeitv_wenigtext
        self.nta_font = nta_font
        self.nta_aufg = nta_aufg
        self.nta_struktur = nta_struktur
        self.nta_arbeitsm = nta_arbeitsm
        self.nta_ersgew = nta_ersgew
        self.nta_vorlesen = nta_vorlesen
        self.nta_other_details = nta_other_details
        self.nta_nos_notes = nta_nos_notes
        self.nta_nos_end_grade = nta_nos_end_grade

        self.min_sessions = min_sessions
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

    def _update_notenschutz(self, key: str | None = None, value: bool = False) -> None:
        """
        If this method is used inside a validate method, you can pass key and value
        to account for the change that will take place after the value has been
        validated.
        """
        nos_dict = {
            "nos_les": self.nos_les,
            "nos_rs": self.nos_rs,
            "nos_other": self.nos_other,
        }
        if key:
            nos_dict[key] = value
        self.notenschutz = any(nos_dict.values())

    @validates("lrst_diagnosis_encr")
    def validate_lrst_diagnosis(self, key: str, value: str | None) -> str:
        value = value or ""
        if value and value not in LRST_DIAG:
            raise ValueError(
                f"Invalid value for lrst_diagnosis: '{value}'. "
                f"Allowed values are: {', '.join(LRST_DIAG)}"
            )
        return value

    @validates("keyword_taet_encr")
    def validate_keyword_taet_encr(self, key: str, value: str) -> str:
        return check_keyword(value) or ""

    @validates("nos_rs_ausn_faecher")
    def validate_nos_rs_ausn_faecher(self, key: str, value: str | None) -> str | None:
        # set nos_rs_ausn to True if the value of nos_rs_ausn_faecher is
        # neither None nor an empty string
        self.nos_rs_ausn = (value is not None) and bool(value.strip())
        return value

    @validates("nos_rs", "nos_les")
    def validate_nos_bool(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)
        self._update_notenschutz(key, boolvalue)
        return boolvalue

    @validates("nos_other_details")
    def validate_nos_other_details(self, key: str, value: str) -> str:
        self.nos_other = (value is not None) and value != ""
        self._update_notenschutz()
        return value

    @validates("min_sessions", "n_sessions")
    def validate_sessions(self, key: str, value: str | int) -> int:
        if isinstance(value, str):
            value = int(value)
        if not isinstance(value, int):
            raise ValueError(f"{key} must be an integer")
        return value

    @validates("nta_zeitv_vieltext", "nta_zeitv_wenigtext")
    def validate_nta_zeitv_percentage(
        self, key: str, value: str | int | None
    ) -> int | None:
        if isinstance(value, str):
            value = int(value) if value else None
        self.nta_zeitv = (value is not None) and (value > 0)
        self._update_nachteilsausgleich()
        return value

    @validates(
        "nta_font",
        "nta_aufg",
        "nta_arbeitsm",
        "nta_ersgew",
        "nta_vorlesen",
        "nta_struktur",
    )
    def validate_nta_bool(self, key: str, value: bool | str | int) -> bool:
        boolvalue = str_to_bool(value)
        self._update_nachteilsausgleich(key, boolvalue)
        return boolvalue

    @validates("nta_other_details")
    def validate_nta_other_details(self, key: str, value: str) -> str:
        self.nta_other = (value is not None) and value != ""
        self._update_nachteilsausgleich()
        return value

    @validates("nta_nos_end_grade")
    def validate_nta_nos_end_grade(
        self, key: str, value: str | int | None
    ) -> int | None:
        if isinstance(value, str):
            value = int(value) if value else None
        self.nta_nos_end = value is not None
        return value

    @validates("lrst_last_test_date_encr")
    def validate_lrst_last_test_date_encr(
        self, key: str, value: str | date | None
    ) -> str:
        if not value:
            return ""
        if isinstance(value, date):
            return value.isoformat()
        value = str(value)
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError(
                f"Invalid date format for {key}: '{value}'. Use YYYY-MM-DD."
            )

    @validates("lrst_last_test_by_encr")
    def validate_lrst_last_test_by_encr(self, key: str, value: str | None) -> str:
        value = value or ""
        if value and value not in LRST_TEST_BY:
            raise ValueError(
                f"Invalid value for {key}: '{value}'. "
                f"Allowed values are: {', '.join(LRST_TEST_BY)}"
            )

        if self.lrst_diagnosis_encr and not value:
            raise ValueError(f"{key} is required when lrst_diagnosis_encr is set.")
        return value

    @validates("birthday_encr")
    def validate_birthday(self, key: str, value: str | date) -> str:
        if isinstance(value, date):
            return value.isoformat()
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        return parsed.isoformat()

    @validates("entry_date")
    def validate_unencrypted_dates(
        self, key: str, value: str | date | None
    ) -> date | None:
        if isinstance(value, str):
            return date.fromisoformat(value) if value else None
        return value

    def __repr__(self) -> str:
        return (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}'"
            f")>"
        )


def str_to_bool(value: str | bool | int) -> bool:
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
