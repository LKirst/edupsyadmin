from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, validates

from edupsyadmin.core.config import config
from edupsyadmin.core.enums import Gender, LrstDiagnosis, LrstTesterType
from edupsyadmin.core.logger import logger
from edupsyadmin.db import Base
from edupsyadmin.db.column_types import EncryptedDate, EncryptedInteger, EncryptedString
from edupsyadmin.db.converters import to_bool_or_none, to_date_or_none, to_int_or_none
from edupsyadmin.utils.academic_year import (
    get_date_destroy_records,
    get_estimated_end_of_academic_year,
)
from edupsyadmin.utils.int_from_str import extract_number
from edupsyadmin.utils.taetigkeitsbericht_check_key import check_keyword

LRST_DIAG: frozenset[LrstDiagnosis] = frozenset(LrstDiagnosis)
LRST_TEST_BY: frozenset[LrstTesterType] = frozenset(LrstTesterType)


class SystemMetadata(Base):
    """Stores unencrypted system-wide settings like the encryption salt."""

    __tablename__ = "system_metadata"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String)


class Client(Base):
    __tablename__ = "clients"

    # Variables of StringEncryptedType
    # These variables cannot be optional (i.e. cannot be None) because if
    # they were, the encryption functions would raise an exception.
    first_name_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselter Vorname des Klienten",
    )
    last_name_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselter Nachname des Klienten",
    )
    gender_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsseltes Geschlecht des Klienten (m/f/x)",
    )
    birthday_encr: Mapped[date] = mapped_column(
        EncryptedDate,
        doc="Verschlüsseltes Geburtsdatum des Klienten (JJJJ-MM-TT)",
    )
    street_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselte Straßenadresse und Hausnummer des Klienten",
    )
    city_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselter Postleitzahl und Stadt des Klienten",
    )
    parent_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselter Name des Elternteils/Erziehungsberechtigten des Klienten",
    )
    telephone1_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselte primäre Telefonnummer des Klienten",
    )
    telephone2_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselte sekundäre Telefonnummer des Klienten",
    )
    email_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselte E-Mail-Adresse des Klienten",
    )
    notes_encr: Mapped[str] = mapped_column(
        EncryptedString,
        doc="Verschlüsselte Notizen zum Klienten",
    )
    class_name_encr: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
        doc=(
            "Verschlüsselter Klassenname des Klienten (einschließlich Buchstaben). "
            "Muss eine Zahl für die Jahrgangsstufe enthalten, wenn ein "
            ":attr:`document_shredding_date_encr` berechnet werden soll."
        ),
    )
    class_int_encr: Mapped[int | None] = mapped_column(
        EncryptedInteger,
        nullable=False,
        doc=(
            "Verschlüsselte numerische Darstellung der Klasse des Klienten. "
            "Diese Variable wird abgeleitet aus :attr:`class_name_encr`."
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

    # Unencrypted variables
    client_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        doc="ID des Klienten",
    )
    school: Mapped[str] = mapped_column(
        String,
        doc=(
            "Schule, die der Klient besucht "
            "(Kurzname wie in der Konfiguration festgelegt)"
        ),
    )
    entry_date_encr: Mapped[date | None] = mapped_column(
        EncryptedDate,
        nullable=False,
        doc="Verschlüsseltes Eintrittsdatum des Klienten in das System",
    )
    estimated_graduation_date_encr: Mapped[date | None] = mapped_column(
        EncryptedDate,
        nullable=False,
        doc=(
            "Voraussichtliches Abschlussdatum des Klienten. "
            "Diese Variable wird abgeleitet aus der Variable `end` aus "
            "der Konfigurationsdatei und der Variable `class_name_encr`."
        ),
    )
    document_shredding_date_encr: Mapped[date | None] = mapped_column(
        EncryptedDate,
        nullable=False,
        doc=(
            "Datum für die Dokumentenvernichtung im Zusammenhang mit dem Klienten."
            "Diese Variable wird abgeleitet aus der Variable "
            ":attr:`estimated_graduation_date_encr`."
        ),
    )
    datetime_created: Mapped[datetime] = mapped_column(
        DateTime,
        doc="Zeitstempel, wann der Klienten-Datensatz erstellt wurde",
    )
    datetime_lastmodified: Mapped[datetime] = mapped_column(
        DateTime,
        doc="Zeitstempel, wann der Klienten-Datensatz zuletzt geändert wurde",
    )

    # Notenschutz
    notenschutz: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient Notenschutz hat. "
            "Diese Variable wird abgeleitet aus "
            ":attr:`nos_rs`, :attr:`nos_les` und :attr:`nos_other_details_encr`."
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
    nos_rs_ausn_faecher_encr: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
        doc=(
            "Verschlüsselte Fächer, die vom Notenschutz (Rechtschreibung) "
            "ausgenommen sind"
        ),
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
            "Diese Variable wird abgeleitet aus :attr:`nos_other_details_encr`."
        ),
    )
    nos_other_details_encr: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
        doc=(
            "Verschlüsselte Details zu anderen Formen des Notenschutzes "
            "für den Klienten"
        ),
    )

    # Nachteilsausgleich
    nachteilsausgleich: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc=(
            "Gibt an, ob der Klient Nachteilsausgleich (NTA) hat. "
            "Diese Variable wird abgeleitet aus den Variablen zur spezifischen "
            "Form des Nachteilsausgleichs z.B. :attr:`nta_zeitv_vieltext` "
            "oder :attr:`nta_other_details_encr`."
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
            "Diese Variable wird abgeleitet aus :attr:`nta_other_details_encr`."
        ),
    )
    nta_other_details_encr: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
        doc="Verschlüsselte Details zu anderen Formen des NTAs für den Klienten",
    )
    nta_nos_notes_encr: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
        doc="Verschlüsselte Notizen zu Notenschutz und Nachteilsausgleich",
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
    case_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc="Zeigt, ob ein Fall aktiv oder abgeschlossen ist",
    )

    def __init__(
        self,
        school: str,
        gender_encr: str,
        class_name_encr: str,
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
        entry_date_encr: date | str | None = None,
        nos_rs: bool | str | int | None = None,
        nos_rs_ausn_faecher_encr: str = "",
        nos_les: bool | str | int | None = None,
        nos_other_details_encr: str = "",
        nta_zeitv_vieltext: int | str | None = None,
        nta_zeitv_wenigtext: int | str | None = None,
        nta_font: bool | str | int | None = None,
        nta_aufg: bool | str | int | None = None,
        nta_struktur: bool | str | int | None = None,
        nta_arbeitsm: bool | str | int | None = None,
        nta_ersgew: bool | str | int | None = None,
        nta_vorlesen: bool | str | int | None = None,
        nta_other_details_encr: str = "",
        nta_nos_notes_encr: str = "",
        nta_nos_end_grade: int | str | None = None,
        lrst_diagnosis_encr: str = "",
        lrst_last_test_date_encr: date | str = "",
        keyword_taet_encr: str = "",
        lrst_last_test_by_encr: str = "",
        min_sessions: int | str | None = None,
        n_sessions: int | str | None = None,
        case_active: bool | str | int | None = True,
    ) -> None:
        client_id_int_or_none = to_int_or_none(client_id)
        if client_id_int_or_none is not None:
            self.client_id = client_id_int_or_none
        self.first_name_encr = first_name_encr
        self.last_name_encr = last_name_encr
        if gender_encr in ("w", "f"):
            self.gender_encr = Gender.FEMALE
        elif gender_encr in ("d", "x"):
            self.gender_encr = Gender.DIVERSE
        elif gender_encr == "m":
            self.gender_encr = Gender.MALE
        else:
            self.gender_encr = gender_encr
        dt_birthday = to_date_or_none(birthday_encr)
        if dt_birthday is None:
            raise ValueError("Das Geburtsdatum ist ein Pflichtfeld.")
        self.birthday_encr = dt_birthday
        self.street_encr = street_encr
        self.city_encr = city_encr
        self.parent_encr = parent_encr
        self.telephone1_encr = telephone1_encr
        self.telephone2_encr = telephone2_encr
        self.email_encr = email_encr
        self.notes_encr = notes_encr
        self.school = school
        self.entry_date_encr = to_date_or_none(entry_date_encr)
        self.class_name_encr = class_name_encr
        self.lrst_diagnosis_encr = lrst_diagnosis_encr
        _lrst_date_dt = to_date_or_none(lrst_last_test_date_encr)
        self.lrst_last_test_date_encr = (
            _lrst_date_dt.isoformat() if _lrst_date_dt else ""
        )
        self.lrst_last_test_by_encr = lrst_last_test_by_encr
        self.keyword_taet_encr = keyword_taet_encr

        # Notenschutz
        self.nos_rs = to_bool_or_none(nos_rs) or False
        self.nos_rs_ausn_faecher_encr = nos_rs_ausn_faecher_encr
        self.nos_les = to_bool_or_none(nos_les) or False
        self.nos_other_details_encr = nos_other_details_encr

        # Nachteilsausgleich
        self.nta_zeitv_vieltext = to_int_or_none(nta_zeitv_vieltext)
        self.nta_zeitv_wenigtext = to_int_or_none(nta_zeitv_wenigtext)
        self.nta_font = to_bool_or_none(nta_font) or False
        self.nta_aufg = to_bool_or_none(nta_aufg) or False
        self.nta_struktur = to_bool_or_none(nta_struktur) or False
        self.nta_arbeitsm = to_bool_or_none(nta_arbeitsm) or False
        self.nta_ersgew = to_bool_or_none(nta_ersgew) or False
        self.nta_vorlesen = to_bool_or_none(nta_vorlesen) or False
        self.nta_other_details_encr = nta_other_details_encr
        self.nta_nos_notes_encr = nta_nos_notes_encr
        self.nta_nos_end_grade = to_int_or_none(nta_nos_end_grade)

        self.min_sessions = to_int_or_none(min_sessions) or 45
        self.n_sessions = to_int_or_none(n_sessions) or 1
        self.case_active = to_bool_or_none(case_active) or False

        # Placeholder for derived fields and timestamps - will be handled by events
        self.class_int_encr = None
        self.estimated_graduation_date_encr = None
        self.document_shredding_date_encr = None
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

        # Calculate class_int_encr
        if self.class_name_encr:
            try:
                self.class_int_encr = extract_number(self.class_name_encr)
            except TypeError, ValueError:
                self.class_int_encr = None
        else:
            self.class_int_encr = None

        # Calculate estimated_graduation_date_encr and document_shredding_date_encr
        self.estimated_graduation_date_encr = None
        self.document_shredding_date_encr = None
        if self.class_int_encr is not None and self.school in config.school:
            try:
                self.estimated_graduation_date_encr = (
                    get_estimated_end_of_academic_year(
                        grade_current=self.class_int_encr,
                        grade_target=config.school[self.school].end,
                    )
                )
                if self.estimated_graduation_date_encr:
                    self.document_shredding_date_encr = get_date_destroy_records(
                        self.estimated_graduation_date_encr,
                    )
            except Exception as e:
                logger.warning(
                    f"Could not calculate estimated_graduation_date_encr or "
                    f"document_shredding_date_encr for client {self.client_id}: {e}",
                )

        # Notenschutz flags
        self.nos_rs_ausn = bool(
            self.nos_rs_ausn_faecher_encr and self.nos_rs_ausn_faecher_encr.strip(),
        )
        self.nos_other = bool(
            self.nos_other_details_encr and self.nos_other_details_encr.strip(),
        )
        self.notenschutz = self.nos_rs or self.nos_les or self.nos_other

        # Nachteilsausgleich flags
        self.nta_zeitv = bool(
            (self.nta_zeitv_vieltext is not None and self.nta_zeitv_vieltext > 0)
            or (self.nta_zeitv_wenigtext is not None and self.nta_zeitv_wenigtext > 0),
        )
        self.nta_other = bool(
            self.nta_other_details_encr and self.nta_other_details_encr.strip(),
        )
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

    @validates("lrst_diagnosis_encr")
    def validate_lrst_diagnosis(
        self,
        key: str,  # noqa: ARG002
        value: str | None,
    ) -> str:
        value = value or ""
        if value and value not in LRST_DIAG:
            raise ValueError(
                f"Invalid value for lrst_diagnosis. "
                f"Allowed values are: {', '.join(LRST_DIAG)}",
            )
        return value

    @validates("keyword_taet_encr")
    def validate_keyword_taet_encr(
        self,
        key: str,  # noqa: ARG002
        value: str,
    ) -> str:
        return check_keyword(value) or ""

    @validates("min_sessions", "n_sessions")
    def validate_sessions(self, key: str, value: str | int) -> int:
        val = to_int_or_none(value)
        if val is None:
            raise ValueError(f"Feld '{key}' muss eine ganze Zahl sein.")
        return val

    @validates("nta_zeitv_vieltext", "nta_zeitv_wenigtext")
    def validate_nta_zeitv_percentage(
        self,
        key: str,  # noqa: ARG002
        value: str | int | None,
    ) -> int | None:
        return to_int_or_none(value)

    @validates(
        "nta_font",
        "nta_aufg",
        "nta_arbeitsm",
        "nta_ersgew",
        "nta_vorlesen",
        "nta_struktur",
        "nos_rs",
        "nos_les",
        "case_active",
    )
    def validate_bool(
        self,
        key: str,  # noqa: ARG002
        value: bool | str | int,
    ) -> bool:
        return to_bool_or_none(value) or False

    @validates("nta_nos_end_grade")
    def validate_nta_nos_end_grade(
        self,
        key: str,  # noqa: ARG002
        value: str | int | None,
    ) -> int | None:
        return to_int_or_none(value)

    @validates("lrst_last_test_date_encr")
    def validate_lrst_last_test_date_encr(
        self,
        key: str,  # noqa: ARG002
        value: str | date | None,
    ) -> str:
        dt = to_date_or_none(value)
        return dt.isoformat() if dt else ""

    @validates("lrst_last_test_by_encr")
    def validate_lrst_last_test_by_encr(self, key: str, value: str | None) -> str:
        value = value or ""
        if value and value not in LRST_TEST_BY:
            raise ValueError(
                f"Invalid value for {key}. "
                f"Allowed values are: {', '.join(LRST_TEST_BY)}",
            )
        return value

    @validates("birthday_encr")
    def validate_birthday(
        self,
        key: str,  # noqa: ARG002
        value: str | date | None,
    ) -> date:
        dt = to_date_or_none(value)
        if dt is None:
            raise ValueError("Das Geburtsdatum ist ein Pflichtfeld.")
        return dt

    @validates(
        "entry_date_encr",
        "estimated_graduation_date_encr",
        "document_shredding_date_encr",
    )
    def validate_optional_dates(
        self,
        key: str,  # noqa: ARG002
        value: str | date | None,
    ) -> date | None:
        return to_date_or_none(value)

    def __repr__(self) -> str:
        return f"<Client(id='{self.client_id}', sc='{self.school}')>"


@event.listens_for(Client, "before_insert")
def receive_before_insert(_mapper, _connection, target: Client) -> None:
    """Set timestamps and calculate derived fields on insert."""
    target.datetime_created = datetime.now()
    target.datetime_lastmodified = datetime.now()
    target._recalculate_derived_fields()


@event.listens_for(Client, "before_update")
def receive_before_update(_mapper, _connection, target: Client) -> None:
    """Update timestamp and recalculate derived fields on update."""
    target.datetime_lastmodified = datetime.now()
    target._recalculate_derived_fields()
