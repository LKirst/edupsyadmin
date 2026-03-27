from datetime import date, datetime
from typing import Required, TypedDict


class ClientData(TypedDict, total=False):
    # Base fields from Client model
    client_id: Required[int]
    first_name_encr: Required[str]
    last_name_encr: Required[str]
    gender_encr: Required[str]
    birthday_encr: Required[date]
    street_encr: Required[str]
    city_encr: Required[str]
    parent_encr: Required[str]
    telephone1_encr: Required[str]
    telephone2_encr: Required[str]
    email_encr: Required[str]
    notes_encr: Required[str]
    keyword_taet_encr: Required[str]
    lrst_diagnosis_encr: Required[str]
    lrst_last_test_date_encr: Required[str]
    lrst_last_test_by_encr: Required[str]
    school: Required[str]
    entry_date_encr: Required[date | None]
    class_name_encr: Required[str | None]
    class_int_encr: Required[int | None]
    estimated_graduation_date_encr: Required[date | None]
    document_shredding_date_encr: Required[date | None]
    datetime_created: Required[datetime]
    datetime_lastmodified: Required[datetime]
    notenschutz: Required[bool]
    nos_rs: Required[bool]
    nos_rs_ausn: Required[bool]
    nos_rs_ausn_faecher_encr: Required[str | None]
    nos_les: Required[bool]
    nos_other: Required[bool]
    nos_other_details_encr: Required[str | None]
    nachteilsausgleich: Required[bool]
    nta_zeitv: Required[bool]
    nta_zeitv_vieltext: Required[int | None]
    nta_zeitv_wenigtext: Required[int | None]
    nta_font: Required[bool]
    nta_aufg: Required[bool]
    nta_struktur: Required[bool]
    nta_arbeitsm: Required[bool]
    nta_ersgew: Required[bool]
    nta_vorlesen: Required[bool]
    nta_other: Required[bool]
    nta_other_details_encr: Required[str | None]
    nta_nos_notes_encr: Required[str | None]
    nta_nos_end: Required[bool]
    nta_nos_end_grade: Required[int | None]
    min_sessions: Required[int]
    n_sessions: Required[int]
    case_active: Required[bool]

    # Convenience fields added by add_convenience_data
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
