from __future__ import annotations

from datetime import date
from functools import cached_property, lru_cache
from importlib.resources import files
from typing import Any

from dateutil.parser import parse
from pydantic import computed_field

from edupsyadmin.api.types import ClientRecord
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


class ClientView(ClientRecord):
    """
    A read-only view of a client, encapsulating all 'convenience' logic.
    """

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

    @computed_field
    @property
    def name(self) -> str:
        """Vor- und Nachname des Klienten."""
        first_name = self.first_name_encr or ""
        last_name = self.last_name_encr or ""
        return f"{first_name} {last_name}".strip()

    @computed_field
    @property
    def addr_s_nname(self) -> str:
        """Adresse in einer Zeile ohne Name."""
        street = self.street_encr
        city = self.city_encr
        if street and city:
            return f"{street}, {city}"
        return ""

    @computed_field
    @property
    def addr_m_wname(self) -> str:
        """Adresse mit Zeilenumbrüchen mit Name."""
        street = self.street_encr
        city = self.city_encr
        if street and city:
            return f"{self.name}\n{street}\n{city}"
        return ""

    @computed_field
    @cached_property
    def schoolpsy_name(self) -> str:
        """Name der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_name

    @computed_field
    @cached_property
    def schoolpsy_street(self) -> str:
        """Straße der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_street

    @computed_field
    @cached_property
    def schoolpsy_city(self) -> str:
        """Ort der Schulpsychologin / des Schulpsychologen (aus Konfiguration)."""
        return config.schoolpsy.schoolpsy_city

    @computed_field
    @cached_property
    def schoolpsy_addr_m_wname(self) -> str:
        """Adresse des Nutzers mit Zeilenumbrüchen mit Name."""
        return f"{self.schoolpsy_name}\n{self.schoolpsy_street}\n{self.schoolpsy_city}"

    @computed_field
    @cached_property
    def schoolpsy_addr_s_wname(self) -> str:
        """Adresse des Nutzers in einer Zeile mit Name."""
        return self.schoolpsy_addr_m_wname.replace("\n", ", ")

    @property
    def _school_config(self) -> Any | None:
        school_key = self.school
        if not school_key:
            return None
        return config.school.get(school_key)

    @computed_field
    @property
    def school_name(self) -> str:
        """Name der Schule (aus Konfiguration)."""
        return self._school_config.school_name if self._school_config else ""

    @computed_field
    @property
    def school_street(self) -> str:
        """Straße der Schule (aus Konfiguration)."""
        return self._school_config.school_street if self._school_config else ""

    @computed_field
    @property
    def school_city(self) -> str:
        """Ort der Schule (aus Konfiguration)."""
        return self._school_config.school_city if self._school_config else ""

    @computed_field
    @property
    def school_head_w_school(self) -> str:
        """Bezeichnung der Schulleitung (aus Konfiguration)."""
        return self._school_config.school_head_w_school if self._school_config else ""

    @computed_field
    @property
    def school_addr_m_wname(self) -> str:
        """Adresse der Schule mit Zeilenumbrüchen."""
        if not self.school_name:
            return ""
        return f"{self.school_name}\n{self.school_street}\n{self.school_city}"

    @computed_field
    @property
    def school_addr_s_wname(self) -> str:
        """Adresse der Schule in einer Zeile."""
        return self.school_addr_m_wname.replace("\n", ", ")

    @computed_field
    @property
    def lrst_diagnosis_long(self) -> str:
        """Ausgeschriebene LRSt-Diagnose."""
        diagnosis = self.lrst_diagnosis_encr
        if not diagnosis:
            return ""
        try:
            return LrstDiagnosis(diagnosis).long_name
        except ValueError:
            allowed = [v.value for v in LrstDiagnosis]
            raise ValueError(
                f"lrst_diagnosis can be only one of {allowed}, but was {diagnosis}",
            ) from None

    @computed_field
    @property
    def today_date(self) -> date:
        """Heutiges Datum."""
        return date.today()

    @computed_field
    @cached_property
    def today_date_de(self) -> str:
        """Heutiges Datum im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.today_date)

    @computed_field
    @property
    def birthday_de(self) -> str:
        """Geburtsdatum des Klienten im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.birthday_encr)

    @computed_field
    @property
    def entry_date_de(self) -> str:
        """Eintrittsdatum im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.entry_date_encr)

    @computed_field
    @property
    def lrst_last_test_date_de(self) -> str:
        """Datum des letzten Tests im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.lrst_last_test_date_encr)

    @computed_field
    @property
    def document_shredding_date_de(self) -> str:
        """Datum für Aktenvernichtung im Format DD.MM.YYYY."""
        return self._date_to_german_string(self.document_shredding_date_encr)

    @computed_field
    @cached_property
    def school_year(self) -> str:
        """Aktuelles Schuljahr im Format YYYY/YYYY."""
        return get_this_academic_year_string()

    @computed_field
    @property
    def nta_nos_end_schoolyear(self) -> str:
        """Schuljahr bis zu dem NTA und Notenschutz begrenzt sind."""
        nta_nos_end = self.nta_nos_end
        class_int = self.class_int_encr
        nta_nos_end_grade = self.nta_nos_end_grade

        if nta_nos_end and class_int is not None and nta_nos_end_grade is not None:
            return get_academic_year_string(
                get_estimated_end_of_academic_year(
                    grade_current=class_int,
                    grade_target=nta_nos_end_grade,
                ),
            )
        return ""

    @computed_field
    @property
    def lrst_schpsy(self) -> int | None:
        """Numerischer Wert für die Person, die den letzten Test durchgeführt hat."""
        test_by = self.lrst_last_test_by_encr
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

    @computed_field
    @property
    def school_subjects(self) -> str:
        """Liste der Schulfächer (aus Fächerdatei)."""
        school_key = self.school
        if not school_key:
            return ""
        return _get_subjects(school_key)
