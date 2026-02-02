from pathlib import Path
from typing import Any, ClassVar, Literal

import yaml
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.validation import Function, Regex
from textual.widgets import Button, Footer, Header, Input, Select, Static

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import (
    DEFAULT_KDF_ITERATIONS,
    check_key_validity,
    derive_key_from_password,
    get_keys_from_keyring,
    load_or_create_salt,
    set_keys_in_keyring,
)
from edupsyadmin.tui.dialogs import YesNoDialog

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
    with file_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config_dict: dict[str, Any], file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with file_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class DeleteItemButton(Button):
    """A button that removes its parent widget when pressed."""

    def __init__(self) -> None:
        super().__init__("Löschen", variant="error", classes="delete-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        parent = self.parent
        if isinstance(parent, Vertical):
            parent.remove()


class SchoolEditor(Vertical):
    """A widget to edit a single school's configuration."""

    def __init__(self, school_key: str, school_data: dict[str, Any]) -> None:
        super().__init__(classes="item-container")
        self._school_key = school_key
        self._school_data = school_data

    def compose(self) -> ComposeResult:
        with Horizontal(classes="input-container"):
            yield Static("Schullabel:", classes="label")
            yield Input(
                self._school_key,
                id="item_key",
                placeholder="Schullabel",
                validators=[NoPeriodValidator],
            )
        school_order = [
            "school_head_w_school",
            "school_name",
            "school_street",
            "school_city",
            "end",
            "nstudents",
        ]
        for key in school_order:
            if key in self._school_data:
                value = self._school_data[key]
                with Horizontal(classes="input-container"):
                    label = Static(f"{key}:", classes="label")
                    label.tooltip = TOOLTIPS.get(key, "")
                    yield label
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
        with Horizontal(classes="input-container"):
            yield Static("Name:", classes="label")
            yield Input(
                self._form_set_key,
                id="item_key",
                placeholder="Formular-Satz-Name",
                validators=[NoPeriodValidator],
            )
        for path in self._paths:
            with Horizontal(classes="input-container"):
                yield Static("Pfad:", classes="label")
                yield Input(
                    path, classes="path-input", validators=[PathIsFileValidator]
                )
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
        paths = [
            inp.value for inp in self.query(".path-input").results(Input) if inp.value
        ]
        return key, paths


class CsvImportEditor(Vertical):
    """A widget to edit a single CSV import configuration."""

    def __init__(self, import_key: str, import_data: dict[str, Any]) -> None:
        super().__init__(classes="item-container")
        self._import_key = import_key
        self._import_data = import_data

    def compose(self) -> ComposeResult:
        with Horizontal(classes="input-container"):
            yield Static("Name:", classes="label")
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
        with Horizontal(classes="input-container"):
            yield Static("Trennzeichen:", classes="label")
            yield Select(
                separator_options,
                value=default_value,
                id="separator",
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
        data: dict[str, Any] = {"column_mapping": {}}
        data["separator"] = self.query_one("#separator", Select).value
        mappings = {}
        for row in self.query(".mapping-row"):
            inputs = row.query(Input)
            if len(inputs) == 2 and inputs[0].value:
                mappings[inputs[0].value] = inputs[1].value
        data["column_mapping"] = mappings
        return key, data


class LgvtEditor(Vertical):
    """A widget to edit the LGVT CSV configuration."""

    def __init__(self, lgvt_data: dict[str, Any] | None) -> None:
        super().__init__(classes="item-container")
        self._lgvt_data = lgvt_data or {}

    def compose(self) -> ComposeResult:
        yield Static("LGVT CSV-Dateien")
        for key in ["Rosenkohl", "Laufbursche", "Toechter"]:
            value = self._lgvt_data.get(key, "")
            with Horizontal(classes="input-container"):
                yield Static(f"{key}:", classes="label")
                inp = Input(
                    str(value) if value else "",
                    id=f"lgvt-{key}",
                    placeholder=key,
                    validators=[PathIsFileValidator],
                    valid_empty=True,
                )
                yield inp

    def get_data(self) -> dict[str, str | None]:
        data = {}
        for key in ["Rosenkohl", "Laufbursche", "Toechter"]:
            inp = self.query_one(f"#lgvt-{key}", Input)
            data[key] = inp.value if inp.value else None
        return data


class ConfigEditorApp(App[None]):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("ctrl+q", "quit", "Abbrechen", show=True),
    ]

    def __init__(
        self, config_path: Path, app_uid: str, app_username: str, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.config_path = config_path
        config.load(self.config_path)
        self.config_dict = config.model_dump(exclude_defaults=False)
        self.app_uid = app_uid
        self.app_username = app_username

        # Determine salt path based on config location
        config_dir = self.config_path.parent
        self.salt_path = config_dir / "salt.txt"
        self.title = "Konfiguration für edupsyadmin"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="main-scroll"):
            # Core section
            yield Static("App-Einstellungen", classes="section-header")
            core_config = self.config_dict.get("core", {})
            core_order = [
                "logging",
                "app_uid",
                "app_username",
                "kdf_iterations",
            ]
            for key in core_order:
                if key in core_config:
                    value = core_config[key]
                    with Horizontal(classes="input-container"):
                        label = Static(f"{key}:", classes="label")
                        label.tooltip = TOOLTIPS.get(key, "")
                        yield label

                        display_value = str(value) if value is not None else ""
                        inp_type: Literal["integer", "text"] = (
                            "integer"
                            if key in ["kdf_iterations", "kdf_iterations_old"]
                            else "text"
                        )
                        valid_empty = key == "kdf_iterations"

                        inp = Input(
                            display_value,
                            id=f"core-{key}",
                            placeholder=key,
                            type=inp_type,
                            valid_empty=valid_empty,
                        )
                        inp.tooltip = TOOLTIPS.get(key, "")
                        yield inp

            # Password
            yield Static("Passwort", classes="section-header")
            with Horizontal(classes="input-container"):
                yield Static("Neues Passwort:", classes="label")
                yield Input(
                    placeholder=(
                        "Leer lassen, falls schon ein Passwort festegelegt wurde"
                    ),
                    password=True,
                    id="password",
                )
            with Horizontal(classes="input-container"):
                yield Static("Passwort bestätigen:", classes="label")
                yield Input(
                    placeholder="Passwort wiederholen",
                    password=True,
                    id="password_confirm",
                )

            # Schoolpsy section
            yield Static("Schulpsychologie-Einstellungen", classes="section-header")
            schoolpsy_config = self.config_dict.get("schoolpsy", {})
            schoolpsy_order = ["schoolpsy_name", "schoolpsy_street", "schoolpsy_city"]
            for key in schoolpsy_order:
                if key in schoolpsy_config:
                    value = schoolpsy_config[key]
                    with Horizontal(classes="input-container"):
                        label = Static(f"{key}:", classes="label")
                        label.tooltip = TOOLTIPS.get(key, "")
                        yield label
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

            yield Static("LGVT CSV-Konfiguration", classes="section-header")
            yield LgvtEditor(self.config_dict.get("lgvtcsv"))

        yield Horizontal(
            Button("Speichern", id="save", variant="success"),
            Button("Abbrechen", id="cancel", variant="error"),
            classes="action-buttons",
        )
        yield Footer()

    def _get_core_config_from_ui(self) -> dict[str, Any]:
        """Rebuild core configuration from UI."""
        config = {}
        keys = ["logging", "app_uid", "app_username", "kdf_iterations"]
        for key in keys:
            value = self.query_one(f"#core-{key}", Input).value
            if key == "kdf_iterations":
                config[key] = int(value) if value else None
            else:
                config[key] = value or ""
        return config

    def _get_schoolpsy_config_from_ui(self) -> dict[str, str]:
        """Rebuild schoolpsy configuration from UI."""
        config = {}
        keys = ["schoolpsy_name", "schoolpsy_street", "schoolpsy_city"]
        for key in keys:
            config[key] = self.query_one(f"#schoolpsy-{key}", Input).value or ""
        return config

    def _get_dynamic_section_data(
        self, editor_type: type[SchoolEditor | FormSetEditor | CsvImportEditor]
    ) -> dict[str, Any]:
        """Helper to get data from dynamic section editors."""
        data = {}
        for editor in self.query(editor_type):
            key, editor_data = editor.get_data()
            if key and editor_data is not None:
                data[key] = editor_data
        return data

    def _get_lgvt_config_from_ui(self) -> dict[str, str | None] | None:
        """Rebuild LGVT CSV configuration from UI."""
        lgvt_editor = self.query_one(LgvtEditor)
        lgvt_data = lgvt_editor.get_data()
        if any(lgvt_data.values()):
            return lgvt_data
        return None

    def _rebuild_config_from_ui(self) -> dict[str, Any]:
        """Reconstructs the entire config from the current state of all UI widgets."""
        return {
            "core": self._get_core_config_from_ui(),
            "schoolpsy": self._get_schoolpsy_config_from_ui(),
            "school": self._get_dynamic_section_data(SchoolEditor),
            "form_set": self._get_dynamic_section_data(FormSetEditor),
            "csv_import": self._get_dynamic_section_data(CsvImportEditor),
            "lgvtcsv": self._get_lgvt_config_from_ui(),
        }

    @on(Button.Pressed)
    async def handle_button_press(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("add-"):
            section = event.button.id.split("-")[1]

            editor: Vertical
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
                default_data: dict[str, Any] = {
                    "separator": "",
                    "column_mapping": {},
                }
                editor = CsvImportEditor(
                    f"NewCsvImport{len(self.query(CsvImportEditor)) + 1}",
                    default_data,
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

    async def _handle_new_password_flow(
        self,
        password: str,
        password_confirm: str,
        app_uid: str,
        username: str,
        existing_keys: list[bytes],
    ) -> bool:
        """
        Handle the logic for when a new password is provided, performing key rotation.
        """
        if len(password) < 8:
            self.notify(
                "Passwort muss mindestens 8 Zeichen lang sein", severity="error"
            )
            self.bell()
            return False

        if password != password_confirm:
            self.notify("Passwörter stimmen nicht überein", severity="error")
            self.bell()
            return False

        # If keys exist, this is a key rotation. Confirm with the user.
        if existing_keys:
            are_existing_keys_valid = all(check_key_validity(k) for k in existing_keys)
            if are_existing_keys_valid:
                confirmed = await self.app.push_screen(
                    YesNoDialog(
                        "Ein gültiger Schlüssel existiert bereits. "
                        "Möchten Sie einen neuen Schlüssel hinzufügen und rotieren?"
                    )
                )
                if not confirmed:
                    self.notify(
                        "Speichern abgebrochen. Die Schlüssel wurden nicht geändert.",
                        severity="warning",
                    )
                    return False
            else:
                self.notify(
                    "Ein oder mehrere existierende Schlüssel sind ungültig "
                    "und werden durch den neuen ersetzt.",
                    severity="error",
                )
                existing_keys.clear()  # Clear invalid keys
                self.bell()

        try:
            self.notify("Neuer Verschlüsselungsschlüssel wird generiert...")
            salt = load_or_create_salt(self.salt_path)
            kdf_input = self.query_one("#core-kdf_iterations", Input)
            iterations = (
                int(kdf_input.value) if kdf_input.value else DEFAULT_KDF_ITERATIONS
            )
            new_key = derive_key_from_password(password, salt, iterations)

            # Prepend the new key for rotation
            updated_keys = [new_key, *existing_keys]
            # Optional: Limit the number of old keys to keep
            # updated_keys = updated_keys[:5]

            set_keys_in_keyring(app_uid, username, updated_keys)
            self.notify(
                "Neuer Verschlüsselungsschlüssel hinzugefügt und gespeichert.",
                severity="information",
            )
        except Exception as e:
            self.notify(f"Fehler beim Speichern des Schlüssels: {e}", severity="error")
            self.bell()
            return False

        return True

    async def action_save(self) -> None:
        """Rebuilds the config from the UI and saves it."""
        password_input = self.query_one("#password", Input)
        password = password_input.value
        password_confirm = self.query_one("#password_confirm", Input).value
        app_uid = self.query_one("#core-app_uid", Input).value
        username = self.query_one("#core-app_username", Input).value

        if not app_uid or not username:
            self.notify(
                "app_uid und app_username müssen gesetzt sein", severity="error"
            )
            self.bell()
            return

        existing_keys = get_keys_from_keyring(app_uid, username)

        if password:
            should_continue = await self._handle_new_password_flow(
                password,
                password_confirm,
                app_uid,
                username,
                existing_keys,
            )
            if not should_continue:
                return
        else:
            if not existing_keys:
                self.notify(
                    "Achtung: Kein Verschlüsselungsschlüssel gesetzt. "
                    "Bitte legen Sie ein Passwort fest.",
                    severity="error",
                )
                self.bell()
                return  # Prevent saving without any keys
            if all(check_key_validity(k) for k in existing_keys):
                self.notify(
                    (
                        "Die bestehenden, gültigen Verschlüsselungsschlüssel werden "
                        "verwendet."
                    ),
                    severity="information",
                )
            else:
                self.notify(
                    (
                        "Achtung: Einer oder mehrere der vorhandenen Schlüssel sind "
                        "ungültig. Bitte Passwort erneut eingeben, um einen neuen, "
                        "gültigen Schlüssel zu erstellen."
                    ),
                    severity="error",
                )
                self.bell()

        self.config_dict = self._rebuild_config_from_ui()
        save_config(self.config_dict, self.config_path)
        self.notify("Konfiguration gespeichert", severity="information")
        self.exit()

    async def action_quit(self) -> None:
        self.exit()
