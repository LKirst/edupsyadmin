import importlib.resources
from pathlib import Path

import keyring
import yaml
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Static

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
}


def load_config(file_path: Path) -> dict:
    """Load the YAML configuration file."""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config_dict: dict, file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)


class ConfigEditorApp(App):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    school_count: reactive[int] = reactive(0)
    form_set_count: reactive[int] = reactive(0)

    def __init__(self, config_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)
        self.inputs = {}
        self.school_key_inputs = {}
        self.password_input = None  # password input widget
        self.last_school_widget = None  # last school widget

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.content = VerticalScroll()
        yield self.content

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "Konfiguration für edupsyadmin"  # title for the header
        self.generate_content()

    def generate_content(self):
        """Generate content for the VerticalScroll container."""

        # Create inputs for core settings
        self.content.mount(Static("App-Einstellungen"))
        for key, value in self.config_dict["core"].items():
            input_widget = Input(value=str(value), placeholder=key)
            input_widget.tooltip = TOOLTIPS.get(key, "")
            self.inputs[f"core.{key}"] = input_widget
            self.content.mount(input_widget)

        # Create password input widget
        self.content.mount(
            Static(
                "Wenn schon ein Passwort festgelegt wurde, bitte das "
                "folgende Feld nicht bearbeiten. "
                "Ändere das Passwort nur, wenn du eine neue Datenbank "
                "anlegst. "
                "Wähle ein sicheres Passwort (siehe Tipps für sichere "
                "Passwörter auf der Website des BSI."
            )
        )
        self.password_input = Input(placeholder="Passwort", password=True)
        self.content.mount(self.password_input)

        # Create inputs for schoolpsy settings
        self.content.mount(Static("Schulpsychologie-Einstellungen"))
        for key, value in self.config_dict["schoolpsy"].items():
            input_widget = Input(value=str(value), placeholder=key)
            input_widget.tooltip = TOOLTIPS.get(key, "")
            self.inputs[f"schoolpsy.{key}"] = input_widget
            self.content.mount(input_widget)

        # Create inputs for each school
        self.load_schools()

        # Add button for adding a school
        add_school_button = Button(label="Schule hinzufügen", id="addschool")
        self.content.mount(add_school_button)

        # Create inputs for form sets
        self.load_form_sets()

        # Add save button
        save_button = Button(label="Speichern", id="save")
        self.content.mount(save_button)

    def load_schools(self):
        self.school_count = len(self.config_dict["school"])
        for i, (school_key, school_info) in enumerate(
            self.config_dict["school"].items(), start=1
        ):
            self.add_school_inputs(school_key, school_info, i)

    def add_school_inputs(self, school_key: str, school_info: dict, index: int):
        this_school_inputs = [Static(f"Einstellungen für Schule {index}")]

        school_key_input = Input(value=school_key, placeholder="Schullabel")
        school_key_input.tooltip = "Schullabel (ohne Lehrzeichen)"
        self.school_key_inputs[school_key] = school_key_input
        this_school_inputs.append(school_key_input)

        for key, value in school_info.items():
            input_widget = Input(value=str(value), placeholder=key)
            input_widget.tooltip = TOOLTIPS.get(key, "")
            self.inputs[f"school.{school_key}.{key}"] = input_widget
            this_school_inputs.append(input_widget)

        # Mount the new school inputs after the last school widget
        if self.last_school_widget:
            self.content.mount_all(this_school_inputs, after=self.last_school_widget)
        else:
            self.content.mount_all(this_school_inputs)

        # Update the last school widget reference
        self.last_school_widget = this_school_inputs[-1]

    def load_form_sets(self):
        self.form_set_count = len(self.config_dict["form_set"])
        for form_set_key, paths in self.config_dict["form_set"].items():
            self.add_form_set_inputs(form_set_key, paths)

    def add_form_set_inputs(self, form_set_key: str, paths: list):
        self.content.mount(Static(f"Form Set: {form_set_key}"))
        for i, path in enumerate(paths):
            input_widget = Input(value=str(path), placeholder=f"Path {i + 1}")
            self.inputs[f"form_set.{form_set_key}.{i}"] = input_widget
            self.content.mount(input_widget)

        add_file_button = Button(
            label=f"Füge Pfad hinzu zum Set {form_set_key}",
            id=f"addfileto{form_set_key}",
        )
        self.content.mount(add_file_button)

    async def on_button_pressed(self, event: Click) -> None:
        if event.button.id == "save":
            await self.save_config()
            self.exit(event.button.id)
        elif event.button.id == "addschool":
            self.add_new_school()
        elif event.button.id.startswith("addfileto"):
            form_set_key = event.button.id.replace("addfileto", "")
            self.add_form_path(form_set_key)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Called when an input is changed."""
        # Update the config dictionary with the new value
        for key, input_widget in self.inputs.items():
            section, *sub_keys = key.split(".")
            sub_dict = self.config_dict[section]
            for sub_key in sub_keys[:-1]:
                sub_dict = sub_dict[sub_key]

            # Convert the last key to an integer if sub_dict is a list
            if isinstance(sub_dict, list):
                sub_dict[int(sub_keys[-1])] = input_widget.value
            else:
                sub_dict[sub_keys[-1]] = input_widget.value

        # Handle school key changes
        changes = []
        for old_key, input_widget in self.school_key_inputs.items():
            new_key = input_widget.value
            if new_key != old_key and new_key not in self.config_dict["school"]:
                changes.append((old_key, new_key))

        for old_key, new_key in changes:
            self.config_dict["school"][new_key] = self.config_dict["school"].pop(
                old_key
            )
            # Update the inputs dictionary to reflect the new key
            for key in list(self.inputs.keys()):
                if key.startswith(f"school.{old_key}."):
                    new_input_key = key.replace(
                        f"school.{old_key}.", f"school.{new_key}."
                    )
                    self.inputs[new_input_key] = self.inputs.pop(key)
            self.school_key_inputs[new_key] = self.school_key_inputs.pop(old_key)

    def add_new_school(self) -> None:
        """Add a new school to the configuration."""
        new_school_key = f"Schule{self.school_count + 1}"
        while new_school_key in self.config_dict["school"]:
            self.school_count += 1
            new_school_key = f"NewSchool{self.school_count + 1}"

        self.config_dict["school"][new_school_key] = {
            "end": "",
            "school_city": "",
            "school_name": "",
            "school_street": "",
        }
        self.add_school_inputs(
            new_school_key,
            self.config_dict["school"][new_school_key],
            self.school_count + 1,
        )
        self.school_count += 1

    def add_form_path(self, form_set_key: str) -> None:
        """Add a new path to the specified form set."""
        # Retrieve the current list of paths for the form set
        current_paths = self.config_dict["form_set"].get(form_set_key, [])

        # Create a new input field for the additional path
        new_path_index = len(current_paths)
        new_path_input = Input(value="", placeholder=f"Path {new_path_index + 1}")

        # Update the configuration dictionary to include the new path
        self.config_dict["form_set"][form_set_key].append("")

        # Add the new input to the form set inputs
        self.inputs[f"form_set.{form_set_key}.{new_path_index}"] = new_path_input

        # Find the last path input widget for the specified form set
        last_path_input = None
        for i in range(new_path_index):
            input_key = f"form_set.{form_set_key}.{i}"
            if input_key in self.inputs:
                last_path_input = self.inputs[input_key]

        # Mount the new input widget in the correct position
        if last_path_input is not None:
            self.content.mount(new_path_input, after=last_path_input)
        else:
            # If no paths exist, add it right after the form set key input
            form_set_key_input = self.inputs[f"form_set_key.{form_set_key}"]
            self.content.mount(new_path_input, after=form_set_key_input)

    async def save_config(self) -> None:
        """Save the updated configuration to the file."""
        save_config(self.config_dict, self.config_path)
        app_uid = self.config_dict["core"].get("app_uid", None)
        username = self.config_dict["core"].get("app_username", None)
        if (
            app_uid
            and username
            and self.password_input.value
            and not keyring.get_password(app_uid, username)
        ):
            keyring.set_password(app_uid, username, self.password_input.value)
        elif app_uid and username:
            raise ValueError(
                f"A password for UID {app_uid} and username {username} already exists."
            )
        else:
            raise ValueError("app_uid and username must not be None.")


if __name__ == "__main__":
    config_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    app = ConfigEditorApp(config_path=config_path)
    app.run()
