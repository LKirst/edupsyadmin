from datetime import date, datetime
from typing import NotRequired, TypedDict

from edupsyadmin.core.enums import Gender, LrstDiagnosis, LrstTesterType


class ClientData(TypedDict, total=True):
    # Base fields from Client model
    client_id: int
    first_name_encr: str
    last_name_encr: str
    gender_encr: Gender | str
    birthday_encr: date
    street_encr: str
    city_encr: str
    parent_encr: str
    telephone1_encr: str
    telephone2_encr: str
    email_encr: str
    notes_encr: str
    keyword_taet_encr: str
    lrst_diagnosis_encr: LrstDiagnosis | str
    lrst_last_test_date_encr: str
    lrst_last_test_by_encr: LrstTesterType | str
    school: str
    entry_date_encr: date | None
    class_name_encr: str
    class_int_encr: int | None
    estimated_graduation_date_encr: date | None
    document_shredding_date_encr: date | None
    datetime_created: datetime
    datetime_lastmodified: datetime
    notenschutz: bool
    nos_rs: bool
    nos_rs_ausn: bool
    nos_rs_ausn_faecher_encr: str
    nos_les: bool
    nos_other: bool
    nos_other_details_encr: str
    nachteilsausgleich: bool
    nta_zeitv: bool
    nta_zeitv_vieltext: int | None
    nta_zeitv_wenigtext: int | None
    nta_font: bool
    nta_aufg: bool
    nta_struktur: bool
    nta_arbeitsm: bool
    nta_ersgew: bool
    nta_vorlesen: bool
    nta_other: bool
    nta_other_details_encr: str
    nta_nos_notes_encr: str
    nta_nos_end: bool
    nta_nos_end_grade: int | None
    min_sessions: int
    n_sessions: int
    case_active: bool

    # Convenience fields added by add_convenience_data
    name: NotRequired[str]
    addr_s_nname: NotRequired[str]
    addr_m_wname: NotRequired[str]
    schoolpsy_name: NotRequired[str]
    schoolpsy_street: NotRequired[str]
    schoolpsy_city: NotRequired[str]
    schoolpsy_addr_m_wname: NotRequired[str]
    schoolpsy_addr_s_wname: NotRequired[str]
    school_name: NotRequired[str]
    school_street: NotRequired[str]
    school_city: NotRequired[str]
    school_head_w_school: NotRequired[str]
    school_addr_m_wname: NotRequired[str]
    school_addr_s_wname: NotRequired[str]
    lrst_diagnosis_long: NotRequired[str]
    today_date: NotRequired[date]
    birthday_de: NotRequired[str]
    today_date_de: NotRequired[str]
    entry_date_de: NotRequired[str]
    lrst_last_test_date_de: NotRequired[str]
    document_shredding_date_de: NotRequired[str]
    school_year: NotRequired[str]
    nta_nos_end_schoolyear: NotRequired[str]
    lrst_schpsy: NotRequired[int]
    school_subjects: NotRequired[str]


class FillFormResult(TypedDict, total=True):
    """Result of filling forms for a single client."""

    client_id: int
    success: bool
    error: Exception | None
