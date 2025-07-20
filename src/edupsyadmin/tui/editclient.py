from datetime import date

from textual import log, on
from textual.app import App
from textual.validation import Function, Regex
from textual.widgets import Button, Checkbox, Input, Label, RichLog

from edupsyadmin.core.config import config
from edupsyadmin.core.python_type import get_python_type
from edupsyadmin.db.clients import Client

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


def _is_school_key(value: str):
    return value in config["school"]


class StudentEntryApp(App):
    def __init__(self, client_id: int | None = None, data: dict | None = None):
        super().__init__()

        data = data or _get_empty_client_dict()
        self._original_data = {}

        for key, value in data.items():
            if value is None:
                self._original_data[key] = ""
            elif isinstance(value, date):
                self._original_data[key] = value.isoformat()
            elif isinstance(value, bool | str):  # check this before checking if int!
                self._original_data[key] = value
            elif isinstance(value, int | float):
                self._original_data[key] = str(value)
        self._changed_data = {}

        self.client_id = client_id
        self.inputs = {}
        self.dates = {}
        self.checkboxes = {}

    def compose(self):
        # Create heading with client_id
        if self.client_id:
            yield Label(f"Daten für client_id: {self.client_id}")
        else:
            yield Label("Daten für einen neuen Klienten")

        # Read fields from the clients table
        log.debug(f"columns in Client.__table__.columns: {Client.__table__.columns}")
        for column in Client.__table__.columns:
            field_type = get_python_type(column.type)
            name = column.name
            if name in HIDDEN_FIELDS:
                continue

            # default value
            if field_type is bool:
                default = self._original_data.get(name, False)
            else:
                default = (
                    str(self._original_data[name])
                    if name in self._original_data
                    else ""
                )

            # create widget
            placeholder = name + "*" if (name in REQUIRED_FIELDS) else name
            if field_type is bool:
                widget = Checkbox(label=name, value=default)
                self.checkboxes[name] = widget
            elif field_type is int:
                widget = Input(
                    value=default,
                    placeholder=placeholder,
                    type="integer",
                    valid_empty=True,
                )
                self.inputs[name] = widget
            elif field_type is float:
                widget = Input(
                    value=default,
                    placeholder=placeholder,
                    type="number",
                    valid_empty=True,
                )
                self.inputs[name] = widget
            elif (field_type is date) or (name == "birthday_encr"):
                widget = Input(
                    value=default,
                    placeholder=placeholder,
                    restrict=r"[\d-]*",
                    validators=Regex(
                        r"\d{4}-[0-1]\d-[0-3]\d",
                        failure_description="Daten müssen im Format YYYY-mm-dd sein.",
                    ),
                    valid_empty=True,
                )
                self.dates[name] = widget
            elif name == "school":
                widget = Input(
                    value=default,
                    placeholder=placeholder,
                    validators=[
                        Function(
                            _is_school_key,
                            failure_description=(
                                "Der Wert für `school` entspricht keinem "
                                "Wert aus der Konfiguration"
                            ),
                        )
                    ],
                )
                self.inputs[name] = widget
            else:
                widget = Input(value=default, placeholder=placeholder)
                self.inputs[name] = widget

            # add tooltip
            widget.tooltip = column.doc
            widget.id = f"{name}"

            yield widget

        # For failures of input validation
        yield RichLog()

        # Submit button
        self.submit_button = Button(label="Submit", id="Submit")
        yield self.submit_button

    def on_button_pressed(self):
        """method that is called when the submit button is pressed"""

        # build snapshot from widgets
        current: dict[str, object] = {}
        current.update({n: w.value for n, w in {**self.inputs, **self.dates}.items()})
        current.update({n: cb.value for n, cb in self.checkboxes.items()})

        required_field_empty = any(current.get(f, "") == "" for f in REQUIRED_FIELDS)

        # validation
        school_valid = self.query_one("#school").is_valid
        dates_valid = all(widget.is_valid for widget in self.dates.values())

        if required_field_empty or not dates_valid or not school_valid:
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

            self.exit()  # Exit the app after submission

    @on(Input.Blurred)
    def check_for_validation(self, event: Input.Blurred) -> None:
        if event.validation_result:
            log = self.query_one(RichLog)
            log.write(event.validation_result.is_valid)
            log.write(event.validation_result.failure_descriptions)

    def get_data(self):
        return self._changed_data


def _get_empty_client_dict() -> dict[str, any]:
    empty_client_dict = {}
    for column in Client.__table__.columns:
        field_type = get_python_type(column.type)
        name = column.name

        if field_type is bool:
            empty_client_dict[name] = False
        else:
            empty_client_dict[name] = ""
    return empty_client_dict
