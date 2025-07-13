import datetime

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
    def __init__(self, client_id: int | None, data: dict = {}):
        super().__init__()
        self.client_id = client_id
        self.data = data
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
                default = self.data.get(name, False)
            else:
                default = str(self.data[name]) if name in self.data else ""

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
            elif (field_type is datetime.date) or (name == "birthday_encr"):
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

        # Collect data from input and date fields
        inputs_and_dates = {**self.inputs, **self.dates}
        for field, input_widget in inputs_and_dates.items():
            self.data[field] = input_widget.value
        # Collect data from checkboxes
        self.data.update(
            {field: self.checkboxes[field].value for field in self.checkboxes}
        )

        log.info(f"Submitted: {self.data}")
        required_field_empty = any(self.data[field] == "" for field in REQUIRED_FIELDS)
        dates_valid = all(
            (len(widget.value) == 10) or (len(widget.value) == 0)
            for field, widget in self.dates.items()
        )
        if required_field_empty or (not dates_valid):
            # show what fields are required and still empty
            for field in REQUIRED_FIELDS:
                if self.data[field] == "":
                    input_widget = self.query_one(f"#{field}", Input)
                    input_widget.add_class("-invalid")
            # show what dates are not in the correct format
            for field, widget in self.dates.items():
                log.debug(
                    f"widget {widget.id} has a value length of {len(widget.value)}"
                )
                if not ((len(widget.value) == 10) or (len(widget.value) == 0)):
                    widget.add_class("-invalid")
        else:
            self.exit()  # Exit the app after submission

    def get_data(self):
        return self.data
