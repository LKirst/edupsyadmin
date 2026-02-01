from pathlib import Path

from keyring import get_keyring
from rich.console import Console
from rich.table import Table

from edupsyadmin.__version__ import __version__


def info(
    app_uid: str,
    app_username: str,
    database_url: str,
    config_path: Path,
    salt_path: Path,
) -> None:
    console = Console()

    # Create a table
    table = Table(
        title="EduPsyAdmin Info",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        title_style="bold cyan",
    )

    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Add rows
    table.add_row("Version", f"[bold bright_red]{__version__}[/bold bright_red]")
    table.add_row("App UID", app_uid)
    table.add_row("App Username", app_username)
    table.add_row("Database URL", database_url)
    table.add_row("Config Path", str(config_path))
    table.add_row("Keyring Backend", str(get_keyring()))
    table.add_row("Salt Path", str(salt_path))

    # Display in a panel
    console.print()
    console.print(table)
    console.print()
