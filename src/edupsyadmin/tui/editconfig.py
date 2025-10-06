from pathlib import Path
from typing import Any, ClassVar, Literal

import keyring
import yaml
from textual import log
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
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


def load_config(file_path: Path) -> dict[str, Any]:
    """Load the YAML configuration file."""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config_dict: dict[str, Any], file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class AddPathButton(Button):
    """Button to add a new path input to a FormSetContainer."""

    def __init__(self) -> None:
        super().__init__("Pfad hinzufügen", classes="addformpath")


class AddMappingButton(Button):
    """Button to add a new mapping to a CsvImportContainer."""

    def __init__(self) -> None:
        super().__init__("Mapping hinzufügen", classes="addmapping")


class DeleteItemButton(Button):
    """Button to delete a container (school, form set, or csv import)."""

    def __init__(self) -> None:
        super().__init__("Löschen", classes="delete")


class SchoolContainer(Vertical):
    """Container for a school's widgets."""


class FormSetContainer(Vertical):
    """Container for a form set's widgets."""


class CsvImportContainer(Vertical):
    """Container for a csv import's widgets."""


class ConfigEditorApp(App[None]):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("ctrl+q", "quit", "Abbrechen", show=True),
    ]

    def __init__(self, config_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)
        self.save_button: Button | None = None
        self.content: VerticalScroll

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.content = VerticalScroll()
        yield self.content

    async def on_mount(self) -> None:
        self.title = "Konfiguration für edupsyadmin"
        self._build_ui_from_config()
        self.call_later(self.update_save_button_state)

    def _build_ui_from_config(self) -> None:
        """Build the entire UI from the self.config_dict."""
        # Core section
        self.content.mount(Static("App-Einstellungen"))
        for key, value in self.config_dict.get("core", {}).items():
            inp = Input(value=str(value), id=f"core-{key}", placeholder=key)
            inp.tooltip = TOOLTIPS.get(key, "")
            self.content.mount(inp)

        # Password
        self.content.mount(
            Static(
                "Wenn bereits ein Passwort hinterlegt ist, lasse das Feld leer. "
                "Ändere es nur, wenn du eine neue Datenbank anlegst."
            )
        )
        self.content.mount(Input(placeholder="Passwort", password=True, id="password"))

        # Schoolpsy section
        self.content.mount(Static("Schulpsychologie-Einstellungen"))
        for key, value in self.config_dict.get("schoolpsy", {}).items():
            inp = Input(value=str(value), id=f"schoolpsy-{key}", placeholder=key)
            inp.tooltip = TOOLTIPS.get(key, "")
            self.content.mount(inp)

        # Dynamic sections
        self._build_dynamic_section("school", "Schule hinzufügen")
        self._build_dynamic_section("form_set", "Formular-Satz hinzufügen")
        self._build_dynamic_section("csv_import", "CSV-Import-Konfiguration hinzufügen")

        # Action buttons
        self.save_button = Button("Speichern", id="save")
        self.content.mount(
            Horizontal(
                self.save_button,
                Button("Abbrechen", id="cancel", variant="error"),
                classes="action-buttons",
            )
        )

    def _build_dynamic_section(self, section_name: str, add_button_label: str) -> None:
        """Build the UI for a dynamic section (school, form_set, csv_import)."""
        self.content.mount(Button(add_button_label, id=f"add-{section_name}-button"))
        for key, data in self.config_dict.get(section_name, {}).items():
            self.add_item_widgets(section_name, key, data)

    def add_item_widgets(
        self, section_name: str, item_key: str, item_data: Any
    ) -> None:
        """Add the widgets for a single item in a dynamic section."""
        container_class = {
            "school": SchoolContainer,
            "form_set": FormSetContainer,
            "csv_import": CsvImportContainer,
        }.get(section_name, Vertical)

        child_widgets = []
        child_widgets.append(Input(value=item_key, id="item_key"))

        if section_name == "school":
            for key, value in item_data.items():
                inp_type: Literal["integer", "text"] = (
                    "integer" if key in ["end", "nstudents"] else "text"
                )
                child_widgets.append(
                    Input(value=str(value), id=key, placeholder=key, type=inp_type)
                )
        elif section_name == "form_set":
            for path in item_data:
                child_widgets.append(Input(value=path, classes="path-input"))
            child_widgets.append(AddPathButton())
        elif section_name == "csv_import":
            separator_options = [
                ("Comma (,)", ","),
                ("Semicolon (;)", ";"),
                ("Tab", "\t"),
                ("Pipe (|)", "|"),
            ]
            current_separator = item_data.get("separator")

            # Default to Tab for new or empty configurations
            default_value = current_separator if current_separator else "\t"

            # Add a custom option if the loaded value isn't standard
            option_values = [opt[1] for opt in separator_options]
            if current_separator and current_separator not in option_values:
                separator_options.append(
                    (f"Custom ('{current_separator}')", current_separator)
                )

            child_widgets.append(
                Select(
                    separator_options,
                    value=default_value,
                    id="separator",
                    allow_blank=False,
                    prompt="Trennzeichen",
                )
            )
            child_widgets.append(Static("Spaltenzuordnung (CSV-Spalte: DB-Feld)"))
            for csv_col, db_col in item_data.get("column_mapping", {}).items():
                child_widgets.append(
                    Horizontal(
                        Input(
                            value=csv_col,
                            placeholder="CSV Column Name",
                            classes="csv-col-input",
                        ),
                        Input(
                            value=db_col,
                            placeholder="Database Field Name",
                            classes="db-col-input",
                        ),
                        classes="mapping-row",
                    )
                )
            child_widgets.append(AddMappingButton())

        child_widgets.append(DeleteItemButton())

        container = container_class(*child_widgets)
        add_button = self.content.query(f"#add-{section_name}-button").first()
        self.content.mount(container, before=add_button)

    def update_save_button_state(self) -> None:
        """Disable the save button if any input is invalid."""
        is_invalid = any(not inp.is_valid for inp in self.query(Input))
        if self.save_button:
            self.save_button.disabled = is_invalid

    async def on_input_changed(self, event: Input.Changed) -> None:
        self.update_save_button_state()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button, DeleteItemButton):
            event.button.parent.remove()
            return
        if isinstance(event.button, AddPathButton):
            event.button.parent.mount(Input(classes="path-input"), before=event.button)
            return
        if isinstance(event.button, AddMappingButton):
            event.button.parent.mount(
                Horizontal(
                    Input(classes="csv-col-input"),
                    Input(classes="db-col-input"),
                    classes="mapping-row",
                ),
                before=event.button,
            )
            return

        if (
            event.button.id
            and event.button.id.startswith("add-")
            and event.button.id.endswith("-button")
        ):
            section = event.button.id.replace("add-", "").replace("-button", "")

            item_data = {}
            if section == "school":
                item_data = {
                    "school_head_w_school": "",
                    "school_name": "",
                    "school_street": "",
                    "school_city": "",
                    "end": "",
                    "nstudents": "",
                }
            elif section == "form_set":
                item_data = []
            elif section == "csv_import":
                item_data = {"separator": "", "column_mapping": {}}

            self.add_item_widgets(section, f"New{section.capitalize()}", item_data)
            return

        if event.button.id == "save":
            await self.action_save()
        elif event.button.id == "cancel":
            self.exit()

    def _rebuild_config_from_ui(self) -> None:
        """Reconstructs self.config_dict from the current state of all UI widgets."""
        new_config = {
            "core": {},
            "schoolpsy": {},
            "school": {},
            "form_set": {},
            "csv_import": {},
        }

        # Simple sections
        for key in self.config_dict.get("core", {}):
            new_config["core"][key] = self.content.query(f"#core-{key}").first().value
        for key in self.config_dict.get("schoolpsy", {}):
            new_config["schoolpsy"][key] = (
                self.content.query(f"#schoolpsy-{key}").first().value
            )

        # Dynamic sections
        for container in self.query(SchoolContainer):
            key = container.query("#item_key").first().value
            if not key:
                continue
            data = {}
            for inp in container.query(Input):
                if inp.id != "item_key":
                    val = (
                        int(inp.value)
                        if inp.id in ["end", "nstudents"] and inp.value
                        else inp.value
                    )
                    data[inp.id] = val
            new_config["school"][key] = data

        for container in self.query(FormSetContainer):
            key = container.query("#item_key").first().value
            if not key:
                continue
            paths = [inp.value for inp in container.query(".path-input") if inp.value]
            new_config["form_set"][key] = paths

        for container in self.query(CsvImportContainer):
            key = container.query("#item_key").first().value
            if not key:
                continue
            data = {"column_mapping": {}}
            data["separator"] = container.query("#separator").first().value
            mappings = {}
            for row in container.query(".mapping-row"):
                inputs = row.query(Input)
                if len(inputs) == 2 and inputs[0].value:
                    csv_input = row.query(".csv-col-input").first()
                    db_input = row.query(".db-col-input").first()
                    mappings[csv_input.value] = db_input.value
            data["column_mapping"] = mappings
            new_config["csv_import"][key] = data

        self.config_dict = new_config

    async def action_save(self) -> None:
        """Rebuilds the config from the UI and saves it."""
        if self.save_button and not self.save_button.disabled:
            self._rebuild_config_from_ui()
            log("save_config was called", config_dict=self.config_dict)
            save_config(self.config_dict, self.config_path)

            password_input = self.query("#password").first()
            if password_input.value:
                app_uid = self.config_dict.get("core", {}).get("app_uid")
                username = self.config_dict.get("core", {}).get("app_username")
                if app_uid and username:
                    keyring.set_password(app_uid, username, password_input.value)
                else:
                    log.error(
                        "Cannot save password: app_uid or app_username is missing."
                    )

            self.exit()
