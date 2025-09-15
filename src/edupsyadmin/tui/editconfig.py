from pathlib import Path
from typing import ClassVar

import keyring
import yaml
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.events import Click
from textual.validation import ValidationResult, Validator
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


class NoPeriodValidator(Validator):
    """A validator to ensure the input does not contain periods."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the value does not contain a period."""
        if "." in value:
            return self.failure("Darf keine Punkte enthalten.")
        return self.success()


class PathIsFileValidator(Validator):
    """A validator to ensure the input is a path to an existing file."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the value is a path to an existing file."""
        path = Path(value).expanduser()
        if not path.exists():
            return self.failure("Pfad existiert nicht.")
        if not path.is_file():
            return self.failure("Pfad ist keine Datei.")
        return self.success()


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


class DeleteSchoolButton(Button):
    """Button to delete a school."""

    def __init__(self, school_key: str) -> None:
        super().__init__("Schule löschen", classes="delete")
        self.school_key = school_key


class DeleteFormSetButton(Button):
    """Button to delete a form set."""

    def __init__(self, form_set_key: str) -> None:
        super().__init__("Formular-Satz löschen", classes="delete")
        self.form_set_key = form_set_key


class SchoolContainer(VerticalScroll):
    """Container for a school's widgets."""

    def __init__(self, *children: Widget, school_key: str, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self.school_key = school_key


class FormSetContainer(VerticalScroll):
    """Container for a form set's widgets."""

    def __init__(self, *children: Widget, form_set_key: str, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self.form_set_key = form_set_key


class ConfigEditorApp(App):
    """A Textual app to edit edupsyadmin YAML configuration files."""

    CSS_PATH = "editconfig.tcss"
    BINDINGS: ClassVar[list] = [
        ("s", "save", "Speichern"),
        ("ctrl+q", "quit", "Beenden"),
    ]

    school_count: int = 0
    form_set_count: int = 0

    def __init__(self, config_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config_dict = load_config(config_path)

        self.inputs: dict[str, Input] = {}  # input fields except for password widget
        self.school_key_inputs: dict[str, Input] = {}
        self.form_set_key_inputs: dict[str, Input] = {}

        self.password_input: Input | None = None
        self.last_school_widget: Widget | None = None
        self.last_form_set_widget: Widget | None = None
        self.save_button: Button | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.content = VerticalScroll()
        yield self.content

    async def on_mount(self) -> None:
        self.title = "Konfiguration für edupsyadmin"  # title for the header

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
        self.content.mount(Button("Formular-Satz hinzufügen", id="addformset"))

        # action buttons
        self.save_button = Button("Speichern", id="save")
        self.content.mount(
            Horizontal(
                self.save_button,
                Button("Abbrechen", id="cancel", variant="error"),
                classes="action-buttons",
            )
        )
        self.call_later(self.update_save_button_state)

    def load_schools(self):
        """
        Load schools that already exist in the config dict
        """
        self.school_count = len(self.config_dict["school"])
        for i, (key, info) in enumerate(self.config_dict["school"].items(), 1):
            self.add_school_inputs(key, info, i)

    def add_school_inputs(self, school_key: str, info: dict[str, str], index: int):
        """
        Add school input widgets for a given school key

        :param school_key: a short key (without special characters) for the school
        :param info: a dict with `"widget name":"widget value"`
        :param index: index of the school
        """
        widgets: list[Widget] = [Static(f"Einstellungen für Schule {index}")]

        key_inp = Input(
            value=school_key, placeholder="Schullabel", validators=[NoPeriodValidator()]
        )
        key_inp.tooltip = "Schullabel (nur Buchstaben, keine Leerzeichen)"
        self.school_key_inputs[school_key] = key_inp
        self.inputs[f"school_key.{school_key}"] = key_inp
        widgets.append(key_inp)

        for k, v in info.items():
            inp = Input(value=str(v), placeholder=k)
            inp.tooltip = TOOLTIPS.get(k, "")
            self.inputs[f"school.{school_key}.{k}"] = inp
            widgets.append(inp)

        widgets.append(DeleteSchoolButton(school_key))

        container = SchoolContainer(*widgets, school_key=school_key)

        if self.last_school_widget:
            self.content.mount(container, after=self.last_school_widget)
        else:
            self.content.mount(container)
        self.last_school_widget = container

    def load_form_sets(self):
        """
        Load existing form sets from the config dict
        """
        self.form_set_count = len(self.config_dict["form_set"])
        for key, paths in self.config_dict["form_set"].items():
            self.add_form_set_inputs(key, paths)

    def add_form_set_inputs(self, form_set_key: str, paths: list[str]):
        """
        Add widgets for a form set

        :param form_set_key: key for this form set
        :param paths: a list of paths belonging to this formset
        """
        widgets: list[Widget] = []

        num = len(self.form_set_key_inputs) + 1  # the index of this form set
        widgets.append(Static(f"Einstellungen für Formular-Satz {num}"))

        key_inp = Input(
            value=form_set_key,
            placeholder="Formular-Satz-Kurzname",
            validators=[NoPeriodValidator()],
        )
        key_inp.tooltip = "Kurzname des Formular-Satzes"
        self.form_set_key_inputs[form_set_key] = key_inp
        self.inputs[f"form_set_key.{form_set_key}"] = key_inp
        widgets.append(key_inp)

        for i, p in enumerate(paths):
            inp = Input(
                value=str(p),
                placeholder=f"Pfad {i + 1}",
                validators=[PathIsFileValidator()],
            )
            self.inputs[f"form_set.{form_set_key}.{i}"] = inp
            widgets.append(inp)

        widgets.append(AddPathButton(form_set_key))
        widgets.append(DeleteFormSetButton(form_set_key))

        container = FormSetContainer(*widgets, form_set_key=form_set_key)

        # mount widgets at the correct position
        if self.last_form_set_widget is not None:
            # insert widgets after the last form_set
            self.content.mount(container, after=self.last_form_set_widget)
        else:
            # insert the first form-set before the addformset button
            try:
                addformset_btn = self.query_exactly_one(
                    "#addformset", expect_type=Button
                )
                self.content.mount(container, before=addformset_btn)
            except NoMatches:  # there is no addformset button yet
                self.content.mount(container)

        # update marker
        self.last_form_set_widget = container

    def add_new_school(self):
        """
        Add new school
        """
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
        """
        Add a new form set with one path
        """
        i = 1
        key = f"FormSet{i}"
        while key in self.config_dict["form_set"]:
            i += 1
            key = f"FormSet{i}"
        self.config_dict["form_set"][key] = []
        self.add_form_set_inputs(key, [])
        self.form_set_count += 1

    def add_form_path(self, button: AddPathButton):
        """
        Add a path widget to the widgets of a form set

        :param button: The button that was pressed.
        """
        form_set_key = button.form_set_key
        paths = self.config_dict["form_set"][form_set_key]
        idx = len(paths)
        paths.append("")

        inp = Input(
            value="", placeholder=f"Pfad {idx + 1}", validators=[PathIsFileValidator()]
        )
        self.inputs[f"form_set.{form_set_key}.{idx}"] = inp

        # Mount the new input before the button that was pressed.
        button.parent.mount(inp, before=button)

    def delete_school(self, school_key: str):
        """
        Delete a school and its widgets.

        :param school_key: The key of the school to delete.
        """
        # Remove school from config
        if school_key in self.config_dict["school"]:
            del self.config_dict["school"][school_key]

        # Remove associated inputs from self.inputs and self.school_key_inputs
        for k in list(self.inputs.keys()):
            if k.startswith(f"school.{school_key}.") or k == f"school_key.{school_key}":
                del self.inputs[k]
        if school_key in self.school_key_inputs:
            del self.school_key_inputs[school_key]

        # Remove the school's widget container
        for container in self.query(SchoolContainer):
            if container.school_key == school_key:
                if self.last_school_widget == container:
                    prev_sibling = container.previous_sibling
                    if isinstance(prev_sibling, SchoolContainer):
                        self.last_school_widget = prev_sibling
                    else:
                        self.last_school_widget = None
                container.remove()
                break

    def delete_form_set(self, form_set_key: str):
        """
        Delete a form set and its widgets.

        :param form_set_key: The key of the form set to delete.
        """
        # Remove form set from config
        if form_set_key in self.config_dict["form_set"]:
            del self.config_dict["form_set"][form_set_key]

        # Remove associated inputs from self.inputs and self.form_set_key_inputs
        for k in list(self.inputs.keys()):
            if (
                k.startswith(f"form_set.{form_set_key}.")
                or k == f"form_set_key.{form_set_key}"
            ):
                del self.inputs[k]
        if form_set_key in self.form_set_key_inputs:
            del self.form_set_key_inputs[form_set_key]

        # Remove the form set's widget container
        for container in self.query(FormSetContainer):
            if container.form_set_key == form_set_key:
                if self.last_form_set_widget == container:
                    prev_sibling = container.previous_sibling
                    if isinstance(prev_sibling, FormSetContainer):
                        self.last_form_set_widget = prev_sibling
                    else:
                        self.last_form_set_widget = None
                container.remove()
                break

    def update_save_button_state(self) -> None:
        """Disables the save button if any input is invalid and logs details."""
        invalid_inputs = []
        for key, inp in self.inputs.items():
            if not inp.is_valid:
                invalid_inputs.append(inp)

        if self.password_input and not self.password_input.is_valid:
            invalid_inputs.append(self.password_input)

        all_valid = not invalid_inputs

        if self.save_button:
            self.save_button.disabled = not all_valid

    async def on_button_pressed(self, event: Click) -> None:
        if isinstance(event.button, AddPathButton):
            self.add_form_path(event.button)
            return
        if isinstance(event.button, DeleteSchoolButton):
            self.delete_school(event.button.school_key)
            return
        if isinstance(event.button, DeleteFormSetButton):
            self.delete_form_set(event.button.form_set_key)
            return
        match event.button.id:
            case "save":
                await self.action_save()
            case "cancel":
                self.exit()
            case "addschool":
                self.add_new_school()
            case "addformset":
                self.add_new_form_set()

    async def on_input_changed(self, event: Input.Changed) -> None:
        self.update_save_button_state()

        if not event.input.is_valid:
            return

        # ignore meta keys
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
        """
        Rename a key within a section of the config and update related metadata

        This function updates the configuration dictionary by renaming a
        specified key in the given section ('school' or 'form_set').
        It also updates the internal inputs dictionary and metadata keys
        associated with the old key. If the section is 'form_set', it
        updates the form_set_key in AddPathButton instances.

        :param section: section within the config dictionary, where the key is located
        :param old_key: the current name of the key to be renamed
        :param new_key: the new name of the key to be renamed
        :param key_dict: a dictionary mapping keys to Input widgets, used to
            update the key mapping
        :param prefix: the prefix used in the keys within the inputs dictionary,
            indicating the type of data structure ('school' or 'form_set')
        """
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
        """
        Save the configuration, and if there are no conflicts, save
        the new password.

        :raises ValueError: If a password already exists for the given UID and username.
        :raises ValueError: If either the app UID or username is missing.
        """
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

    async def action_save(self) -> None:
        """Save the configuration and exit the app."""
        if not self.query_one("#save", Button).disabled:
            self.save_config()
            self.exit()
