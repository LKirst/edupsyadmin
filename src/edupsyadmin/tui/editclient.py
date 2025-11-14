from datetime import date
from typing import Any, ClassVar

from textual import log, on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.validation import Function, Regex
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
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


class StudentEntryApp(App[dict[str, Any] | None]):
    CSS_PATH = "editclient.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", "save", "Speichern", show=True),
        Binding("ctrl+q", "quit", "Abbrechen", show=True),
    ]

    def __init__(
        self, client_id: int | None = None, data: dict[str, Any] | None = None
    ):
        super().__init__()

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

        self.client_id = client_id
        if self.client_id:
            self.title = f"Daten für client_id: {self.client_id}"
        else:
            self.title = "Daten für einen neuen Klienten"
        self.inputs: dict[str, Input] = {}
        self.dates: dict[str, Input] = {}
        self.checkboxes: dict[str, Checkbox] = {}
        self.save_button: Button  # Initialized in compose

    def compose(self) -> ComposeResult:
        yield Header()

        # Read fields from the clients table
        log.debug(f"columns in Client.__table__.columns: {Client.__table__.columns}")
        for column in Client.__table__.columns:
            field_type = get_python_type(column.type)
            name = column.name
            if name in HIDDEN_FIELDS:
                continue

            label_text = name + "*" if (name in REQUIRED_FIELDS) else name

            # checkboxes
            if field_type is bool:
                bool_value = self._original_data.get(name)
                bool_default = bool_value if isinstance(bool_value, bool) else False
                with Horizontal(classes="checkbox-container"):
                    yield Static(classes="spacer")
                    checkbox = Checkbox(label=name, value=bool_default)
                    self.checkboxes[name] = checkbox
                    # add tooltip
                    checkbox.tooltip = column.doc
                    checkbox.id = f"{name}"
                    yield checkbox
                continue

            with Horizontal(classes="input-container"):
                label_widget = Static(f"{label_text}:", classes="label")
                label_widget.tooltip = column.doc
                yield label_widget

                # input widgets
                default = (
                    str(self._original_data[name])
                    if name in self._original_data
                    else ""
                )

                placeholder = "Erforderlich" if name in REQUIRED_FIELDS else ""

                if field_type is int:
                    input_widget = Input(
                        value=default,
                        placeholder=placeholder,
                        type="integer",
                        valid_empty=True,
                    )
                    self.inputs[name] = input_widget
                elif field_type is float:
                    input_widget = Input(
                        value=default,
                        placeholder=placeholder,
                        type="number",
                        valid_empty=True,
                    )
                    self.inputs[name] = input_widget
                elif (field_type is date) or (
                    name in {"birthday_encr", "lrst_last_test_date_encr"}
                ):
                    input_widget = Input(
                        value=default,
                        placeholder="JJJJ-MM-TT",
                        restrict=r"[\d-]*",
                        validators=Regex(
                            r"\d{4}-[0-1]\d-[0-3]\d",
                            failure_description=(
                                "Daten müssen im Format YYYY-mm-dd sein."
                            ),
                        ),
                        valid_empty=True,
                    )
                    self.dates[name] = input_widget
                elif name in {
                    "school",
                    "lrst_diagnosis_encr",
                    "lrst_last_test_by_encr",
                }:
                    if name == "school":
                        validator = Function(
                            _is_school_key,
                            failure_description=(
                                "Der Wert für `school` entspricht keinem "
                                "Wert aus der Konfiguration"
                            ),
                        )
                        valid_empty = False
                    elif name == "lrst_diagnosis_encr":
                        validator = Function(
                            _is_lrst_diag,
                            failure_description=(
                                f"Der Wert für `lrst_diagnosis_encr` muss einer "
                                f"der folgenden sein: {LRST_DIAG}"
                            ),
                        )
                        valid_empty = True
                    else:
                        validator = Function(
                            _is_test_by_value,
                            failure_description=(
                                f"Der Wert für `lrst_last_test_by_encr` muss einer "
                                f"der folgenden sein: {LRST_TEST_BY}"
                            ),
                        )
                        valid_empty = True

                    input_widget = Input(
                        value=default,
                        placeholder=placeholder,
                        validators=[validator],
                        valid_empty=valid_empty,
                    )
                    self.inputs[name] = input_widget
                else:
                    input_widget = Input(value=default, placeholder=placeholder)
                    self.inputs[name] = input_widget

                input_widget.id = f"{name}"

                if name not in self.dates:
                    self.inputs[name] = input_widget

                yield input_widget

        # Submit button
        self.save_button = Button(label="Speichern", id="save", variant="success")
        yield Horizontal(
            self.save_button,
            Button("Abbrechen", id="cancel", variant="error"),
            classes="action-buttons",
        )

        # For failures of input validation
        yield RichLog(classes="log")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            await self.action_save()
        elif event.button.id == "cancel":
            await self.action_quit()

    async def action_save(self) -> None:
        # build snapshot from widgets
        current: dict[str, str | bool] = {}
        current.update({n: w.value for n, w in {**self.inputs, **self.dates}.items()})
        current.update({n: cb.value for n, cb in self.checkboxes.items()})

        required_field_empty = any(current.get(f, "") == "" for f in REQUIRED_FIELDS)

        # validation
        school_valid = self.query_one("#school", Input).is_valid
        lrst_diag_valid = self.query_one("#lrst_diagnosis_encr", Input).is_valid
        dates_valid = all(widget.is_valid for widget in self.dates.values())

        if (
            required_field_empty
            or not dates_valid
            or not school_valid
            or not lrst_diag_valid
        ):
            # mark required fields that are still empty
            for f in REQUIRED_FIELDS:
                if current.get(f, "") == "":
                    self.query_one(f"#{f}", Input).add_class("-invalid")
        else:
            # find fields that changed
            self._changed_data = {
                key: value
                for key, value in current.items()
                if value != self._original_data.get(key)
            }

            self.exit(self._changed_data)  # Exit the app after submission

    @on(Input.Blurred)
    def check_for_validation(self, event: Input.Blurred) -> None:
        if event.validation_result:
            log = self.query_one(RichLog)
            log.write(event.validation_result.failure_descriptions)

    async def action_quit(self) -> None:
        self.exit(None)


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
