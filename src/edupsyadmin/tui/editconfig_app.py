from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Footer, Header, Input, Static
from textual.worker import get_current_worker

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import (
    DEFAULT_KDF_ITERATIONS,
    check_key_validity,
    derive_key_from_password,
    get_keys_from_keyring,
    get_salt_from_db,
    set_keys_in_keyring,
)
from edupsyadmin.tui.dialogs import YesNoDialog
from edupsyadmin.tui.editconfig import (
    ConfigInput,
    CsvImportEditor,
    FormSetEditor,
    LgvtEditor,
    PasswordEditor,
    PathIsDirValidator,
    SchoolEditor,
)


def save_config(config_dict: dict[str, Any], file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with file_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class GotKeys(Message):
    def __init__(self, keys: list[bytes]) -> None:
        self.keys = keys
        super().__init__()


class KeyDerivationResult(Message):
    def __init__(self, success: bool, message: str) -> None:
        self.success = success
        self.message = message
        super().__init__()


class ConfigSaved(Message):
    def __init__(self) -> None:
        super().__init__()


class ConfigEditorApp(App[None]):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("ctrl+q", "quit", "Abbrechen", show=True, priority=True),
    ]

    def __init__(
        self,
        config_path: Path,
        app_uid: str,
        app_username: str,
        database_url: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config_path = config_path
        config.load(self.config_path)
        self.config_dict = config.model_dump(exclude_defaults=False)
        self.app_uid = app_uid
        self.app_username = app_username
        self.database_url = database_url

        self.title = "Konfiguration für edupsyadmin"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="main-scroll"):
            # Core section
            yield Static("App-Einstellungen", classes="section-header")
            core_config = self.config_dict.get("core", {})
            for key in (
                "logging",
                "app_uid",
                "app_username",
                "kdf_iterations",
                "template_directory",
                "output_directory",
            ):
                if key in core_config:
                    validators = []
                    if key in ("template_directory", "output_directory"):
                        validators = [PathIsDirValidator]
                    yield ConfigInput(
                        key,
                        core_config[key],
                        id=f"core-{key}",
                        validators=validators,
                        valid_empty=True if validators else None,
                    )

            # Password
            yield PasswordEditor(id="password-section")

            # Schoolpsy section
            yield Static("Schulpsychologie-Einstellungen", classes="section-header")
            schoolpsy_config = self.config_dict.get("schoolpsy", {})
            for key in ("schoolpsy_name", "schoolpsy_street", "schoolpsy_city"):
                if key in schoolpsy_config:
                    yield ConfigInput(key, schoolpsy_config[key], id=f"schoolpsy-{key}")

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
        config_data = {}
        for key in (
            "logging",
            "app_uid",
            "app_username",
            "kdf_iterations",
            "template_directory",
            "output_directory",
        ):
            inp = self.query_one(f"#core-{key}", Input)
            if key == "kdf_iterations":
                config_data[key] = int(inp.value) if inp.value else None
            elif key in ("template_directory", "output_directory"):
                config_data[key] = inp.value or None
            else:
                config_data[key] = inp.value or ""
        return config_data

    def _get_schoolpsy_config_from_ui(self) -> dict[str, str]:
        """Rebuild schoolpsy configuration from UI."""
        config_data = {}
        for key in ("schoolpsy_name", "schoolpsy_street", "schoolpsy_city"):
            config_data[key] = self.query_one(f"#schoolpsy-{key}", Input).value or ""
        return config_data

    def _get_dynamic_section_data(
        self,
        editor_type: type[SchoolEditor | FormSetEditor | CsvImportEditor],
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
        lgvt_data = self.query_one(LgvtEditor).get_data()
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
                    f"NewSchool{len(self.query(SchoolEditor)) + 1}",
                    default_data,
                )
            elif section == "form_set":
                editor = FormSetEditor(
                    f"NewFormSet{len(self.query(FormSetEditor)) + 1}",
                    [],
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

    @on(GotKeys)
    async def on_got_keys(self, message: GotKeys) -> None:
        """Handles the GotKeys message to continue the save process."""
        self.loading = False
        existing_keys = message.keys

        password_editor = self.query_one("#password-section", PasswordEditor)
        password = password_editor.password
        password_confirm = password_editor.password_confirm

        app_uid = self.query_one("#core-app_uid", Input).value
        username = self.query_one("#core-app_username", Input).value

        if password:
            # Call _handle_new_password_flow which fires _key_derivation_worker
            # The rest of the saving logic will continue in on_key_derivation_result
            await self._handle_new_password_flow(
                password,
                password_confirm,
                app_uid,
                username,
                existing_keys,
            )
            return
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
            # If no password and existing keys are valid, proceed to save config
            self.loading = True  # Start loading for save_config
            self.config_dict = self._rebuild_config_from_ui()
            self._save_config_worker(self.config_dict, self.config_path)
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

    async def _handle_new_password_flow(
        self,
        password: str,
        password_confirm: str,
        app_uid: str,
        username: str,
        existing_keys: list[bytes],
    ) -> None:
        """
        Handle the logic for when a new password is provided, performing key rotation.
        """
        if len(password) < 8:
            self.notify(
                "Passwort muss mindestens 8 Zeichen lang sein",
                severity="error",
            )
            self.bell()
            return

        if password != password_confirm:
            self.notify("Passwörter stimmen nicht überein", severity="error")
            self.bell()
            return

        # If keys exist, this is a key rotation. Confirm with the user.
        if existing_keys:
            are_existing_keys_valid = all(check_key_validity(k) for k in existing_keys)
            if are_existing_keys_valid:
                confirmed = await self.app.push_screen(
                    YesNoDialog(
                        "Ein gültiger Schlüssel existiert bereits. "
                        "Möchten Sie einen neuen Schlüssel hinzufügen und rotieren?",
                    ),
                )
                if not confirmed:
                    self.notify(
                        "Speichern abgebrochen. Die Schlüssel wurden nicht geändert.",
                        severity="warning",
                    )
                    return
            else:
                self.notify(
                    "Ein oder mehrere existierende Schlüssel sind ungültig "
                    "und werden durch den neuen ersetzt.",
                    severity="error",
                )
                existing_keys.clear()  # Clear invalid keys
                self.bell()

        self.loading = True  # Start loading indicator
        self.notify("Neuer Verschlüsselungsschlüssel wird generiert...")

        # Get kdf_iterations_value from UI before starting worker
        kdf_iterations_input = self.query_one("#core-kdf_iterations", Input)
        kdf_iterations_value = kdf_iterations_input.value

        # Await the worker to complete the blocking operation
        self._key_derivation_worker(
            password,
            self.database_url,
            app_uid,
            username,
            existing_keys,
            kdf_iterations_value,
        )

    async def action_save(self) -> None:
        """Rebuilds the config from the UI and saves it."""
        app_uid = self.query_one("#core-app_uid", Input).value
        username = self.query_one("#core-app_username", Input).value

        if not app_uid or not username:
            self.notify(
                "app_uid und app_username müssen gesetzt sein",
                severity="error",
            )
            self.bell()
            return

        self.loading = True  # Start loading for get_keys
        self._get_keys_worker(app_uid, username)

    @work(thread=True, exclusive=True, group="key_generation")
    def _key_derivation_worker(
        self,
        password: str,
        database_url: str,
        app_uid: str,
        username: str,
        existing_keys: list[bytes],
        kdf_iterations_value: str,
    ) -> None:
        worker = get_current_worker()  # Get worker for cancellation checks

        try:
            salt = get_salt_from_db(database_url)
            iterations = (
                int(kdf_iterations_value)
                if kdf_iterations_value
                else DEFAULT_KDF_ITERATIONS
            )

            if worker.is_cancelled:
                self.post_message(
                    KeyDerivationResult(False, "Key generation cancelled."),
                )
                return

            new_key = derive_key_from_password(password, salt, iterations)

            if worker.is_cancelled:
                self.post_message(
                    KeyDerivationResult(False, "Key generation cancelled."),
                )
                return

            updated_keys = [new_key, *existing_keys]
            set_keys_in_keyring(app_uid, username, updated_keys)

            self.post_message(
                KeyDerivationResult(
                    True,
                    "Neuer Verschlüsselungsschlüssel hinzugefügt und gespeichert.",
                ),
            )
        except Exception as e:
            self.post_message(
                KeyDerivationResult(
                    False,
                    f"Fehler beim Speichern des Schlüssels: {e}",
                ),
            )

    @work(thread=True)
    def _get_keys_worker(self, app_uid: str, username: str) -> None:
        try:
            existing_keys = get_keys_from_keyring(app_uid, username)
            self.post_message(GotKeys(existing_keys))
        except Exception as e:
            self.log(f"Error getting keys: {e}")
            self.call_from_thread(
                self.notify,
                f"Fehler beim Laden der Schlüssel: {e}",
                severity="error",
            )
            self.call_from_thread(self.bell)
            self.call_from_thread(self.exit)

    @work(thread=True)
    def _save_config_worker(self, config_dict: dict[str, Any], file_path: Path) -> None:
        try:
            save_config(config_dict, file_path)
            self.post_message(ConfigSaved())
        except Exception as e:
            self.log(f"Error saving config: {e}")
            self.call_from_thread(
                self.notify,
                f"Fehler beim Speichern der Konfiguration: {e}",
                severity="error",
            )
            self.call_from_thread(self.bell)
            self.call_from_thread(self.exit)

    @on(KeyDerivationResult)
    async def on_key_derivation_result(self, message: KeyDerivationResult) -> None:
        """Handles the KeyDerivationResult message."""
        self.loading = False
        if message.success:
            self.notify(message.message, severity="information")
            self.loading = True  # Start loading for save_config
            self.config_dict = self._rebuild_config_from_ui()
            self._save_config_worker(self.config_dict, self.config_path)
        else:
            self.notify(message.message, severity="error")
            self.bell()

    @on(ConfigSaved)
    async def on_config_saved(self, message: ConfigSaved) -> None:
        """Handles the ConfigSaved message."""
        self.loading = False
        self.notify("Konfiguration gespeichert", severity="information")
        self.exit()

    async def action_quit(self) -> None:
        self.exit()
