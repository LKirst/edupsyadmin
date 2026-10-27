from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar, Final

import yaml
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from rich.markup import escape
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.dom import DOMNode
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, RichLog, Select, Static
from textual.worker import get_current_worker

from edupsyadmin.core.config import (
    AppConfig,
    CoreConfig,
    SchoolConfig,
    SchoolpsyConfig,
    config,
)
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
    MAPPING_INPUTS_COUNT,
    ConfigInput,
    CsvImportEditor,
    FormSetEditor,
    LgvtEditor,
    PasswordEditor,
    PathIsDirValidator,
    SchoolEditor,
)

MIN_PASSWORD_LENGTH: Final[int] = 8

# app_uid has a model default, but the keyring needs a non-empty value.
CORE_REQUIRED_FIELDS: Final[tuple[str, ...]] = ("app_uid", "app_username")
SCHOOLPSY_FIELDS: Final[tuple[str, ...]] = tuple(SchoolpsyConfig.model_fields)
SCHOOL_REQUIRED_FIELDS: Final[tuple[str, ...]] = tuple(
    name for name, info in SchoolConfig.model_fields.items() if info.is_required()
)
# Integer inputs and their minimum values.
INTEGER_FIELDS: Final[dict[str, int]] = {
    "kdf_iterations": 1,
    "end": 1,
    "nstudents": 0,
}
LOGGING_DEFAULT: Final[str] = CoreConfig.model_fields["logging"].default

FIELD_LABELS: Final[dict[str, str]] = {
    # core
    "app_uid": "App-UID",
    "app_username": "Benutzername",
    "logging": "Logging",
    "kdf_iterations": "KDF-Iterationen",
    "template_directory": "Vorlagen-Verzeichnis",
    "output_directory": "Ausgabe-Verzeichnis",
    # schoolpsy
    "schoolpsy_name": "Name (Schulpsycholog:in)",
    "schoolpsy_street": "Straße (Schulpsycholog:in)",
    "schoolpsy_city": "Ort (Schulpsycholog:in)",
    # school fields
    "school_head_w_school": "Schulleitung (m/w)",
    "school_name": "Schulname",
    "school_street": "Schulstraße",
    "school_city": "Schulort",
    "end": "Abschluss-Jahrgangsstufe",
    "nstudents": "Schüleranzahl",
    # dynamic section editors
    "item_key": "Name",
    "separator": "Trennzeichen",
}


def save_config(config_dict: dict[str, Any], file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file.

    :param config_dict: The configuration to write.
    :param file_path: Target YAML file.
    """
    with file_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


def normalize_config_value(value: Any) -> Any:
    """Strip strings recursively and drop empty list items and empty dict keys.

    Do not use this on values where whitespace is meaningful, such as the
    CSV separator (a tab strips to an empty string).

    :param value: A string, dict, list or any other value.
    :returns: The normalized value; other types are returned unchanged.
    """
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        cleaned = {
            (k.strip() if isinstance(k, str) else k): normalize_config_value(v)
            for k, v in value.items()
        }
        return {k: v for k, v in cleaned.items() if k != ""}
    if isinstance(value, list):
        items = (normalize_config_value(item) for item in value)
        return [item for item in items if item != ""]
    return value


class GotKeys(Message):
    """Posted when the keys have been read from the keyring."""

    def __init__(self, keys: list[bytes]) -> None:
        self.keys = keys
        super().__init__()


class KeyDerivationResult(Message):
    """Posted when the key derivation worker has finished."""

    def __init__(self, success: bool, message: str) -> None:
        self.success = success
        self.message = message
        super().__init__()


class ConfigSaved(Message):
    """Posted when the configuration file has been written."""

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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.config_path = config_path
        config.load(self.config_path)
        self.config_dict = config.model_dump(exclude_defaults=False)
        self.app_uid = app_uid
        self.app_username = app_username
        self.database_url = database_url

        # Widgets that blocked the most recent save attempt.
        self._invalid_inputs: list[Widget] = []

        # Keyring identity as loaded; keys live under these names.
        core = self.config_dict.get("core", {})
        self._loaded_identity: tuple[str, str] = (
            str(core.get("app_uid") or ""),
            str(core.get("app_username") or ""),
        )

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
            for key in SCHOOLPSY_FIELDS:
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

        yield RichLog(id="edit-config-log", markup=True, wrap=True)
        # Spnner shown during long-running operations
        yield Horizontal(
            Button("Speichern", id="save", variant="success"),
            Button("Abbrechen", id="cancel", variant="error"),
            classes="action-buttons",
        )
        yield Footer()

    # ------------------------------------------------------------------
    # Log widget and error reporting
    # ------------------------------------------------------------------

    def log_error(self, message: str, *, bell: bool = True) -> None:
        """Write an error message to the log widget and make it visible.

        :param message: Plain text. Rich markup in it is escaped.
        :param bell: Whether to ring the terminal bell.
        """
        log = self.query_one("#edit-config-log", expect_type=RichLog)
        log.add_class("-visible")
        log.write(f"[bold red]Fehler:[/bold red] {escape(message)}")
        if bell:
            self.bell()

    def log_warning(self, message: str) -> None:
        """Write a warning message to the log widget and make it visible.

        :param message: Plain text. Rich markup in it is escaped.
        """
        log = self.query_one("#edit-config-log", expect_type=RichLog)
        log.add_class("-visible")
        log.write(f"[bold yellow]Warnung:[/bold yellow] {escape(message)}")

    def log_detail(self, message: str) -> None:
        """Write an indented bullet line to the log widget.

        :param message: Plain text. Rich markup in it is escaped.
        """
        log = self.query_one("#edit-config-log", expect_type=RichLog)
        log.add_class("-visible")
        log.write(f"  • {escape(message)}")

    def clear_log(self) -> None:
        """Clear the log widget and hide it."""
        log = self.query_one("#edit-config-log", expect_type=RichLog)
        log.clear()
        log.remove_class("-visible")

    def _fail(self, message: str) -> None:
        """Stop loading, show an error toast and log the error.

        The toast is created with ``markup=False`` because ``notify`` parses
        markup by default and messages may contain square brackets. Safe to
        use with ``call_from_thread``.

        :param message: Plain text error message.
        """
        self.screen.loading = False  # turn off spinner
        self.notify(message, severity="error", markup=False)
        self.log_error(message)

    # ------------------------------------------------------------------
    # Validation before saving
    # ------------------------------------------------------------------

    def _mark_input(self, widget: Widget, *, valid: bool) -> None:
        """Set the ``-valid``/``-invalid`` classes and remember invalid widgets.

        :param widget: The input or select widget to style.
        :param valid: Whether the widget is valid.
        """
        widget.set_class(not valid, "-invalid")
        widget.set_class(valid, "-valid")
        if not valid:
            self._invalid_inputs.append(widget)

    @staticmethod
    def _integer_error(prefix: str, value: str, minimum: int) -> str | None:
        """Check that ``value`` is an integer of at least ``minimum``.

        :param prefix: Message prefix naming the field.
        :param value: The stripped, non-empty text.
        :param minimum: Smallest accepted value.
        :returns: An error message, or ``None`` if the value is fine.
        """
        try:
            number = int(value)
        except ValueError:
            return f"{prefix} muss eine ganze Zahl sein."
        if number < minimum:
            return f"{prefix} muss mindestens {minimum} sein."
        return None

    def _check_required_input(
        self,
        inp: Input,
        context: str,
        *,
        field_label: str | None = None,
        required: bool = True,
        integer_min: int | None = None,
    ) -> str | None:
        """Validate an input and style it accordingly.

        The value is stripped before the validators run, so validation sees
        what will be saved.

        :param inp: The input widget to check.
        :param context: Context used in the error message.
        :param field_label: Optional field name appended to ``context``.
        :param required: Whether an empty value is an error.
        :param integer_min: If set, the value must be an integer >= this.
        :returns: An error message, or ``None`` if the input is valid.
        """
        prefix = f"{context}: {field_label}" if field_label else context
        value = inp.value.strip()
        error: str | None = None
        if not value:
            if required:
                error = f"{prefix} darf nicht leer sein."
        else:
            if integer_min is not None:
                error = self._integer_error(prefix, value, integer_min)
            if error is None:
                result = inp.validate(value)
                if result is not None and not result.is_valid:
                    reasons = "; ".join(
                        desc.rstrip(".") for desc in result.failure_descriptions
                    )
                    error = f"{prefix} ist ungültig" + (
                        f" ({reasons})." if reasons else "."
                    )
        self._mark_input(inp, valid=error is None)
        return error

    def _check_fields(
        self,
        scope: DOMNode,
        id_prefix: str,
        fields: Iterable[str],
        context: str,
        *,
        required: bool = True,
    ) -> list[str]:
        """Check a group of inputs below ``scope``.

        :param scope: Node to query (the app or an editor).
        :param id_prefix: Prefix of the input ids, e.g. ``"core-"``.
        :param fields: Field names without prefix.
        :param context: Context used in error messages.
        :param required: Whether empty values are errors.
        :returns: A list of error messages.
        """
        errors: list[str] = []
        for field in fields:
            inp = scope.query_one(f"#{id_prefix}{field}", expect_type=Input)
            label = FIELD_LABELS.get(field, field)
            error = self._check_required_input(
                inp,
                context,
                field_label=f"'{label}'",
                required=required,
                integer_min=INTEGER_FIELDS.get(field),
            )
            if error:
                errors.append(error)
        return errors

    def _validate_unique_keys(
        self,
        editor_type: type[Widget],
        context: str,
        field_label: str = "Name",
    ) -> list[str]:
        """Validate the ``#item_key`` input of every editor of one type.

        :param editor_type: Editor widget class to query.
        :param context: Section label used in error messages.
        :param field_label: Name of the key field in messages.
        :returns: A list of error messages.
        """
        errors: list[str] = []
        seen: set[str] = set()
        for editor in self.query(editor_type).results(editor_type):
            key_inp = editor.query_one("#item_key", expect_type=Input)
            key = key_inp.value.strip()
            scope = f"{context} '{key}'" if key else context
            error = self._check_required_input(
                key_inp,
                scope,
                field_label=field_label,
            )
            if error is None:
                if key in seen:
                    error = f"{scope}: {field_label} existiert mehrfach."
                    self._mark_input(key_inp, valid=False)
                else:
                    seen.add(key)
            if error:
                errors.append(error)
        return errors

    def _validate_school_inputs(self) -> list[str]:
        """Validate school keys and the required fields of every school.

        :returns: A list of error messages.
        """
        errors = self._validate_unique_keys(SchoolEditor, "Schule", "Schullabel")
        for editor in self.query(SchoolEditor).results(SchoolEditor):
            key = editor.query_one("#item_key", expect_type=Input).value.strip()
            display_name = key or "Neue Schule"
            errors += self._check_fields(
                editor,
                "",
                SCHOOL_REQUIRED_FIELDS,
                f"Schule '{display_name}'",
            )
        return errors

    def _validate_csv_details(self) -> list[str]:
        """Validate separator and column mapping of every CSV import.

        A blank separator, a mapping row with only one side filled in and a
        CSV column that is mapped twice are errors. Rows where both sides are
        empty are ignored, as ``get_data`` drops them.

        :returns: A list of error messages.
        """
        errors: list[str] = []
        for editor in self.query(CsvImportEditor).results(CsvImportEditor):
            name = editor.query_one("#item_key", expect_type=Input).value.strip()
            scope = f"CSV-Import '{name}'" if name else "CSV-Import"

            separator = editor.query_one("#separator", expect_type=Select)
            blank = separator.is_blank()
            if blank:
                errors.append(f"{scope}: Trennzeichen muss ausgewählt werden.")
            self._mark_input(separator, valid=not blank)

            seen: set[str] = set()
            for row in editor.query(".mapping-row"):
                inputs = list(row.query(Input).results(Input))
                if len(inputs) != MAPPING_INPUTS_COUNT:
                    continue
                csv_inp, db_inp = inputs
                csv_col = csv_inp.value.strip()
                db_col = db_inp.value.strip()
                csv_inp.remove_class("-invalid")
                db_inp.remove_class("-invalid")
                if not csv_col and not db_col:
                    continue
                if not csv_col:
                    errors.append(f"{scope}: CSV-Spalte fehlt für Feld '{db_col}'.")
                    self._mark_input(csv_inp, valid=False)
                elif not db_col:
                    errors.append(f"{scope}: DB-Feld fehlt für Spalte '{csv_col}'.")
                    self._mark_input(db_inp, valid=False)
                elif csv_col in seen:
                    errors.append(f"{scope}: Spalte '{csv_col}' ist mehrfach belegt.")
                    self._mark_input(csv_inp, valid=False)
                else:
                    seen.add(csv_col)
        return errors

    @staticmethod
    def _format_model_error(error: ErrorDetails) -> str:
        """Turn one Pydantic error into a German log line.

        :param error: An entry from ``ValidationError.errors()``.
        :returns: A readable message that names the section and field.
        """
        parts = [str(part) for part in error["loc"]]
        field = parts[-1] if parts else "?"
        label = FIELD_LABELS.get(field, field)
        section = " / ".join(parts[:-1])
        where = f"{section}: " if section else ""
        return f"Konfiguration, {where}'{label}': {error['msg']}"

    def _validate_against_model(self) -> list[str]:
        """Validate the rebuilt config against the ``AppConfig`` model.

        This catches anything that would make ``config.load()`` fail on the
        next start, including cases the widget checks miss.

        :returns: A list of error messages, empty if the config is valid.
        """
        try:
            data = self._rebuild_config_from_ui()
        except ValueError as e:
            return [f"Konfiguration konnte nicht gelesen werden: {e}"]
        try:
            AppConfig.model_validate(data)
        except ValidationError as e:
            return [self._format_model_error(err) for err in e.errors()]
        return []

    def _validate_inputs_for_save(self) -> bool:
        """Validate all inputs, log every problem and focus the first one.

        Widget checks run first so fields get highlighted. Only if they pass
        is the whole config validated against the Pydantic model.

        :returns: ``True`` if the configuration may be saved, else ``False``.
        """
        self._invalid_inputs = []
        errors: list[str] = []
        errors += self._check_fields(
            self,
            "core-",
            CORE_REQUIRED_FIELDS,
            "App-Einstellungen",
        )
        errors += self._check_fields(
            self,
            "core-",
            ("kdf_iterations",),
            "App-Einstellungen",
            required=False,
        )
        errors += self._check_fields(
            self,
            "schoolpsy-",
            SCHOOLPSY_FIELDS,
            "Schulpsychologie",
        )
        errors += self._validate_school_inputs()
        errors += self._validate_unique_keys(FormSetEditor, "Formular-Satz")
        errors += self._validate_unique_keys(CsvImportEditor, "CSV-Import")
        errors += self._validate_csv_details()

        if not errors:
            errors = self._validate_against_model()
        if not errors:
            return True

        # One bell for the header; the detail lines are silent.
        self.log_error("Bitte alle Pflichtfelder ausfüllen und Fehler korrigieren:")
        for err in errors:
            self.log_detail(err)

        # Focus the first blocking widget in document order.
        blocking = set(self._invalid_inputs)
        first_invalid = next(
            (w for w in self.query("Input, Select") if w in blocking),
            None,
        )
        if first_invalid is not None:
            first_invalid.focus()
        return False

    # ------------------------------------------------------------------
    # Rebuilding the config from the UI
    # ------------------------------------------------------------------

    def _get_core_config_from_ui(self) -> dict[str, Any]:
        """Rebuild core configuration from UI."""
        config_data: dict[str, Any] = {}
        for key in (
            "logging",
            "app_uid",
            "app_username",
            "kdf_iterations",
            "template_directory",
            "output_directory",
        ):
            inp = self.query_one(f"#core-{key}", expect_type=Input)
            value = inp.value.strip()
            if key == "kdf_iterations":
                config_data[key] = int(value) if value else None
            elif key in ("template_directory", "output_directory"):
                config_data[key] = value or None
            elif key == "logging":
                config_data[key] = value or LOGGING_DEFAULT
            else:
                config_data[key] = value
        return config_data

    def _get_schoolpsy_config_from_ui(self) -> dict[str, Any]:
        """Rebuild schoolpsy configuration from UI."""
        config_data: dict[str, Any] = {}
        for key in SCHOOLPSY_FIELDS:
            inp = self.query_one(f"#schoolpsy-{key}", expect_type=Input)
            config_data[key] = inp.value.strip()
        return config_data

    def _get_dynamic_section_data(
        self,
        editor_type: type[SchoolEditor | FormSetEditor | CsvImportEditor],
    ) -> dict[str, Any]:
        """Helper to get data from dynamic section editors."""
        data: dict[str, Any] = {}
        for editor in self.query(editor_type).results(editor_type):
            key, editor_data = editor.get_data()
            if key and editor_data is not None:
                data[key] = editor_data
        return data

    def _get_csv_import_config_from_ui(self) -> dict[str, Any]:
        """Rebuild the CSV import section.

        Only the column mapping is normalized; the separator is left alone
        because a tab is whitespace.
        """
        data = self._get_dynamic_section_data(CsvImportEditor)
        for entry in data.values():
            entry["column_mapping"] = normalize_config_value(
                entry.get("column_mapping", {}),
            )
        return data

    def _get_lgvt_config_from_ui(self) -> dict[str, str | None]:
        """Rebuild LGVT CSV configuration from UI."""
        raw = self.query_one(LgvtEditor).get_data()
        return {
            key: (value.strip() or None) if isinstance(value, str) else value
            for key, value in raw.items()
        }

    def _rebuild_config_from_ui(self) -> dict[str, Any]:
        """Reconstruct the entire config from the current state of all widgets.

        :raises ValueError: If an integer field cannot be converted.
        """
        return {
            "core": self._get_core_config_from_ui(),
            "schoolpsy": self._get_schoolpsy_config_from_ui(),
            "school": normalize_config_value(
                self._get_dynamic_section_data(SchoolEditor),
            ),
            "form_set": normalize_config_value(
                self._get_dynamic_section_data(FormSetEditor),
            ),
            "csv_import": self._get_csv_import_config_from_ui(),
            "lgvtcsv": self._get_lgvt_config_from_ui(),
        }

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _unused_key(self, prefix: str, editor_type: type[Widget]) -> str:
        """Return ``prefix`` plus the smallest number not yet used as a key.

        :param prefix: Name prefix such as ``"NewSchool"``.
        :param editor_type: Editor class whose ``#item_key`` values are taken.
        :returns: A key that no editor of this type uses yet.
        """
        used = {
            editor.query_one("#item_key", expect_type=Input).value.strip()
            for editor in self.query(editor_type).results(editor_type)
        }
        number = len(used) + 1
        while f"{prefix}{number}" in used:
            number += 1
        return f"{prefix}{number}"

    @on(Button.Pressed)
    async def handle_button_press(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("add-"):
            section = event.button.id.split("-")[1]

            editor: Vertical
            if section == "school":
                school_defaults: dict[str, Any] = {
                    "school_head_w_school": "",
                    "school_name": "",
                    "school_street": "",
                    "school_city": "",
                    "end": "",
                    "nstudents": "",
                }
                editor = SchoolEditor(
                    self._unused_key("NewSchool", SchoolEditor),
                    school_defaults,
                )
            elif section == "form_set":
                editor = FormSetEditor(
                    self._unused_key("NewFormSet", FormSetEditor),
                    [],
                )
            elif section == "csv_import":
                csv_defaults: dict[str, Any] = {
                    "separator": "",
                    "column_mapping": {},
                }
                editor = CsvImportEditor(
                    self._unused_key("NewCsvImport", CsvImportEditor),
                    csv_defaults,
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

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        """Clear a stale ``-invalid`` mark once the input looks acceptable."""
        inp = event.input
        result = event.validation_result
        if (
            inp.has_class("-invalid")
            and inp.value.strip()
            and (result is None or result.is_valid)
        ):
            inp.set_class(False, "-invalid")
            inp.set_class(True, "-valid")

    @on(Select.Changed)
    def on_select_changed(self, event: Select.Changed) -> None:
        """Clear a stale ``-invalid`` mark once a value is selected."""
        if event.select.has_class("-invalid") and not event.select.is_blank():
            event.select.set_class(False, "-invalid")

    @staticmethod
    def _label_for_input(inp: Input) -> str:
        """Return a human-readable label for an input.

        :param inp: The input widget.
        :returns: The German label, the id without prefix, or a generic name.
        """
        if inp.has_class("path-input"):
            return "Pfad"
        input_id = inp.id
        if not input_id:
            return "Eingabefeld"
        for prefix in ("core-", "schoolpsy-", "lgvt-"):
            if input_id.startswith(prefix):
                input_id = input_id.removeprefix(prefix)
                break
        return FIELD_LABELS.get(input_id, input_id)

    @on(Input.Blurred)
    def check_for_validation(self, event: Input.Blurred) -> None:
        """Show validator failures of a blurred input as a quiet warning."""
        result = event.validation_result
        if result is None or result.is_valid or not result.failure_descriptions:
            return
        label = self._label_for_input(event.input)
        for desc in result.failure_descriptions:
            self.log_warning(f"'{label}': {desc}")

    @on(GotKeys)
    async def on_got_keys(self, message: GotKeys) -> None:
        """Handles the GotKeys message to continue the save process."""
        existing_keys = message.keys

        password_editor = self.query_one(
            "#password-section",
            expect_type=PasswordEditor,
        )
        password = password_editor.password
        password_confirm = password_editor.password_confirm

        app_uid = self.query_one("#core-app_uid", expect_type=Input).value.strip()
        username = self.query_one("#core-app_username", expect_type=Input).value.strip()

        if password:
            # May start the key derivation worker; saving then continues in
            # on_key_derivation_result.
            self._handle_new_password_flow(
                password,
                password_confirm,
                app_uid,
                username,
                existing_keys,
            )
            return
        if not existing_keys:
            self._fail(
                "Achtung: Kein Verschlüsselungsschlüssel gesetzt. "
                "Bitte legen Sie ein Passwort fest.",
            )
            return  # Prevent saving without any keys
        if all(check_key_validity(k) for k in existing_keys):
            self.notify(
                "Die bestehenden, gültigen Verschlüsselungsschlüssel werden verwendet.",
                severity="information",
            )
            self._start_save()
        else:
            self._fail(
                "Achtung: Einer oder mehrere der vorhandenen Schlüssel sind "
                "ungültig. Bitte Passwort erneut eingeben, um einen neuen, "
                "gültigen Schlüssel zu erstellen.",
            )

    def _handle_new_password_flow(
        self,
        password: str,
        password_confirm: str,
        app_uid: str,
        username: str,
        existing_keys: list[bytes],
    ) -> None:
        """Handle a newly entered password, performing key rotation if needed.

        If a valid key already exists, the user is asked for confirmation
        first. The dialog result is delivered through a callback, because
        awaiting ``push_screen`` outside a worker only waits for the mount.

        :param password: The new password.
        :param password_confirm: The repeated password.
        :param app_uid: Keyring service name.
        :param username: Keyring user name.
        :param existing_keys: Keys currently stored in the keyring.
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            self._fail(
                f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein",
            )
            return

        if password != password_confirm:
            self._fail("Passwörter stimmen nicht überein")
            return

        if existing_keys:
            if all(check_key_validity(k) for k in existing_keys):

                def on_confirm(confirmed: bool | None) -> None:
                    if not confirmed:
                        self.screen.loading = False
                        self.notify(
                            "Speichern abgebrochen. "
                            "Die Schlüssel wurden nicht geändert.",
                            severity="warning",
                        )
                        return
                    self._start_key_derivation(
                        password,
                        app_uid,
                        username,
                        existing_keys,
                    )  # turns loading on
                    self.screen.loading = False

                self.push_screen(
                    YesNoDialog(
                        "Ein gültiger Schlüssel existiert bereits. "
                        "Möchten Sie einen neuen Schlüssel hinzufügen und rotieren?",
                    ),
                    on_confirm,
                )
                return

            self.notify(
                "Ein oder mehrere existierende Schlüssel sind ungültig "
                "und werden durch den neuen ersetzt.",
                severity="error",
            )
            existing_keys.clear()  # Clear invalid keys
            self.bell()

        self._start_key_derivation(password, app_uid, username, existing_keys)

    def _start_key_derivation(
        self,
        password: str,
        app_uid: str,
        username: str,
        existing_keys: list[bytes],
    ) -> None:
        """Show the loading state and start the key derivation worker.

        :param password: The new password.
        :param app_uid: Keyring service name.
        :param username: Keyring user name.
        :param existing_keys: Valid keys to keep next to the new one.
        """
        self.screen.loading = True  # show spinner
        self.notify("Neuer Verschlüsselungsschlüssel wird generiert...")
        kdf_iterations_value = self.query_one(
            "#core-kdf_iterations",
            expect_type=Input,
        ).value.strip()
        self._key_derivation_worker(
            password,
            self.database_url,
            app_uid,
            username,
            existing_keys,
            kdf_iterations_value,
        )

    def _start_save(self) -> None:
        """Rebuild the config from the UI and start the save worker."""
        self.screen.loading = True  # show spinner
        try:
            self.config_dict = self._rebuild_config_from_ui()
        except ValueError as e:
            self._fail(f"Konfiguration konnte nicht gelesen werden: {e}")
            return
        self._save_config_worker(self.config_dict, self.config_path)

    async def action_save(self) -> None:
        """Validate the UI, then start the save process."""
        if self.screen.loading:
            return
        self.clear_log()
        if not self._validate_inputs_for_save():
            return

        app_uid = self.query_one("#core-app_uid", expect_type=Input).value.strip()
        username = self.query_one("#core-app_username", expect_type=Input).value.strip()

        password = self.query_one(
            "#password-section", expect_type=PasswordEditor
        ).password
        identity_changed = (app_uid, username) != self._loaded_identity
        if not password and not identity_changed:
            self._start_save()  # sets screen.loading = True
            return

        self.screen.loading = True  # show spinner for get_keys
        self._get_keys_worker(app_uid, username)

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

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
        except Exception as e:  # noqa: BLE001
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
        except Exception as e:  # noqa: BLE001
            self.log(f"Error getting keys: {e}")
            self.call_from_thread(self._fail, f"Fehler beim Laden der Schlüssel: {e}")

    @work(thread=True)
    def _save_config_worker(self, config_dict: dict[str, Any], file_path: Path) -> None:
        try:
            save_config(config_dict, file_path)
            self.post_message(ConfigSaved())
        except Exception as e:  # noqa: BLE001
            self.log(f"Error saving config: {e}")
            self.call_from_thread(
                self._fail,
                f"Fehler beim Speichern der Konfiguration: {e}",
            )

    @on(KeyDerivationResult)
    async def on_key_derivation_result(self, message: KeyDerivationResult) -> None:
        """Handles the KeyDerivationResult message."""
        if not message.success:
            self._fail(message.message)
            return
        self.notify(message.message, severity="information", markup=False)
        self._start_save()

    @on(ConfigSaved)
    async def on_config_saved(self, message: ConfigSaved) -> None:
        """Handles the ConfigSaved message."""
        self.screen.loading = False
        self.exit()

    async def action_quit(self) -> None:
        self.exit()
