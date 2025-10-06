from pathlib import Path
from typing import Any, ClassVar, Literal

import keyring
import yaml
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.validation import Function, Regex
from textual.widgets import Button, Footer, Header, Input, Select, Static

TOOLTIPS = {
    "logging": "Logging-Niveau für die Anwendung (DEBUG, INFO, WARN oder ERROR)",
    "app_uid": "Identifikator für die Anwendung (muss nicht geändert werden)",
    "app_username": "Benutzername für die Anwendung",
    "schoolpsy_name": "Vollständiger Name der Schulpsychologin / des Schulpsychologen",
    "schoolpsy_street": "Straße und Hausnummer der Stammschule",
    "schoolpsy_city": "Stadt der Stammschule",
    "school_head_w_school": "Titel der Schulleitung an der Schule",
    "school_name": "Vollständiger Name der Schule",
    "school_street": "Straße und Hausnummer der Schule",
    "school_city": "Stadt und Postleitzahl der Schule",
    "end": "Jahrgangsstufe, nach der Schüler typischerweise die Schule abschließen",
    "nstudents": "Anzahl Schüler an der Schule",
}

NoPeriodValidator = Regex(
    regex=r"^(?!.*\.).*$", failure_description="Darf keine Punkte enthalten"
)

PathIsFileValidator = Function(
    function=lambda value: Path(value).expanduser().is_file(),
    failure_description="Pfad ist keine Datei.",
)


def load_config(file_path: Path) -> dict[str, Any]:
    """Load the YAML configuration file."""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config_dict: dict[str, Any], file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class DeleteItemButton(Button):
    """A button that removes its parent widget when pressed."""

    def __init__(self) -> None:
        super().__init__("Löschen", variant="error", classes="delete-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.parent.remove()


class SchoolEditor(Vertical):
    """A widget to edit a single school's configuration."""

    def __init__(self, school_key: str, school_data: dict[str, Any]) -> None:
        super().__init__(classes="item-container")
        self._school_key = school_key
        self._school_data = school_data

    def compose(self) -> ComposeResult:
        yield Input(
            self._school_key,
            id="item_key",
            placeholder="Schullabel",
            validators=[NoPeriodValidator],
        )
        for key, value in self._school_data.items():
            inp_type: Literal["integer", "text"] = (
                "integer" if key in ["end", "nstudents"] else "text"
            )
            inp = Input(str(value), id=key, placeholder=key, type=inp_type)
            inp.tooltip = TOOLTIPS.get(key, "")
            yield inp
        yield DeleteItemButton()

    def get_data(self) -> tuple[str | None, dict[str, Any] | None]:
        key = self.query_one("#item_key", Input).value
        if not key:
            return None, None
        data = {}
        for inp in self.query(Input):
            if inp.id and inp.id != "item_key":
                val = (
                    int(inp.value)
                    if inp.id in ["end", "nstudents"] and inp.value
                    else inp.value
                )
                data[inp.id] = val
        return key, data


class FormSetEditor(Vertical):
    """A widget to edit a single form set."""

    def __init__(self, form_set_key: str, paths: list[str]) -> None:
        super().__init__(classes="item-container")
        self._form_set_key = form_set_key
        self._paths = paths

    def compose(self) -> ComposeResult:
        yield Input(
            self._form_set_key,
            id="item_key",
            placeholder="Formular-Satz-Name",
            validators=[NoPeriodValidator],
        )
        for path in self._paths:
            yield Input(path, classes="path-input", validators=[PathIsFileValidator])
        yield Button("Pfad hinzufügen", classes="add-path-button")
        yield DeleteItemButton()

    @on(Button.Pressed, ".add-path-button")
    def add_path(self, event: Button.Pressed) -> None:
        event.stop()
        self.mount(
            Input(classes="path-input", validators=[PathIsFileValidator]),
            before=event.button,
        )

    def get_data(self) -> tuple[str | None, list[str] | None]:
        key = self.query_one("#item_key", Input).value
        if not key:
            return None, None
        paths = [inp.value for inp in self.query(".path-input") if inp.value]
        return key, paths


class CsvImportEditor(Vertical):
    """A widget to edit a single CSV import configuration."""

    def __init__(self, import_key: str, import_data: dict[str, Any]) -> None:
        super().__init__(classes="item-container")
        self._import_key = import_key
        self._import_data = import_data

    def compose(self) -> ComposeResult:
        yield Input(
            self._import_key,
            id="item_key",
            placeholder="CSV-Import-Name",
            validators=[NoPeriodValidator],
        )

        separator_options = [
            ("Comma (,)", ","),
            ("Semicolon (;)", ";"),
            ("Tab", "\t"),
            ("Pipe (|)", "|"),
        ]
        current_separator = self._import_data.get("separator")
        default_value = current_separator if current_separator else "\t"
        option_values = [opt[1] for opt in separator_options]
        if current_separator and current_separator not in option_values:
            separator_options.append(
                (f"Custom ('{current_separator}')", current_separator)
            )

        yield Select(
            separator_options,
            value=default_value,
            id="separator",
            prompt="Trennzeichen",
        )
        yield Static("Spaltenzuordnung (CSV-Spalte -> DB-Feld)")
        for csv_col, db_col in self._import_data.get("column_mapping", {}).items():
            yield Horizontal(
                Input(csv_col, placeholder="CSV-Spalte", classes="csv-col-input"),
                Input(db_col, placeholder="DB-Feld", classes="db-col-input"),
                classes="mapping-row",
            )
        yield Button("Mapping hinzufügen", classes="add-mapping-button")
        yield DeleteItemButton()

    @on(Button.Pressed, ".add-mapping-button")
    def add_mapping(self, event: Button.Pressed) -> None:
        event.stop()
        self.mount(
            Horizontal(
                Input(placeholder="CSV-Spalte", classes="csv-col-input"),
                Input(placeholder="DB-Feld", classes="db-col-input"),
                classes="mapping-row",
            ),
            before=event.button,
        )

    def get_data(self) -> tuple[str | None, dict[str, Any] | None]:
        key = self.query_one("#item_key", Input).value
        if not key:
            return None, None
        data = {"column_mapping": {}}
        data["separator"] = self.query_one("#separator", Select).value
        mappings = {}
        for row in self.query(".mapping-row"):
            inputs = row.query(Input)
            if len(inputs) == 2 and inputs[0].value:
                mappings[inputs[0].value] = inputs[1].value
        data["column_mapping"] = mappings
        return key, data


class ConfigEditorApp(App[None]):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("ctrl+q", "quit", "Abbrechen", show=True),
    ]

    def __init__(self, config_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="main-scroll"):
            # Core section
            yield Static("App-Einstellungen", classes="section-header")
            for key, value in self.config_dict.get("core", {}).items():
                inp = Input(str(value), id=f"core-{key}", placeholder=key)
                inp.tooltip = TOOLTIPS.get(key, "")
                yield inp

            # Password
            yield Static("Passwort", classes="section-header")
            yield Input(
                placeholder="(Leer lassen, um nicht zu ändern)",
                password=True,
                id="password",
            )

            # Schoolpsy section
            yield Static("Schulpsychologie-Einstellungen", classes="section-header")
            for key, value in self.config_dict.get("schoolpsy", {}).items():
                inp = Input(str(value), id=f"schoolpsy-{key}", placeholder=key)
                inp.tooltip = TOOLTIPS.get(key, "")
                yield inp

            # Dynamic sections
            yield Static("Schulen", classes="section-header")
            for key, data in self.config_dict.get("school", {}).items():
                yield SchoolEditor(key, data)
            yield Button("Schule hinzufügen", id="add-school-button")

            yield Static("Formular-Sätze", classes="section-header")
            for key, data in self.config_dict.get("form_set", {}).items():
                yield FormSetEditor(key, data)
            yield Button("Formular-Satz hinzufügen", id="add-form_set-button")

            yield Static("CSV-Importe", classes="section-header")
            for key, data in self.config_dict.get("csv_import", {}).items():
                yield CsvImportEditor(key, data)
            yield Button("CSV-Import hinzufügen", id="add-csv_import-button")
        yield Horizontal(
            Button("Speichern", id="save", variant="success"),
            Button("Abbrechen", id="cancel", variant="error"),
            classes="action-buttons",
        )
        yield Footer()

    def _rebuild_config_from_ui(self) -> dict[str, Any]:
        """Reconstructs the entire config from the current state of all UI widgets."""
        new_config = {
            "core": {},
            "schoolpsy": {},
            "school": {},
            "form_set": {},
            "csv_import": {},
        }

        # Simple sections
        for key in self.config_dict.get("core", {}):
            new_config["core"][key] = self.query_one(f"#core-{key}", Input).value
        for key in self.config_dict.get("schoolpsy", {}):
            new_config["schoolpsy"][key] = self.query_one(
                f"#schoolpsy-{key}", Input
            ).value

        # Dynamic sections
        for editor in self.query(SchoolEditor):
            key, data = editor.get_data()
            if key and data is not None:
                new_config["school"][key] = data

        for editor in self.query(FormSetEditor):
            key, data = editor.get_data()
            if key and data is not None:
                new_config["form_set"][key] = data

        for editor in self.query(CsvImportEditor):
            key, data = editor.get_data()
            if key and data is not None:
                new_config["csv_import"][key] = data

        return new_config

    @on(Button.Pressed)
    async def handle_button_press(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("add-"):
            section = event.button.id.split("-")[1]

            if section == "school":
                default_data = {
                    "school_head_w_school": "",
                    "school_name": "",
                    "school_street": "",
                    "school_city": "",
                    "end": "",
                    "nstudents": "",
                }
                editor = SchoolEditor(
                    f"NewSchool{len(self.query(SchoolEditor)) + 1}", default_data
                )
            elif section == "form_set":
                editor = FormSetEditor(
                    f"NewFormSet{len(self.query(FormSetEditor)) + 1}", []
                )
            elif section == "csv_import":
                default_data = {"separator": "", "column_mapping": {}}
                editor = CsvImportEditor(
                    f"NewCsvImport{len(self.query(CsvImportEditor)) + 1}", default_data
                )
            else:
                return

            self.query_one("#main-scroll").mount(editor, before=event.button)
            editor.scroll_visible()
            return

        if event.button.id == "save":
            await self.action_save()
        elif event.button.id == "cancel":
            await self.action_quit()

    async def action_save(self) -> None:
        """Rebuilds the config from the UI and saves it."""
        self.config_dict = self._rebuild_config_from_ui()
        save_config(self.config_dict, self.config_path)

        password_input = self.query_one("#password", Input)
        if password_input.value:
            app_uid = self.config_dict.get("core", {}).get("app_uid")
            username = self.config_dict.get("core", {}).get("app_username")
            if app_uid and username:
                keyring.set_password(app_uid, username, password_input.value)
            else:
                self.bell()  # Notify user of error

        self.exit("Configuration saved.")

    async def action_quit(self) -> None:
        self.exit()
