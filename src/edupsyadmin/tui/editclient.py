import datetime
import os
from typing import Type

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String
from textual.app import App
from textual.events import Key
from textual.widgets import Button, Checkbox, Input, Label

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.db.clients import Client


def get_python_type(sqlalchemy_type: Type) -> Type:
    """
    Maps SQLAlchemy types to Python standard types.

    :param sqlalchemy_type: The SQLAlchemy type to be mapped.
    :return: A string representing the Python standard type.
    """
    if isinstance(sqlalchemy_type, Integer):
        return int
    elif isinstance(sqlalchemy_type, String):
        return str
    elif isinstance(sqlalchemy_type, Float):
        return float
    elif isinstance(sqlalchemy_type, Date):
        return datetime.date
    elif isinstance(sqlalchemy_type, DateTime):
        return datetime.datetime
    elif isinstance(sqlalchemy_type, Boolean):
        return bool
    else:
        raise ValueError(f"could not match {sqlalchemy_type} to a builtin type")


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
                    else:
                        event.prevent_default()
                else:
                    return  # Allow digits
            else:
                event.prevent_default()  # Prevent input if length exceeds 10
        else:
            event.prevent_default()  # Prevent invalid input


# TODO: Write a test
class StudentEntryApp(App):
    def __init__(self, client_id: int, data: dict = {}):
        super().__init__()
        self.client_id = client_id
        self.data = data
        self.inputs = {}
        self.checkboxes = {}

    def compose(self):
        # Create heading with client_id
        yield Label(f"Data for client_id: {self.client_id}")

        # Read fields from the clients table
        for column in Client.__table__.columns:
            field_type = get_python_type(column.type)
            name = column.name

            # default value
            if field_type is bool:
                default = self.data[name] if name in self.data else False
            else:
                default = str(self.data[name]) if name in self.data else ""

            # create widget
            if field_type is bool:
                widget = Checkbox(label=name, value=default)
            elif field_type is int:
                widget = Input(value=default, placeholder=name, type="integer")
            elif field_type is float:
                widget = Input(value=default, placeholder=name, type="number")
            elif field_type is datetime.date:
                widget = DateInput(value=default, placeholder=name)
            else:
                widget = Input(value=default, placeholder=name)

            # add tooltip
            widget.tooltip = column.doc

            # add widget to collection of checkboxes or input widgets
            if field_type is bool:
                self.checkboxes[name] = widget
            else:
                self.inputs[name] = widget

            yield widget

        # Submit button
        self.submit_button = Button(label="Submit")
        yield self.submit_button

    def on_button_pressed(self):
        self.data = {}

        # Collect data from input fields
        for field, input_widget in self.inputs.items():
            self.data[field] = (
                int(input_widget.value) if input_widget.value.isdigit() else None
            )
        else:
            self.data[field] = input_widget.value
        # Collect data from checkboxes
        self.data.update(
            {field: self.checkboxes[field].value for field in self.checkboxes}
        )

        self.exit()  # Exit the app after submission

    def get_data(self):
        return self.data


def get_modified_values(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike,
    client_id: int,
) -> dict:
    # retrieve current values
    manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    current_data = manager.get_decrypted_client(client_id=client_id)

    # display a form with current values filled in
    app = StudentEntryApp(client_id, data=current_data)
    app.run()

    # return changed values
    new_data = app.get_data()
    modified_values = _find_changed_values(current_data, new_data)
    return modified_values


def _find_changed_values(original: dict, updates: dict) -> dict:
    changed_values = {}

    for key, new_value in updates.items():
        if key not in original:
            raise KeyError(
                f"Key '{key}' found in updates but not in original dictionary."
            )

        # Check if the value has changed
        if original[key] != new_value:
            changed_values[key] = new_value

    return changed_values


if __name__ == "__main__":
    # just for testing
    app = StudentEntryApp(42)
    app.run()
    new_data = app.get_data()
    print(f"The data collected is: {new_data}")
