from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class YesNoDialog(ModalScreen[bool]):
    """A modal dialog to ask a yes/no question."""

    def __init__(
        self,
        question: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.question = question
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.question, id="question"),
            Button("Ja", variant="primary", id="yes"),
            Button("Nein", variant="error", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class InputDialog(ModalScreen[str | None]):
    """A modal dialog to ask for text input."""

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    #input_dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto auto 3;
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }
    #input_prompt {
        column-span: 2;
        content-align: center middle;
        width: 100%;
    }
    #dialogue_input_value {
        column-span: 2;
        width: 100%;
    }
    Button {
        width: 100%;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "cancel", "Abbrechen"),
    ]

    def __init__(
        self,
        prompt: str,
        initial_value: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.prompt = prompt
        self.initial_value = initial_value
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.prompt, id="input_prompt"),
            Input(value=self.initial_value, id="dialogue_input_value"),
            Button("OK", variant="primary", id="ok"),
            Button("Abbrechen", variant="error", id="cancel"),
            id="input_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            input_widget = self.query_one("#dialogue_input_value", expect_type=Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)
