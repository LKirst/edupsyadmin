from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def display_client_details(client_data: dict[str, Any]) -> None:
    """Displays client details in a formatted way using rich."""
    console = Console()

    # Helper to print a table for a group of fields
    def print_group_table(data: dict, title: str, fields: list[str]) -> None:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="cyan")
        table.add_column()
        for field in fields:
            value = data.get(field)
            if value is not None and value != "":
                table.add_row(field, str(value))

        console.print(Panel(table, title=f"[bold cyan]{title}[/bold cyan]"))

    # Person
    person_fields = [
        "client_id",
        "first_name_encr",
        "last_name_encr",
        "gender_encr",
        "birthday_encr",
        "school",
        "class_name",
        "entry_date",
        "keyword_taet_encr",
        "min_sessions",
        "n_sessions",
        "estimated_graduation_date",
    ]
    print_group_table(client_data, "Person", person_fields)

    # Notizen
    notes_field = ["notes_encr"]
    print_group_table(client_data, "Notizen", notes_field)

    # Kontaktdaten
    kontaktdaten_fields = [
        "street_encr",
        "city_encr",
        "parent_encr",
        "telephone1_encr",
        "telephone2_encr",
        "email_encr",
    ]
    print_group_table(client_data, "Kontaktdaten", kontaktdaten_fields)

    # Notenschutz
    notenschutz_fields = [
        "notenschutz",
        "nos_rs",
        "nos_rs_ausn",
        "nos_rs_ausn_faecher",
        "nos_les",
        "nos_other",
        "nos_other_details",
    ]
    print_group_table(client_data, "Notenschutz", notenschutz_fields)

    # Nachteilsausgleich
    nta_fields = [
        "nachteilsausgleich",
        "nta_zeitv",
        "nta_zeitv_vieltext",
        "nta_zeitv_wenigtext",
        "nta_font",
        "nta_aufg",
        "nta_struktur",
        "nta_arbeitsm",
        "nta_ersgew",
        "nta_vorlesen",
        "nta_other",
        "nta_other_details",
        "nta_nos_notes",
        "nta_nos_end",
        "nta_nos_end_grade",
    ]
    print_group_table(client_data, "Nachteilsausgleich", nta_fields)

    # LRSt
    lrst_fields = [
        "lrst_diagnosis_encr",
        "lrst_last_test_by_encr",
        "lrst_last_test_date_encr",
    ]
    print_group_table(client_data, "LRSt", lrst_fields)

    # Dates
    dates_fields = [
        "document_shredding_date",
        "datetime_created",
        "datetime_lastmodified",
    ]
    print_group_table(client_data, "Daten Dokumentation", dates_fields)
