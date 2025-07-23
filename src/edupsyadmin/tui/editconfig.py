from pathlib import Path

import keyring
import yaml
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
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


class AddPathButton(Button):
    """Button with a custom attribute of form_set_key"""

    def __init__(self, form_set_key: str) -> None:
        super().__init__("Pfad hinzufügen", classes="addformpath")
        self.form_set_key = form_set_key


class ConfigEditorApp(App):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"

    school_count: reactive[int] = reactive(0)
    form_set_count: reactive[int] = reactive(0)

    def __init__(self, config_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)

        self.inputs: dict[str, Input] = {}
        self.school_key_inputs: dict[str, Input] = {}
        self.form_set_key_inputs: dict[str, Input] = {}

        self.password_input: Input | None = None
        self.last_school_widget: Widget | None = None
        self.last_form_set_widget: Widget | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.content = VerticalScroll()
        yield self.content

    async def on_mount(self) -> None:
        self.title = "Konfiguration für edupsyadmin"  # title for the header
        self.generate_content()

    def generate_content(self):
        # core
        self.content.mount(Static("App-Einstellungen"))
        for key, value in self.config_dict["core"].items():
            inp = Input(value=str(value), placeholder=key)
            inp.tooltip = TOOLTIPS.get(key, "")
            self.inputs[f"core.{key}"] = inp
            self.content.mount(inp)

        # password
        self.content.mount(
            Static(
                "Wenn bereits ein Passwort hinterlegt ist, lasse das Feld leer. "
                "Ändere es nur, wenn du eine neue Datenbank anlegst."
            )
        )
        self.password_input = Input(placeholder="Passwort", password=True)
        self.content.mount(self.password_input)

        # schoolpsy
        self.content.mount(Static("Schulpsychologie-Einstellungen"))
        for key, value in self.config_dict["schoolpsy"].items():
            inp = Input(value=str(value), placeholder=key)
            inp.tooltip = TOOLTIPS.get(key, "")
            self.inputs[f"schoolpsy.{key}"] = inp
            self.content.mount(inp)

        # schools
        self.load_schools()
        self.content.mount(Button("Schule hinzufügen", id="addschool"))

        # form_sets
        self.load_form_sets()
        self.content.mount(Button("Form-Set hinzufügen", id="addformset"))

        # save button
        self.content.mount(Button("Speichern", id="save"))

    def load_schools(self):
        self.school_count = len(self.config_dict["school"])
        for i, (key, info) in enumerate(self.config_dict["school"].items(), 1):
            self.add_school_inputs(key, info, i)

    def add_school_inputs(self, school_key: str, info: dict, index: int):
        widgets = [Static(f"Einstellungen für Schule {index}")]

        key_inp = Input(value=school_key, placeholder="Schullabel")
        key_inp.tooltip = "Schullabel (nur Buchstaben, keine Leerzeichen)"
        self.school_key_inputs[school_key] = key_inp
        self.inputs[f"school_key.{school_key}"] = key_inp
        widgets.append(key_inp)

        for k, v in info.items():
            inp = Input(value=str(v), placeholder=k)
            inp.tooltip = TOOLTIPS.get(k, "")
            self.inputs[f"school.{school_key}.{k}"] = inp
            widgets.append(inp)

        if self.last_school_widget:
            self.content.mount_all(widgets, after=self.last_school_widget)
        else:
            self.content.mount_all(widgets)
        self.last_school_widget = widgets[-1]

    def load_form_sets(self):
        self.form_set_count = len(self.config_dict["form_set"])
        for key, paths in self.config_dict["form_set"].items():
            self.add_form_set_inputs(key, paths)

    def add_form_set_inputs(self, form_set_key: str, paths: list[str]):
        widgets: list[Widget] = []

        num = len(self.form_set_key_inputs) + 1
        widgets.append(Static(f"Einstellungen für Form-Set {num}"))

        key_inp = Input(value=form_set_key, placeholder="Form-Set-Label")
        key_inp.tooltip = "Name des Form-Sets"
        self.form_set_key_inputs[form_set_key] = key_inp
        self.inputs[f"form_set_key.{form_set_key}"] = key_inp
        widgets.append(key_inp)

        for i, p in enumerate(paths):
            inp = Input(value=str(p), placeholder=f"Pfad {i+1}")
            self.inputs[f"form_set.{form_set_key}.{i}"] = inp
            widgets.append(inp)

        widgets.append(AddPathButton(form_set_key))

        # mount widgets at the correct position
        if self.last_form_set_widget is not None:
            # insert widgets after the last form_set
            self.content.mount_all(widgets, after=self.last_form_set_widget)
        else:
            # insert the first form-set before the addformset button
            try:
                addformset_btn = self.query_exactly_one(
                    "#addformset", expect_type=Button
                )
                self.content.mount_all(widgets, before=addformset_btn)
            except NoMatches:  # there is no addformset button yet
                self.content.mount_all(widgets)

        # update marker
        self.last_form_set_widget = widgets[-1]

    def add_new_school(self):
        key = f"Schule{self.school_count + 1}"
        while key in self.config_dict["school"]:
            self.school_count += 1
            key = f"Schule{self.school_count + 1}"

        self.config_dict["school"][key] = {
            "school_head_w_school": "",
            "school_name": "",
            "school_street": "",
            "school_city": "",
            "end": "",
        }
        self.add_school_inputs(
            key, self.config_dict["school"][key], self.school_count + 1
        )
        self.school_count += 1

    def add_new_form_set(self):
        i = 1
        key = f"FormSet{i}"
        while key in self.config_dict["form_set"]:
            i += 1
            key = f"FormSet{i}"
        self.config_dict["form_set"][key] = []
        self.add_form_set_inputs(key, [])
        self.form_set_count += 1

    def add_form_path(self, form_set_key: str):
        paths = self.config_dict["form_set"][form_set_key]
        idx = len(paths)
        paths.append("")

        inp = Input(value="", placeholder=f"Pfad {idx + 1}")
        self.inputs[f"form_set.{form_set_key}.{idx}"] = inp

        last = None
        for i in range(idx):
            k = f"form_set.{form_set_key}.{i}"
            if k in self.inputs:
                last = self.inputs[k]

        if last:
            self.content.mount(inp, after=last)
        else:
            key_widget = self.inputs[f"form_set_key.{form_set_key}"]
            self.content.mount(inp, after=key_widget)

    async def on_button_pressed(self, event: Click) -> None:
        if isinstance(event.button, AddPathButton):
            self.add_form_path(event.button.form_set_key)
            return
        match event.button.id:
            case "save":
                await self.save_config()
                self.exit()
            case "addschool":
                self.add_new_school()
            case "addformset":
                self.add_new_form_set()

    async def on_input_changed(self, event: Input.Changed) -> None:
        # --- reine Wertfelder (Meta-Keys ausklammern)
        for key, inp in self.inputs.items():
            if key.startswith(("school_key.", "form_set_key.")):
                continue

            section, *rest = key.split(".")
            target = self.config_dict[section]

            for part in rest[:-1]:
                target = target[part]

            last = rest[-1]
            if isinstance(target, list):
                target[int(last)] = inp.value
            else:
                target[last] = inp.value

        # rename schools
        changes = [
            (old, inp.value)
            for old, inp in self.school_key_inputs.items()
            if inp.value
            and inp.value != old
            and inp.value not in self.config_dict["school"]
        ]
        for old, new in changes:
            self._rename_key(
                "school", old, new, self.school_key_inputs, prefix="school"
            )

        # rename form_sets
        changes = [
            (old, inp.value)
            for old, inp in self.form_set_key_inputs.items()
            if inp.value
            and inp.value != old
            and inp.value not in self.config_dict["form_set"]
        ]
        for old, new in changes:
            self._rename_key(
                "form_set", old, new, self.form_set_key_inputs, prefix="form_set"
            )

    def _rename_key(
        self,
        section: str,
        old_key: str,
        new_key: str,
        key_dict: dict[str, Input],
        *,
        prefix: str,
    ):
        # move entry in the config dict
        self.config_dict[section][new_key] = self.config_dict[section].pop(old_key)

        # update keys in self.inputs
        for k in list(self.inputs):
            if k.startswith(f"{prefix}.{old_key}."):
                self.inputs[
                    k.replace(f"{prefix}.{old_key}.", f"{prefix}.{new_key}.")
                ] = self.inputs.pop(k)

        # update meta keys
        meta_old = f"{prefix}_key.{old_key}"
        meta_new = f"{prefix}_key.{new_key}"
        if meta_old in self.inputs:
            self.inputs[meta_new] = self.inputs.pop(meta_old)

        key_dict[new_key] = key_dict.pop(old_key)

        # change the form_set_key in addformpath buttons
        if section == "form_set":
            for btn in self.query(AddPathButton):
                if btn.form_set_key == old_key:
                    btn.form_set_key = new_key

    async def save_config(self):
        save_config(self.config_dict, self.config_path)

        app_uid = self.config_dict["core"].get("app_uid")
        username = self.config_dict["core"].get("app_username")
        if self.password_input and self.password_input.value:
            if app_uid and username and not keyring.get_password(app_uid, username):
                keyring.set_password(app_uid, username, self.password_input.value)
            elif app_uid and username:
                raise ValueError(
                    f"Für UID {app_uid} und "
                    f"Benutzer {username} existiert bereits ein Passwort."
                )
            else:
                raise ValueError("app_uid und / oder app_username fehlen.")
