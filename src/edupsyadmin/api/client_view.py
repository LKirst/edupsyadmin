from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import cached_property, lru_cache
from importlib.resources import files
from typing import Any

from dateutil.parser import parse

from edupsyadmin.api.types import ClientData, ClientRecord
from edupsyadmin.core.config import config
from edupsyadmin.core.enums import LrstDiagnosis, LrstTesterType
from edupsyadmin.core.logger import logger
from edupsyadmin.utils.academic_year import (
    get_academic_year_string,
    get_estimated_end_of_academic_year,
    get_this_academic_year_string,
)


@lru_cache(maxsize=32)
def _get_subjects(school: str) -> str:
    """Get a list of subjects for the given school.

    :param school: The name of the school.
    :return: A string containing the subjects separated by newlines.
    """
    file_path = files("edupsyadmin.data").joinpath(f"Faecher_{school}.txt")
    logger.debug(f"trying to read school subjects file: {file_path}")
    if file_path.is_file():
        logger.debug("subjects file exists")
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    else:
        logger.debug("school subjects file does not exist")
        return ""


@dataclass(frozen=True)
class ClientView:
    """
    A read-only view of a client, encapsulating all 'convenience' logic.
    """

    record: ClientRecord

    def _date_to_german_string(self, isodate: date | str | None) -> str:
        if isinstance(isodate, date):
            return isodate.strftime("%d.%m.%Y")
        if (isodate is None) or (isodate == ""):
            return ""
        try:
            return parse(str(isodate), dayfirst=False).strftime("%d.%m.%Y")
        except ValueError:
            logger.error(f"'{isodate}' could not be parsed as a date")
            raise
        except TypeError:
            logger.error(f"'{isodate}' is neither None, datetime.date, nor str")
            raise

    @property
    def name(self) -> str:
        """Vor- und Nachname des Klienten."""
        first_name = self.record.get("first_name_encr") or ""
        last_name = self.record.get("last_name_encr") or ""
        return f"{first_name} {last_name}".strip()

    @property
    def addr_s_nname(self) -> str:
        """Adresse in einer Zeile ohne Name."""
        street = self.record.get("street_encr")
        city = self.record.get("city_encr")
        if street and city:
            return f"{street}, {city}"
        return ""

    @property
    def addr_m_wname(self) -> str:
        """Adresse mit Zeilenumbrüchen mit Name."""
        street = self.record.get("street_encr")
        city = self.record.get("city_encr")
        if street and city:
            return f"{self.name}\n{street}\n{city}"
        return ""

    @cached_property
    def schoolpsy_name(self) -> str:
        """Name der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_name

    @cached_property
    def schoolpsy_street(self) -> str:
        """Straße der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_street

    @cached_property
    def schoolpsy_city(self) -> str:
        """Ort der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_city

    @cached_property
    def schoolpsy_addr_m_wname(self) -> str:
        """Adresse des Nutzers mit Zeilenumbrüchen mit Name."""
        return f"{self.schoolpsy_name}\n{self.schoolpsy_street}\n{self.schoolpsy_city}"

    @cached_property
    def schoolpsy_addr_s_wname(self) -> str:
        """Adresse des Nutzers in einer Zeile mit Name."""
        return self.schoolpsy_addr_m_wname.replace("\n", ", ")

    @property
    def _school_config(self) -> Any | None:
        school_key = self.record.get("school")
        if not school_key:
            return None
        return config.school.get(school_key)

    @property
    def school_name(self) -> str:
        """Name der Schule (aus Konfiguration)."""
        return self._school_config.school_name if self._school_config else ""

    @property
    def school_street(self) -> str:
        """Straße der Schule (aus Konfiguration)."""
        return self._school_config.school_street if self._school_config else ""

    @property
    def school_city(self) -> str:
        """Ort der Schule (aus Konfiguration)."""
        return self._school_config.school_city if self._school_config else ""

    @property
    def school_head_w_school(self) -> str:
        """Bezeichnung der Schulleitung (aus Konfiguration)."""
        return self._school_config.school_head_w_school if self._school_config else ""

    @property
    def school_addr_m_wname(self) -> str:
        """Adresse der Schule mit Zeilenumbrüchen."""
        if not self.school_name:
            return ""
        return f"{self.school_name}\n{self.school_street}\n{self.school_city}"

    @property
    def school_addr_s_wname(self) -> str:
        """Adresse der Schule in einer Zeile."""
        return self.school_addr_m_wname.replace("\n", ", ")

    @property
    def lrst_diagnosis_long(self) -> str:
        """Ausgeschriebene LRSt-Diagnose."""
        diagnosis = self.record.get("lrst_diagnosis_encr")
        if not diagnosis:
            return ""
        try:
            return LrstDiagnosis(diagnosis).long_name
        except ValueError:
            allowed = [v.value for v in LrstDiagnosis]
            raise ValueError(
                f"lrst_diagnosis can be only one of {allowed}, but was {diagnosis}",
            ) from None

    @property
    def today_date(self) -> date:
        """Heutiges Datum."""
        return date.today()

    @cached_property
    def today_date_de(self) -> str:
        """Heutiges Datum im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.today_date)

    @property
    def birthday_de(self) -> str:
        """Geburtsdatum des Klienten im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.record.get("birthday_encr"))

    @property
    def entry_date_de(self) -> str:
        """Eintrittsdatum im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.record.get("entry_date_encr"))

    @property
    def lrst_last_test_date_de(self) -> str:
        """Datum des letzten Tests im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.record.get("lrst_last_test_date_encr"))

    @property
    def document_shredding_date_de(self) -> str:
        """Datum für Aktenvernichtung im Format DD.MM.YYYY."""
        return self._date_to_german_string(
            self.record.get("document_shredding_date_encr")
        )

    @cached_property
    def school_year(self) -> str:
        """Aktuelles Schuljahr im Format YYYY/YYYY."""
        return get_this_academic_year_string()

    @property
    def nta_nos_end_schoolyear(self) -> str:
        """Schuljahr bis zu dem NTA und Notenschutz begrenzt sind."""
        nta_nos_end = self.record.get("nta_nos_end")
        class_int = self.record.get("class_int_encr")
        nta_nos_end_grade = self.record.get("nta_nos_end_grade")

        if nta_nos_end and class_int is not None and nta_nos_end_grade is not None:
            return get_academic_year_string(
                get_estimated_end_of_academic_year(
                    grade_current=class_int,
                    grade_target=nta_nos_end_grade,
                ),
            )
        return ""

    @property
    def lrst_schpsy(self) -> int | None:
        """Numerischer Wert für die Person, die den letzten Test durchgeführt hat."""
        test_by = self.record.get("lrst_last_test_by_encr")
        if not test_by:
            return None
        try:
            return LrstTesterType(test_by).numerical_value
        except ValueError:
            allowed = [v.value for v in LrstTesterType]
            logger.error(
                f"Value for lrst_last_test_by must be in {allowed} but is {test_by}",
            )
            return None

    @property
    def school_subjects(self) -> str:
        """Liste der Schulfächer (aus Fächerdatei)."""
        school_key = self.record.get("school")
        if not school_key:
            return ""
        return _get_subjects(school_key)

    def to_dict(self) -> ClientData:
        """
        Convert to a flat dict including both record and convenience fields.
        Keys are only added if the computed property is non-empty.
        """
        # Create a new ClientData using unpacking.
        # This ensures the type checker can verify required fields if needed,
        # although TypedDict(total=False) is more flexible.
        data: ClientData = {
            **self.record,
            "name": self.name,
            "schoolpsy_name": self.schoolpsy_name,
            "schoolpsy_street": self.schoolpsy_street,
            "schoolpsy_city": self.schoolpsy_city,
            "schoolpsy_addr_m_wname": self.schoolpsy_addr_m_wname,
            "schoolpsy_addr_s_wname": self.schoolpsy_addr_s_wname,
            "today_date": self.today_date,
            "today_date_de": self.today_date_de,
            "birthday_de": self.birthday_de,
            "entry_date_de": self.entry_date_de,
            "lrst_last_test_date_de": self.lrst_last_test_date_de,
            "document_shredding_date_de": self.document_shredding_date_de,
            "school_year": self.school_year,
        }

        # Address fields (only added if both street and city are present)
        addr_s = self.addr_s_nname
        if addr_s:
            data["addr_s_nname"] = addr_s
            data["addr_m_wname"] = self.addr_m_wname

        # School
        if self._school_config:
            data["school_name"] = self.school_name
            data["school_street"] = self.school_street
            data["school_city"] = self.school_city
            data["school_head_w_school"] = self.school_head_w_school
            data["school_addr_m_wname"] = self.school_addr_m_wname
            data["school_addr_s_wname"] = self.school_addr_s_wname
            data["school_subjects"] = self.school_subjects

        # LRSt
        diag_long = self.lrst_diagnosis_long
        if diag_long:
            data["lrst_diagnosis_long"] = diag_long

        # NTA/NOS
        nta_end = self.nta_nos_end_schoolyear
        if nta_end:
            data["nta_nos_end_schoolyear"] = nta_end

        # Tester
        lrst_schpsy = self.lrst_schpsy
        if lrst_schpsy is not None:
            data["lrst_schpsy"] = lrst_schpsy

        return data
