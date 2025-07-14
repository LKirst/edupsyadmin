from datetime import date

from textual import log
from textual.app import App
from textual.events import Key
from textual.widgets import Button, Checkbox, Input, Label

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


class DateInput(Input):
    """A custom input widget that accepts dates as YYYY-MM-DD."""

    def on_key(self, event: Key) -> None:
        """Handle key press events to enforce date format."""
        # Allow navigation and control keys
        if event.key in {"backspace", "delete", "left", "right", "home", "end"}:
            return

        # Allow digits and dashes at the correct positions
        if event.character and (event.character.isdigit() or event.character == "-"):
            current_text = self.value

            # Check the current length and position of the input
            if len(current_text) < 10:  # YYYY-MM-DD has 10 characters
                if event.character == "-":
                    # Allow dashes only at the 5th and 8th positions
                    if len(current_text) in {4, 7}:
                        return
                    event.prevent_default()
                else:
                    return  # Allow digits
            else:
                event.prevent_default()  # Prevent input if length exceeds 10
        else:
            event.prevent_default()  # Prevent invalid input


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
                widget = Input(value=default, placeholder=placeholder, type="integer")
                widget.valid_empty = True
                self.inputs[name] = widget
            elif field_type is float:
                widget = Input(value=default, placeholder=placeholder, type="number")
                widget.valid_empty = True
                self.inputs[name] = widget
            elif (field_type is date) or (name == "birthday_encr"):
                widget = DateInput(value=default, placeholder=placeholder)
                self.dates[name] = widget
            else:
                widget = Input(value=default, placeholder=placeholder)
                self.inputs[name] = widget

            # add tooltip
            widget.tooltip = column.doc
            widget.id = f"{name}"

            yield widget

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

        # validation: every date must be "" or length 10
        dates_valid = all(
            len(widget.value) in (0, 10) for widget in self.dates.values()
        )

        if required_field_empty or not dates_valid:
            # mark required fields that are still empty
            for f in REQUIRED_FIELDS:
                if current.get(f, "") == "":
                    self.query_one(f"#{f}", Input).add_class("-invalid")

            # mark dates that have a wrong length
            for widget in self.dates.values():
                if len(widget.value) not in (0, 10):
                    widget.add_class("-invalid")
        else:
            # find fields that changed
            self._changed_data = {
                key: value
                for key, value in current.items()
                if value != self._original_data.get(key)
            }

            self.exit()  # Exit the app after submission

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
