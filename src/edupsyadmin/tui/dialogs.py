from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class YesNoDialog(ModalScreen[bool]):
    """A modal dialog to ask a yes/no question."""

    DEFAULT_CSS = """
    YesNoDialog {
        align: center middle;
    }

    YesNoDialog > Grid {
        grid-size: 2;
        grid-gutter: 1 2;
        width: auto;
        height: auto;
        padding: 0 1;
        border: thick $primary;
        background: $surface;
    }

    #question {
        column-span: 2;
        width: 100%;
        padding: 1 2;
        text-align: center;
    }

    #yes {
        width: 100%;
    }

    #no {
        width: 100%;
    }
    """

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
