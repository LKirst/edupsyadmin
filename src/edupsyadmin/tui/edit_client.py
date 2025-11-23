from datetime import date
from typing import Any, ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message
from textual.validation import Function, Regex
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    RichLog,
    Static,
)

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
HIDDEN_FIELDS = [
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
]


def _is_school_key(value: str) -> bool:
    return value in config.school


def _is_lrst_diag(value: str) -> bool:
    return value in LRST_DIAG


def _is_test_by_value(value: str) -> bool:
    return value in LRST_TEST_BY


class InputRow(Horizontal):
    """A widget to display a label and an input field."""

    def __init__(self, label: str, widget: Input) -> None:
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
        margin-bottom: 1;
    }
    .label {
        width: 1fr;
        height: 3;
        content-align: right middle;
        margin-right: 1;
    }
    InputRow > Input {
        width: 2fr;
    }
    CheckboxRow {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
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
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.client_id: int | None = None
        self._original_data: dict[str, str | bool] = {}
        self._changed_data: dict[str, Any] = {}
        self.inputs: dict[str, Input] = {}
        self.dates: dict[str, Input] = {}
        self.checkboxes: dict[str, Checkbox] = {}
        self.save_button: Button | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="edit-client-form"):
            yield Static(
                "Klient*in aus der Liste auswählen oder neue*n anlegen.",
                id="placeholder",
            )
        yield RichLog(classes="log", id="edit-client-log")

    def _clear_form(self) -> None:
        form = self.query_one("#edit-client-form", VerticalScroll)
        form.query("*").remove()
        self.query_one("#edit-client-log", RichLog).clear()
        self.inputs.clear()
        self.dates.clear()
        self.checkboxes.clear()
        self.save_button = None

    def update_client(self, client_id: int | None, data: dict[str, Any] | None) -> None:
        self._clear_form()

        self.client_id = client_id
        data = data or _get_empty_client_dict()
        self._original_data: dict[str, str | bool] = {}

        for key, value in data.items():
            if value is None:
                self._original_data[key] = ""
            elif isinstance(value, date):
                self._original_data[key] = value.isoformat()
            elif isinstance(value, bool | str):  # check this before checking if int!
                self._original_data[key] = value
            elif isinstance(value, int | float):
                self._original_data[key] = str(value)
        self._changed_data: dict[str, Any] = {}

        form = self.query_one("#edit-client-form", VerticalScroll)

        if self.client_id:
            form.mount(Static(f"Daten für client_id: {self.client_id}"))
        else:
            form.mount(Static("Daten für einen neuen Klienten"))

        for column in Client.__table__.columns:
            field_type = get_python_type(column.type)
            name = column.name
            if name in HIDDEN_FIELDS:
                continue

            label_text = name + "*" if (name in REQUIRED_FIELDS) else name

            # checkbox widgets
            if field_type is bool:
                bool_value = self._original_data.get(name)
                bool_default = bool_value if isinstance(bool_value, bool) else False
                checkbox = Checkbox(label=name, value=bool_default, id=f"{name}")
                checkbox.tooltip = column.doc
                self.checkboxes[name] = checkbox
                form.mount(CheckboxRow(checkbox))
                continue

            # input widgets
            default = str(self._original_data.get(name, ""))
            placeholder = "Erforderlich" if name in REQUIRED_FIELDS else ""
            valid_empty = name not in REQUIRED_FIELDS
            input_widget: Input
            if field_type is int:
                input_widget = Input(
                    value=default,
                    placeholder=placeholder,
                    type="integer",
                    valid_empty=valid_empty,
                )
            elif field_type is float:
                valid_empty = name not in REQUIRED_FIELDS
                input_widget = Input(
                    value=default,
                    placeholder=placeholder,
                    type="number",
                    valid_empty=valid_empty,
                )
            elif (field_type is date) or (
                name in {"birthday_encr", "lrst_last_test_date_encr"}
            ):
                input_widget = Input(
                    value=default,
                    placeholder="JJJJ-MM-TT",
                    restrict=r"[\d-]*",
                    validators=Regex(
                        r"\d{4}-[0-1]\d-[0-3]\d",
                        failure_description=("Daten müssen im Format YYYY-mm-dd sein."),
                    ),
                    valid_empty=valid_empty,
                )
                self.dates[name] = input_widget
            elif name in {"school", "lrst_diagnosis_encr", "lrst_last_test_by_encr"}:
                validator: Function
                if name == "school":
                    validator = Function(
                        _is_school_key,
                        failure_description=(
                            "Der Wert für `school` entspricht keinem Wert "
                            "aus der Konfiguration"
                        ),
                    )
                elif name == "lrst_diagnosis_encr":
                    validator = Function(
                        _is_lrst_diag,
                        failure_description=(
                            f"Der Wert für `lrst_diagnosis_encr` muss "
                            f"einer der folgenden sein: {LRST_DIAG}"
                        ),
                    )
                else:
                    validator = Function(
                        _is_test_by_value,
                        failure_description=(
                            f"Der Wert für `lrst_last_test_by_encr` muss "
                            f"einer der folgenden sein: {LRST_TEST_BY}"
                        ),
                    )
                input_widget = Input(
                    value=default,
                    placeholder=placeholder,
                    validators=[validator],
                    valid_empty=valid_empty,
                )
            else:
                input_widget = Input(value=default, placeholder=placeholder)

            input_widget.id = f"{name}"
            if name not in self.dates:
                self.inputs[name] = input_widget

            row = InputRow(f"{label_text}:", input_widget)
            row.tooltip = column.doc
            form.mount(row)

        self.save_button = Button(label="Speichern", id="save", variant="success")
        form.mount(
            Horizontal(
                self.save_button,
                Button("Abbrechen", id="cancel", variant="error"),
                classes="action-buttons",
            )
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            await self.action_save()
        elif event.button.id == "cancel":
            await self.action_cancel()

    async def action_save(self) -> None:
        log = self.query_one("#edit-client-log", RichLog)
        log.clear()
        all_inputs = list(self.inputs.values()) + list(self.dates.values())

        # Check for empty required fields
        required_fields_empty = False
        for field_name in REQUIRED_FIELDS:
            widget = self.inputs.get(field_name) or self.dates.get(field_name)
            if widget and not widget.value.strip():
                required_fields_empty = True

        # Check if all inputs are valid according to their validators
        all_widgets_valid = all(widget.is_valid for widget in all_inputs)

        # If any validation fails, notify user and stop
        if required_fields_empty or not all_widgets_valid:
            # Trigger validation display on all inputs to show which ones are invalid
            for widget in all_inputs:
                if not widget.is_valid:
                    widget.remove_class("-valid")
                    widget.add_class("-invalid")
                else:
                    widget.remove_class("-invalid")
                    widget.add_class("-valid")
            log.write(
                "Bitte alle Pflichtfelder (*) ausfüllen und auf "
                "korrekte Formate achten."
            )
            return

        # Proceed with saving if validation passed
        current: dict[str, str | bool] = {}
        current.update({n: w.value for n, w in {**self.inputs, **self.dates}.items()})
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
    for column in Client.__table__.columns:
        field_type = get_python_type(column.type)
        name = column.name

        if field_type is bool:
            empty_client_dict[name] = False
        else:
            empty_client_dict[name] = ""
    return empty_client_dict
