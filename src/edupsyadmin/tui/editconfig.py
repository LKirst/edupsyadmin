from pathlib import Path
from typing import Any, Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import Function, Regex
from textual.widgets import Button, Input, Select, Static

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
    "template_directory": "Standardordner für Formularvorlagen",
    "output_directory": "Standardordner für ausgefüllte Formulare",
}

NoPeriodValidator = Regex(
    regex=r"^(?!.*\.).*$",
    failure_description="Darf keine Punkte enthalten",
)

PathIsFileValidator = Function(
    function=lambda value: Path(value).expanduser().is_file(),
    failure_description="Pfad ist keine Datei.",
)

PathIsDirValidator = Function(
    function=lambda value: Path(value).expanduser().is_dir(),
    failure_description="Pfad ist kein Ordner.",
)


class DeleteItemButton(Button):
    """A button that removes its parent widget when pressed."""

    def __init__(self) -> None:
        super().__init__("Löschen", variant="error", classes="delete-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        parent = self.parent
        if isinstance(parent, Vertical):
            parent.remove()


class ConfigInput(Horizontal):
    """A row containing a label and an input field for configuration."""

    def __init__(
        self,
        key: str,
        value: str | int | None,
        id: str | None = None,
        validators: list | None = None,
        valid_empty: bool | None = None,
        password: bool = False,
        placeholder: str | None = None,
    ) -> None:
        super().__init__(classes="input-container")
        self.key = key
        self.value = value
        self.row_id = id
        self.validators = validators
        self.valid_empty = valid_empty
        self.password = password
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        label = Static(f"{self.key}:", classes="label")
        label.tooltip = TOOLTIPS.get(self.key, "")
        yield label

        display_value = str(self.value) if self.value is not None else ""
        inp_type: Literal["integer", "text"] = (
            "integer" if self.key in ("kdf_iterations", "end", "nstudents") else "text"
        )
        # Use provided valid_empty or default based on key
        if self.valid_empty is not None:
            valid_empty = self.valid_empty
        else:
            valid_empty = self.key == "kdf_iterations"

        inp = Input(
            display_value,
            id=self.row_id or self.key,
            placeholder=self.placeholder or self.key,
            type=inp_type,
            valid_empty=valid_empty,
            validators=self.validators or [],
            password=self.password,
        )
        inp.tooltip = TOOLTIPS.get(self.key, "")
        yield inp


class PasswordEditor(Vertical):
    """A widget to edit password settings."""

    def compose(self) -> ComposeResult:
        yield Static("Passwort", classes="section-header")
        yield ConfigInput(
            key="Neues Passwort",
            value="",
            id="password",
            valid_empty=True,
            password=True,
            placeholder="Leer lassen, falls schon ein Passwort festgelegt wurde",
        )
        yield ConfigInput(
            key="Passwort bestätigen",
            value="",
            id="password_confirm",
            valid_empty=True,
            password=True,
            placeholder="Passwort wiederholen",
        )

    @property
    def password(self) -> str:
        return self.query_one("#password", Input).value

    @property
    def password_confirm(self) -> str:
        return self.query_one("#password_confirm", Input).value


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
                yield ConfigInput(key, value=self._school_data[key])
        yield DeleteItemButton()

    def get_data(self) -> tuple[str | None, dict[str, Any] | None]:
        key = self.query_one("#item_key", Input).value
        if not key:
            return None, None
        data = {}
        for inp in self.query(Input):
            if inp.id and inp.id != "item_key":
                if inp.type == "integer":
                    val = int(inp.value) if inp.value else None
                else:
                    val = inp.value
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
                    path,
                    classes="path-input",
                    validators=[PathIsFileValidator],
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
        default_value = current_separator or "\t"
        option_values = [opt[1] for opt in separator_options]
        if current_separator and current_separator not in option_values:
            separator_options.append(
                (f"Custom ('{current_separator}')", current_separator),
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
        for key in ("Rosenkohl", "Laufbursche", "Toechter"):
            yield ConfigInput(
                key,
                value=self._lgvt_data.get(key, ""),
                id=f"lgvt-{key}",
                validators=[PathIsFileValidator],
                valid_empty=True,
            )

    def get_data(self) -> dict[str, str | None]:
        data = {}
        for key in ("Rosenkohl", "Laufbursche", "Toechter"):
            inp = self.query_one(f"#lgvt-{key}", Input)
            data[key] = inp.value or None
        return data
