from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.types import TypeDecorator

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger
from edupsyadmin.db import Base
from edupsyadmin.utils.academic_year import (
    get_date_destroy_records,
    get_estimated_end_of_academic_year,
)
from edupsyadmin.utils.int_from_str import extract_number
from edupsyadmin.utils.taetigkeitsbericht_check_key import check_keyword

LRST_DIAG = {"lrst", "iLst", "iRst"}
LRST_TEST_BY = {"schpsy", "psychia", "psychoth", "spz", "andere"}


class EncryptedString(TypeDecorator):
    """Stores base-64 ciphertext in a TEXT/VARCHAR column;
    Presents plain str values to the application."""

    impl = String
    cache_ok = True  # SQLAlchemy 2.0 requirement

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encr.encrypt(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
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
    client_id: Mapped[int | None] = mapped_column(
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
        nos_rs: bool | str | int | None = None,
        nos_rs_ausn_faecher: str | None = None,
        nos_les: bool | str | int | None = None,
        nos_other_details: str | None = None,
        nta_zeitv_vieltext: int | str | None = None,
        nta_zeitv_wenigtext: int | str | None = None,
        nta_font: bool | str | int | None = None,
        nta_aufg: bool | str | int | None = None,
        nta_struktur: bool | str | int | None = None,
        nta_arbeitsm: bool | str | int | None = None,
        nta_ersgew: bool | str | int | None = None,
        nta_vorlesen: bool | str | int | None = None,
        nta_other_details: str | None = None,
        nta_nos_notes: str | None = None,
        nta_nos_end_grade: int | str | None = None,
        lrst_diagnosis_encr: str = "",
        lrst_last_test_date_encr: date | str | None = None,
        keyword_taet_encr: str = "",
        lrst_last_test_by_encr: str = "",
        min_sessions: int | str | None = None,
        n_sessions: int | str | None = None,
    ) -> None:
        self.client_id = to_int_or_none(client_id)
        self.first_name_encr = first_name_encr
        self.last_name_encr = last_name_encr
        self.gender_encr = (
            gender_encr
            if gender_encr not in ["w", "d"]
            else ("f" if gender_encr == "w" else "x")
        )
        _birthday_dt = to_date_or_none(birthday_encr)
        self.birthday_encr = _birthday_dt.isoformat() if _birthday_dt else ""
        self.street_encr = street_encr
        self.city_encr = city_encr
        self.parent_encr = parent_encr
        self.telephone1_encr = telephone1_encr
        self.telephone2_encr = telephone2_encr
        self.email_encr = email_encr
        self.notes_encr = notes_encr
        self.school = school
        self.entry_date = to_date_or_none(entry_date)
        self.class_name = class_name
        self.lrst_diagnosis_encr = lrst_diagnosis_encr
        _lrst_date_dt = to_date_or_none(lrst_last_test_date_encr)
        self.lrst_last_test_date_encr = (
            _lrst_date_dt.isoformat() if _lrst_date_dt else ""
        )
        self.lrst_last_test_by_encr = lrst_last_test_by_encr
        self.keyword_taet_encr = keyword_taet_encr

        # Notenschutz
        self.nos_rs = to_bool_or_none(nos_rs) or False
        self.nos_rs_ausn_faecher = nos_rs_ausn_faecher
        self.nos_les = to_bool_or_none(nos_les) or False
        self.nos_other_details = nos_other_details

        # Nachteilsausgleich
        self.nta_zeitv_vieltext = to_int_or_none(nta_zeitv_vieltext)
        self.nta_zeitv_wenigtext = to_int_or_none(nta_zeitv_wenigtext)
        self.nta_font = to_bool_or_none(nta_font) or False
        self.nta_aufg = to_bool_or_none(nta_aufg) or False
        self.nta_struktur = to_bool_or_none(nta_struktur) or False
        self.nta_arbeitsm = to_bool_or_none(nta_arbeitsm) or False
        self.nta_ersgew = to_bool_or_none(nta_ersgew) or False
        self.nta_vorlesen = to_bool_or_none(nta_vorlesen) or False
        self.nta_other_details = nta_other_details
        self.nta_nos_notes = nta_nos_notes
        self.nta_nos_end_grade = to_int_or_none(nta_nos_end_grade)

        self.min_sessions = to_int_or_none(min_sessions) or 45
        self.n_sessions = to_int_or_none(n_sessions) or 1

        # Placeholder for derived fields and timestamps - will be handled by events
        self.class_int = None
        self.estimated_graduation_date = None
        self.document_shredding_date = None
        self.notenschutz = False
        self.nos_rs_ausn = False
        self.nos_other = False
        self.nachteilsausgleich = False
        self.nta_zeitv = False
        self.nta_other = False
        self.nta_nos_end = False

        self.datetime_created = datetime.now()
        self.datetime_lastmodified = datetime.now()

        self._recalculate_derived_fields()  # Call the new method at the end of init

    def _recalculate_derived_fields(self) -> None:
        """
        Calculates and updates all derived fields based on current attribute values.
        This method should be called after initial assignment or any attribute change.
        """
        # Handle gender conversion (if not already done by __init__)

        # Calculate class_int
        if self.class_name:
            try:
                self.class_int = extract_number(self.class_name)
            except TypeError:
                self.class_int = None
        else:
            self.class_int = None

        # Calculate estimated_graduation_date and document_shredding_date
        self.estimated_graduation_date = None
        self.document_shredding_date = None
        if self.class_int is not None and self.school in config.school:
            try:
                self.estimated_graduation_date = get_estimated_end_of_academic_year(
                    grade_current=self.class_int,
                    grade_target=config.school[self.school].end,
                )
                if self.estimated_graduation_date:
                    self.document_shredding_date = get_date_destroy_records(
                        self.estimated_graduation_date
                    )
            except Exception as e:
                logger.warning(
                    f"Could not calculate estimated_graduation_date or "
                    f"document_shredding_date for client {self.client_id}: {e}"
                )

        # Notenschutz flags
        self.nos_rs_ausn = bool(
            self.nos_rs_ausn_faecher and self.nos_rs_ausn_faecher.strip()
        )
        self.nos_other = bool(self.nos_other_details and self.nos_other_details.strip())
        self.notenschutz = self.nos_rs or self.nos_les or self.nos_other

        # Nachteilsausgleich flags
        self.nta_zeitv = bool(
            (self.nta_zeitv_vieltext is not None and self.nta_zeitv_vieltext > 0)
            or (self.nta_zeitv_wenigtext is not None and self.nta_zeitv_wenigtext > 0)
        )
        self.nta_other = bool(self.nta_other_details and self.nta_other_details.strip())
        self.nachteilsausgleich = (
            self.nta_font
            or self.nta_aufg
            or self.nta_struktur
            or self.nta_arbeitsm
            or self.nta_ersgew
            or self.nta_vorlesen
            or self.nta_zeitv
            or self.nta_other
        )
        self.nta_nos_end = bool(self.nta_nos_end_grade is not None)

        self.datetime_lastmodified = datetime.now()

    @validates("lrst_diagnosis_encr")
    def validate_lrst_diagnosis(self, key: str, value: str | None) -> str:
        value = value or ""
        if value and value not in LRST_DIAG:
            raise ValueError(
                f"Invalid value for lrst_diagnosis. "
                f"Allowed values are: {', '.join(LRST_DIAG)}"
            )
        return value

    @validates("keyword_taet_encr")
    def validate_keyword_taet_encr(self, key: str, value: str) -> str:
        return check_keyword(value) or ""

    @validates("nos_rs_ausn_faecher")
    def validate_nos_rs_ausn_faecher(self, key: str, value: str | None) -> str | None:
        return value

    @validates("nos_rs", "nos_les")
    def validate_nos_bool(self, key: str, value: bool | str | int) -> bool:
        return to_bool_or_none(value) or False

    @validates("nos_other_details")
    def validate_nos_other_details(self, key: str, value: str) -> str:
        return value

    @validates("min_sessions", "n_sessions")
    def validate_sessions(self, key: str, value: str | int) -> int:
        val = to_int_or_none(value)
        if val is None:
            raise ValueError(f"Feld '{key}' muss eine ganze Zahl sein.")
        return val

    @validates("nta_zeitv_vieltext", "nta_zeitv_wenigtext")
    def validate_nta_zeitv_percentage(
        self, key: str, value: str | int | None
    ) -> int | None:
        return to_int_or_none(value)

    @validates(
        "nta_font",
        "nta_aufg",
        "nta_arbeitsm",
        "nta_ersgew",
        "nta_vorlesen",
        "nta_struktur",
    )
    def validate_nta_bool(self, key: str, value: bool | str | int) -> bool:
        return to_bool_or_none(value) or False

    @validates("nta_other_details")
    def validate_nta_other_details(self, key: str, value: str) -> str:
        return value

    @validates("nta_nos_end_grade")
    def validate_nta_nos_end_grade(
        self, key: str, value: str | int | None
    ) -> int | None:
        return to_int_or_none(value)

    @validates("lrst_last_test_date_encr")
    def validate_lrst_last_test_date_encr(
        self, key: str, value: str | date | None
    ) -> str:
        dt = to_date_or_none(value)
        return dt.isoformat() if dt else ""

    @validates("lrst_last_test_by_encr")
    def validate_lrst_last_test_by_encr(self, key: str, value: str | None) -> str:
        value = value or ""
        if value and value not in LRST_TEST_BY:
            raise ValueError(
                f"Invalid value for {key}. "
                f"Allowed values are: {', '.join(LRST_TEST_BY)}"
            )
        return value

    @validates("birthday_encr")
    def validate_birthday(self, key: str, value: str | date | None) -> str:
        dt = to_date_or_none(value)
        return dt.isoformat() if dt else ""

    @validates("entry_date")
    def validate_entry_date(self, key: str, value: str | date | None) -> date | None:
        return to_date_or_none(value)

    def __repr__(self) -> str:
        return (
            f"<Client(id='{self.client_id}', "
            f"sc='{self.school}', "
            f"cl='{self.class_name}'"
            f")>"
        )


@event.listens_for(Client, "before_insert")
@event.listens_for(Client, "before_update")
def receive_before_insert_update(_mapper, _connection, target: Client) -> None:
    """
    Listen for before_insert and before_update events to recalculate derived fields.
    """
    target._recalculate_derived_fields()


def to_bool_or_none(value: str | bool | int | None) -> bool | None:
    """
    Convert a string, int, or None to a boolean or None.
    - '1', 1, True -> True
    - '0', 0, False -> False
    - None, '' -> None
    - Any other string raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(
            f"Integer value {value} cannot be converted to a boolean (expected 0 or 1)."
        )
    if isinstance(value, str):
        lower_value = value.lower().strip()
        if lower_value == "true" or lower_value == "1":
            return True
        if lower_value == "false" or lower_value == "0":
            return False
        raise ValueError(
            f"String value '{value}' cannot be converted to a boolean "
            f"(expected 'true', 'false', '0', or '1')."
        )
    raise TypeError(f"Value of type {type(value)} cannot be converted to a boolean.")


def to_int_or_none(value: str | int | None) -> int | None:
    """
    Convert a string or int to an int or None.
    - '123', 123 -> 123
    - None, '' -> None
    - Any other string raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(
                f"String value '{value}' cannot be converted to an integer."
            ) from e
    raise TypeError(f"Value of type {type(value)} cannot be converted to an integer.")


def to_date_or_none(value: str | date | None) -> date | None:
    """
    Convert a string (YYYY-MM-DD) or date object to a date object or None.
    - '2023-01-01', date(2023, 1, 1) -> date(2023, 1, 1)
    - None, '' -> None
    - Invalid string format raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid date format for '{value}'. Use YYYY-MM-DD."
            ) from e
    raise TypeError(f"Value of type {type(value)} cannot be converted to a date.")
