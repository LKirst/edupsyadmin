import importlib.resources
from pathlib import Path

import yaml
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Static


def load_config(file_path: Path) -> dict:
    """Load the YAML configuration file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def save_config(config_dict: dict, file_path: Path) -> None:
    """Save the configuration dictionary back to the YAML file."""
    with open(file_path, "w") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False)


class ConfigEditorApp(App):
    """A Textual app to edit YAML configuration files."""

    CSS_PATH = "config_editor.tcss"
    school_count: reactive[int] = reactive(0)
    form_set_count: reactive[int] = reactive(0)

    def __init__(self, config_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)
        self.inputs = {}
        self.school_key_inputs = {}

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
            self.inputs[f"core.{key}"] = input_widget
            self.content.mount(input_widget)

        # Create inputs for schoolpsy settings
        self.content.mount(Static("Schulpsychologie-Einstellungen"))
        for key, value in self.config_dict["schoolpsy"].items():
            input_widget = Input(value=str(value), placeholder=key)
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
        i = 0
        for school_key, school_info in self.config_dict["school"].items():
            i += 1
            self.add_school_inputs(school_key, school_info, i)

    def add_school_inputs(self, school_key: str, school_info: dict, index: int):
        self.content.mount(Static(f"Einstellungen für Schule {index}"))

        school_key_input = Input(value=school_key, placeholder="Schullabel")
        self.school_key_inputs[school_key] = school_key_input
        self.content.mount(school_key_input)

        for key, value in school_info.items():
            input_widget = Input(value=str(value), placeholder=key)
            self.inputs[f"school.{school_key}.{key}"] = input_widget
            self.content.mount(input_widget)

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


if __name__ == "__main__":
    config_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    app = ConfigEditorApp(config_path=config_path)
    app.run()
