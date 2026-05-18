from datetime import date, datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from edupsyadmin.core.enums import Gender, LrstDiagnosis, LrstTesterType


def _empty_str_to_none(v: Any) -> Any:
    if v == "":
        return None
    return v


class ClientRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Base fields from Client model
    client_id: int | None = None
    first_name_encr: str = ""
    last_name_encr: str = ""
    gender_encr: Gender | str = ""
    birthday_encr: date | None = None
    street_encr: str = ""
    city_encr: str = ""
    parent_encr: str = ""
    telephone1_encr: str = ""
    telephone2_encr: str = ""
    email_encr: str = ""
    notes_encr: str = ""
    keyword_taet_encr: str = ""
    lrst_diagnosis_encr: LrstDiagnosis | str = ""
    lrst_last_test_date_encr: date | None = None
    lrst_last_test_by_encr: LrstTesterType | str = ""
    school: str = ""
    entry_date_encr: date | None = None
    class_name_encr: str = ""
    class_int_encr: int | None = None
    estimated_graduation_date_encr: date | None = None
    document_shredding_date_encr: date | None = None

    datetime_created: datetime = Field(default_factory=datetime.now)
    datetime_lastmodified: datetime = Field(default_factory=datetime.now)

    notenschutz: bool = False
    nos_rs: bool = False
    nos_rs_ausn: bool = False
    nos_rs_ausn_faecher_encr: str = ""
    nos_les: bool = False
    nos_other: bool = False
    nos_other_details_encr: str = ""

    nachteilsausgleich: bool = False
    nta_zeitv: bool = False
    nta_zeitv_vieltext: int | None = None
    nta_zeitv_wenigtext: int | None = None
    nta_font: bool = False
    nta_aufg: bool = False
    nta_struktur: bool = False
    nta_arbeitsm: bool = False
    nta_ersgew: bool = False
    nta_vorlesen: bool = False
    nta_other: bool = False
    nta_other_details_encr: str = ""
    nta_nos_notes_encr: str = ""
    nta_nos_end: bool = False
    nta_nos_end_grade: int | None = None

    min_sessions: int = 45
    n_sessions: int = 1
    case_active: bool = True

    @field_validator(
        "birthday_encr",
        "lrst_last_test_date_encr",
        "entry_date_encr",
        "estimated_graduation_date_encr",
        "document_shredding_date_encr",
        mode="before",
    )
    @classmethod
    def validate_date(cls, v: Any) -> Any:
        return _empty_str_to_none(v)


class FillFormResult(TypedDict, total=True):
    """Result of filling forms for a single client."""

    client_id: int
    success: bool
    error: Exception | None
