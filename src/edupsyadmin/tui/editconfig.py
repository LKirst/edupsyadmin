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

    school_count: reactive[int] = reactive(0)
    form_set_count: reactive[int] = reactive(0)

    def __init__(self, config_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)
        self.inputs = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.content = VerticalScroll()
        yield self.content

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
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

        # Add buttons for adding a school
        add_school_button = Button(label="Schule hinzufügen", id="addschool")
        self.content.mount(add_school_button)

        # Create inputs for form sets
        self.load_form_sets()

        # Add save button
        save_button = Button(label="Speichern", id="save")
        self.content.mount(save_button)

    def load_schools(self):
        self.school_count = len(self.config_dict["school"])
        for school_key, school_info in self.config_dict["school"].items():
            self.add_school_inputs(school_key, school_info)

    def add_school_inputs(self, school_key: str, school_info: dict):
        self.content.mount(Static(f"Einstellungen für {school_key}"))
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

    async def save_config(self) -> None:
        """Save the updated configuration to the file."""
        save_config(self.config_dict, self.config_path)


if __name__ == "__main__":
    config_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    app = ConfigEditorApp(config_path=config_path)
    app.run()
