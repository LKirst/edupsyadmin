from datetime import date
from typing import Any, ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message
from textual.validation import Regex
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    RichLog,
    Select,
    Static,
)
from textual.widgets._select import NoSelection

from edupsyadmin.core.config import config
from edupsyadmin.core.python_type import get_python_type
from edupsyadmin.db.clients import LRST_DIAG, LRST_TEST_BY, Client

REQUIRED_FIELDS = [
    "school",
    "gender_encr",
    "class_name",
    "first_name_encr",
    "last_name_encr",
    "birthday_encr",
]

# fields which depend on other fields and should not be set by the user
HIDDEN_FIELDS = {
    "class_int",
    "estimated_graduation_date",
    "document_shredding_date",
    "datetime_created",
    "datetime_lastmodified",
    "notenschutz",
    "nos_rs_ausn",
    "nos_other",
    "nachteilsausgleich",
    "nta_zeitv",
    "nta_other",
    "nta_nos_end",
}

DATE_FIELDS = {"birthday_encr", "lrst_last_test_date_encr"}
DATE_REGEX = r"\d{4}-[0-1]\d-[0-3]\d"


def _to_str_or_bool(value: None | date | bool | str | int | float) -> str | bool | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool | str):  # check this before checking if int!
        return value
    if isinstance(value, int | float):
        return str(value)
    return str(value)


class InputRow(Horizontal):
    """A widget to display a label and an input field."""

    def __init__(self, label: str, widget: Input | Select) -> None:
        super().__init__()
        self.label = Static(label, classes="label")
        self.widget = widget

    def compose(self) -> ComposeResult:
        yield self.label
        yield self.widget


class CheckboxRow(Horizontal):
    """A widget to display a spacer and a checkbox."""

    def __init__(self, widget: Checkbox) -> None:
        super().__init__()
        self.spacer = Static(classes="spacer")
        self.widget = widget

    def compose(self) -> ComposeResult:
        yield self.spacer
        yield self.widget


class EditClient(Container):
    DEFAULT_CSS = """
    InputRow {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-bottom: 0;
    }
    .label {
        width: 1fr;
        height: 3;
        content-align: right middle;
        margin-right: 1;
    }
    InputRow > Input, Select {
        width: 2fr;
    }
    CheckboxRow {
        layout: horizontal;
        height: auto;
        margin-bottom: 0;
    }
    CheckboxRow > .spacer {
        width: 1fr;
        margin-right: 1;
    }
    CheckboxRow > Checkbox {
        width: 2fr;
    }
    #edit-client-form {
        height: 1fr;
    }
    #edit-client-log {
        height: 5;
    }
    .action-buttons {
        height: 3;
    }
    .action-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("escape", "cancel", "Abbrechen", show=True),
    ]

    class SaveClient(Message):
        def __init__(self, client_id: int | None, data: dict[str, Any]) -> None:
            self.client_id = client_id
            self.data = data
            super().__init__()

    # TODO: Implement CancelEdit message?
    class CancelEdit(Message): ...

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.client_id: int | None = None
        self._original_data: dict[str, str | bool | None] = {}
        self._changed_data: dict[str, str | bool | None] = {}
        self.inputs: dict[str, Input | Select] = {}
        self.dates: dict[str, Input] = {}
        self.checkboxes: dict[str, Checkbox] = {}
        self.save_button: Button | None = None
        self.choice_fields: dict[str, list[tuple[str, str]]] = {
            "school": [(k, k) for k in config.school],
            "lrst_diagnosis_encr": [(v, v) for v in LRST_DIAG],
            "lrst_last_test_by_encr": [(v, v) for v in LRST_TEST_BY],
        }

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="edit-client-form"):
            yield Static(
                "Klient*in aus der Liste auswählen oder neue*n anlegen.",
                id="edit-client-header",
            )
            # Build rows
            for db_column in self._visible_db_columns():
                name = db_column.name
                field_type = get_python_type(db_column.type)
                required = self._is_required(name)
                label_text = f"{name}*" if required else name
                default = ""

                widget = self._build_field_widget(
                    name=name,
                    field_type=field_type,
                    default=default,
                    required=required,
                    tooltip=db_column.doc,
                )
                self._register_widget(name, widget)

                # Keep the original row layout choices
                if isinstance(widget, Checkbox):
                    yield CheckboxRow(widget)
                else:
                    yield InputRow(f"{label_text}:", widget)

            # Actions
            self.save_button = Button(label="Speichern", id="save", variant="success")
            yield Horizontal(
                self.save_button,
                Button("Abbrechen", id="cancel", variant="error"),
                classes="action-buttons",
            )
        yield RichLog(classes="log", id="edit-client-log")

    def _normalize_original_data(
        self, data: dict[str, Any]
    ) -> dict[str, str | bool | None]:
        return {k: _to_str_or_bool(v) for k, v in data.items()}

    def _visible_db_columns(self):
        for db_column in Client.__table__.columns:
            if db_column.name not in HIDDEN_FIELDS:
                yield db_column

    def _is_required(self, name: str) -> bool:
        return name in REQUIRED_FIELDS

    def _register_widget(self, name: str, widget: Checkbox | Input | Select) -> None:
        if isinstance(widget, Checkbox):
            self.checkboxes[name] = widget
        elif isinstance(widget, Input):
            if (name in DATE_FIELDS) or (
                get_python_type(Client.__table__.columns[name].type) is date
            ):
                self.dates[name] = widget
            else:
                self.inputs[name] = widget
        elif isinstance(widget, Select):
            # Treat Select like other inputs for save/compare purposes
            self.inputs[name] = widget
        else:
            self.inputs[name] = widget  # fallback

    def _build_field_widget(
        self,
        name: str,
        field_type: type,
        default: str | bool | None,
        required: bool,
        tooltip: str | None,
    ) -> Checkbox | Select | Input:
        widget: Checkbox | Select[Any] | Input
        # Booleans -> Checkbox
        if field_type is bool:
            widget = Checkbox(
                label=name,
                value=bool(default) if isinstance(default, bool) else False,
                id=name,
            )

        # Choice fields -> Select
        elif name in self.choice_fields:
            options = self.choice_fields[name]
            # Determine the initial value before creating the widget
            initial_value: object = Select.BLANK
            if isinstance(default, str):
                stripped_default = default.strip()
                if stripped_default and any(stripped_default == v for v, _ in options):
                    initial_value = stripped_default

            widget = Select(
                options=options,
                id=name,
                prompt="Auswählen ...",
                allow_blank=(not required),
                value=initial_value,
            )

        # Dates -> Input with shared config
        elif field_type is date or name in DATE_FIELDS:
            widget = Input(
                value=str(default or ""),
                placeholder="JJJJ-MM-TT",
                restrict=r"[\d-]*",
                validators=Regex(
                    DATE_REGEX,
                    failure_description="Daten müssen im Format YYYY-mm-dd sein.",
                ),
                valid_empty=not required,
                id=name,
            )

        # Numbers
        elif field_type is int:
            widget = Input(
                value=str(default or ""),
                placeholder="Erforderlich" if required else "",
                type="integer",
                valid_empty=not required,
                id=name,
            )
        elif field_type is float:
            widget = Input(
                value=str(default or ""),
                placeholder="Erforderlich" if required else "",
                type="number",
                valid_empty=not required,
                id=name,
            )

        # Fallback = plain text
        else:
            widget = Input(
                value=str(default or ""),
                placeholder="Erforderlich" if required else "",
                valid_empty=not required,
                id=name,
            )

        # Attach tooltip uniformly
        widget.tooltip = tooltip
        return widget

    def update_client(self, client_id: int | None, data: dict[str, Any] | None) -> None:
        self.client_id = client_id
        data = data or _get_empty_client_dict()

        self._original_data = self._normalize_original_data(data)
        self._changed_data = {}

        header = self.query_one("#edit-client-header", Static)
        if self.client_id:
            header.update(f"Daten für client_id: {self.client_id}")
        else:
            header.update("Daten für einen neuen Klienten")

        # Update widget values
        for name, widget in {**self.inputs, **self.dates}.items():
            value = self._original_data.get(name)
            if isinstance(widget, Select):
                if value:
                    widget.value = value
                elif not self._is_required(name):
                    widget.clear()
            else:
                widget.value = str(value) if value is not None else ""

        for name, widget in self.checkboxes.items():
            value = self._original_data.get(name)
            widget.value = bool(value)

        self.query_one("#edit-client-log", RichLog).clear()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            await self.action_save()
        elif event.button.id == "cancel":
            await self.action_cancel()

    def _validate_inputs_for_save(self) -> bool:
        """Check all inputs and log errors if validation fails."""
        log = self.query_one("#edit-client-log", RichLog)
        all_inputs = list(self.inputs.values()) + list(self.dates.values())

        # Check for empty required fields
        required_fields_empty = False
        for field_name in REQUIRED_FIELDS:
            widget = self.inputs.get(field_name) or self.dates.get(field_name)
            if not widget:
                continue
            value = widget.value
            if value is None or (isinstance(value, str) and not value.strip()):
                required_fields_empty = True

        # Check if all inputs are valid according to their validators
        all_widgets_valid = all(
            widget.is_valid for widget in all_inputs if isinstance(widget, Input)
        )

        if required_fields_empty or not all_widgets_valid:
            # Trigger validation display on all inputs to show which ones are invalid
            for widget in all_inputs:
                is_w_valid = True
                if isinstance(widget, Input):
                    is_w_valid = widget.is_valid
                # Select widgets are considered valid here, as their requirement
                # is checked separately.
                if not is_w_valid:
                    widget.remove_class("-valid")
                    widget.add_class("-invalid")
                else:
                    widget.remove_class("-invalid")
                    widget.add_class("-valid")
            log.write(
                "Bitte alle Pflichtfelder (*) ausfüllen und auf "
                "korrekte Formate achten."
            )
            return False
        return True

    async def action_save(self) -> None:
        log = self.query_one("#edit-client-log", RichLog)
        log.clear()

        if not self._validate_inputs_for_save():
            return

        # Proceed with saving if validation passed
        current: dict[str, str | bool | None] = {}

        # Handle inputs and dates
        for name, widget in {**self.inputs, **self.dates}.items():
            if isinstance(widget, Select):
                # TODO: Do I need to check for BLANK and NoSelection?
                value = widget.value
                if (
                    value is None
                    or value == Select.BLANK
                    or isinstance(value, NoSelection)
                ):
                    current[name] = None
                else:
                    current[name] = value
            else:
                # For Input: keep as string (empty string if None)
                current[name] = widget.value if widget.value is not None else ""

        # Handle checkboxes
        current.update({n: cb.value for n, cb in self.checkboxes.items()})

        self._changed_data = {
            key: value
            for key, value in current.items()
            if value != self._original_data.get(key)
        }
        self.post_message(self.SaveClient(self.client_id, self._changed_data))

    @on(Input.Blurred)
    def check_for_validation(self, event: Input.Blurred) -> None:
        if event.validation_result and event.validation_result.failure_descriptions:
            log_widget = self.query_one("#edit-client-log", RichLog)
            log_widget.write(event.validation_result.failure_descriptions)

    async def action_cancel(self) -> None:
        self.post_message(self.CancelEdit())


def _get_empty_client_dict() -> dict[str, str | bool]:
    empty_client_dict: dict[str, str | bool] = {}
    for db_column in Client.__table__.columns:
        field_type = get_python_type(db_column.type)
        name = db_column.name

        if field_type is bool:
            empty_client_dict[name] = False
        else:
            empty_client_dict[name] = ""
    return empty_client_dict
