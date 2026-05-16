from datetime import date, datetime
from typing import TypedDict

from edupsyadmin.core.enums import Gender, LrstDiagnosis, LrstTesterType


class ClientRecord(TypedDict, total=True):
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


class ClientData(ClientRecord, total=False):
    # Convenience fields added by ClientView.to_dict()
    name: str
    addr_s_nname: str
    addr_m_wname: str
    schoolpsy_name: str
    schoolpsy_street: str
    schoolpsy_city: str
    schoolpsy_addr_m_wname: str
    schoolpsy_addr_s_wname: str
    school_name: str
    school_street: str
    school_city: str
    school_head_w_school: str
    school_addr_m_wname: str
    school_addr_s_wname: str
    lrst_diagnosis_long: str
    today_date: date
    birthday_de: str
    today_date_de: str
    entry_date_de: str
    lrst_last_test_date_de: str
    document_shredding_date_de: str
    school_year: str
    nta_nos_end_schoolyear: str
    lrst_schpsy: int
    school_subjects: str


class FillFormResult(TypedDict, total=True):
    """Result of filling forms for a single client."""

    client_id: int
    success: bool
    error: Exception | None
