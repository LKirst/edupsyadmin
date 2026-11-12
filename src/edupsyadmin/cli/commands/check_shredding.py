import csv
import textwrap
from argparse import ArgumentParser, Namespace
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.table import Table

from edupsyadmin.api.types import (
    ShreddingCandidateRecord,
    ShreddingReport,
    ShreddingUnsetRecord,
)
from edupsyadmin.core.logger import logger
from edupsyadmin.utils.path_utils import normalize_path
lazy from edupsyadmin.api.managers import ClientsManager

CSV_FIELDNAMES = [
    "client_id",
    "record_academic_year",
    "school",
    "status",
    "document_shredding_date",
]

COMMAND_DESCRIPTION = "Check database for clients due for document shredding"
COMMAND_HELP = "Check database for clients due for document shredding"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Examples:
      # Display human-readable Rich table of clients due for document shredding
      edupsyadmin check-shredding

      # Output only client IDs (one per line) for piping to delete-client:
      edupsyadmin check-shredding --ids-only | xargs -r -n 1 edupsyadmin delete-client

      # Check shredding status as of a future or specific date
      edupsyadmin check-shredding --as-of-date 2026-12-31

      # Also show clients that have no shredding date configured
      edupsyadmin check-shredding --show-unset

      # Filter by school
      edupsyadmin check-shredding --schools SchoolA

      # Export results to CSV
      edupsyadmin check-shredding --out shred_candidates.csv
    """,
)


def _parse_iso_date(value: str) -> date:
    """Parse an ISO 8601 date string (YYYY-MM-DD)."""
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"Invalid date format '{value}'. Expected YYYY-MM-DD.") from e


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for check-shredding command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--ids-only",
        action="store_true",
        help="print only client IDs of due clients (one per line), suitable for piping",
    )
    parser.add_argument(
        "--as-of-date",
        type=_parse_iso_date,
        default=None,
        help="cutoff date (YYYY-MM-DD) to compare against (default: today)",
    )
    parser.add_argument(
        "--show-unset",
        action="store_true",
        help="show clients for which no shredding date is set",
    )
    parser.add_argument(
        "--schools",
        nargs="*",
        type=str,
        default=None,
        help="filter by school name(s)",
    )
    parser.add_argument(
        "--out",
        type=normalize_path,
        default=None,
        help="path to write results as CSV",
    )


def _print_due_table(
    console: Console,
    candidates: list[ShreddingCandidateRecord],
    cutoff: date,
) -> None:
    """Print a Rich table of clients due for document shredding."""
    if not candidates:
        console.print(f"No clients due for document shredding as of {cutoff}.")
        return

    table = Table(title=f"Clients Due for Document Shredding (as of {cutoff})")
    table.add_column("Client ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Academic Year", style="magenta")
    table.add_column("School", style="green")
    table.add_column("Shredding Date", style="yellow")

    for candidate in candidates:
        table.add_row(
            str(candidate.client_id),
            candidate.record_academic_year,
            candidate.school,
            candidate.document_shredding_date_encr.isoformat(),
        )
    console.print(table)


def _print_unset_table(
    console: Console,
    unset_clients: list[ShreddingUnsetRecord],
) -> None:
    """Print a Rich table of clients without a calculated shredding date."""
    if not unset_clients:
        console.print("All clients have a document shredding date set.")
        return

    unset_table = Table(title="Clients Without Document Shredding Date")
    unset_table.add_column("Client ID", justify="right", style="cyan", no_wrap=True)
    unset_table.add_column("Academic Year", style="magenta")
    unset_table.add_column("School", style="green")
    unset_table.add_column("Class", style="white")

    for client in unset_clients:
        unset_table.add_row(
            str(client.client_id),
            client.record_academic_year,
            client.school,
            client.class_name_encr,
        )
    console.print(unset_table)


def _export_csv(
    out_path: Path,
    report: ShreddingReport,
    include_unset: bool,
) -> None:
    """Export shredding report entries to a CSV file."""
    rows: list[dict[str, str | int]] = [
        {
            "client_id": c.client_id,
            "record_academic_year": c.record_academic_year,
            "school": c.school,
            "status": "due",
            "document_shredding_date": c.document_shredding_date_encr.isoformat(),
        }
        for c in report.due_clients
    ]
    if include_unset:
        rows.extend(
            {
                "client_id": u.client_id,
                "record_academic_year": u.record_academic_year,
                "school": u.school,
                "status": "unset",
                "document_shredding_date": "",
            }
            for u in report.unset_clients
        )

    with out_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
    logger.info(f"Saved {len(rows)} records to {out_path}")


def execute(args: Namespace) -> None:
    """Execute check-shredding command."""
    clients_manager = ClientsManager(database_url=args.database_url)
    cutoff = args.as_of_date or date.today()
    console = Console()

    report = clients_manager.get_shredding_report(
        as_of=cutoff,
        schools=args.schools,
    )

    # 1. IDs-only output mode (machine-readable, piped)
    if args.ids_only:
        for candidate in report.due_clients:
            print(candidate.client_id)
        return

    # 2. Rich human-readable table output mode
    _print_due_table(console, report.due_clients, cutoff)

    if args.show_unset:
        _print_unset_table(console, report.unset_clients)
    elif report.unset_clients:
        count = len(report.unset_clients)
        console.print(
            f"[dim]Notice: {count} client(s) have no document shredding "
            "date set. Use --show-unset to display them.[/dim]"
        )

    if args.out:
        _export_csv(args.out, report, include_unset=args.show_unset)
