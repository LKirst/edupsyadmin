import os

from textual.app import App
from textual.widgets import Button, Checkbox, Input, Label

from edupsyadmin.api.managers import ClientsManager


# TODO: Write a test
class StudentEntryApp(App):
    def __init__(self, client_id: int, data: dict = {}):
        super().__init__()
        self.client_id = client_id
        self.data = data
        self.inputs = {}
        self.checkboxes = {}

    def compose(self):
        # Define fields and their types
        # TODO: Update the field names (and the booleand fields below)
        fields = {
            "school": str,
            "gender": str,
            "entry_date": str,
            "class_name": str,
            "first_name": str,
            "last_name": str,
            "birthday": str,
            "street": str,
            "city": str,
            "parent": str,
            "telephone1": str,
            "telephone2": str,
            "email": str,
            "notes": str,
            "keyword_taetigkeitsbericht": str,
            "lrst_diagnosis": str,
            "nta_sprachen": int,
            "nta_mathephys": int,
            "nta_other_details": str,
            "nta_notes": int,
            "n_sessions": int,
        }

        boolean_fields = [
            "notenschutz",
            "nachteilsausgleich",
            "nta_font",
            "nta_aufgabentypen",
            "nta_strukturierungshilfen",
            "nta_arbeitsmittel",
            "nta_ersatz_gewichtung",
            "nta_vorlesen",
        ]

        # Create heading with client_id
        yield Label(f"Data for client_id: {self.client_id}")

        # Create input fields
        for field, field_type in fields.items():
            default_value = str(self.data[field]) if field in self.data else ""
            input_widget = Input(value=default_value, placeholder=field)
            self.inputs[field] = input_widget
            yield input_widget

        # Create checkboxes
        for field in boolean_fields:
            default_value = self.data[field] if field in self.data else False
            checkbox_widget = Checkbox(label=field, value=default_value)
            self.checkboxes[field] = checkbox_widget
            yield checkbox_widget

        # Submit button
        self.submit_button = Button(label="Submit")
        yield self.submit_button

    def on_button_pressed(self):
        # Collect data
        self.data = {field: self.inputs[field].value for field in self.inputs}
        self.data.update(
            {field: self.checkboxes[field].value for field in self.checkboxes}
        )

        # Convert string inputs to their respective types
        for field, field_type in {
            "nta_sprachen": int,
            "nta_mathephys": int,
            "nta_notes": int,
            "n_sessions": int,
        }.items():
            if self.data[field]:
                self.data[field] = field_type(self.data[field])

        self.exit()  # Exit the app after submission

    def get_data(self):
        return self.data


def edit_client(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str | os.PathLike,
    client_id: int,
) -> dict:
    # retrieve current values
    manager = ClientsManager(
        database_url,
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
