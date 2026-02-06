from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from edupsyadmin.tui.dialogs import YesNoDialog

CSS = """
QuitScreen {
    align: center middle;
}

#dialog {
    grid-size: 2;
    grid-gutter: 1 2;
    grid-rows: 1fr 3;
    padding: 0 1;
    width: 60;
    height: 11;
    border: thick $background 80%;
    background: $surface;
}

#question {
    column-span: 2;
    height: 1fr;
    width: 1fr;
    content-align: center middle;
}

Button {
    width: 100%;
}
"""


class DialogTestApp(App[None]):
    """A simple app for testing YesNoDialog."""

    CSS = CSS

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_show_dialog(self) -> None:
        def handle_result(result: bool) -> None:
            self.app.log(f"Dialog dismissed with result: {result}")

        self.push_screen(YesNoDialog(question="Möchten Sie fortfahren?"), handle_result)


def test_yes_no_dialog(snap_compare) -> None:
    """Test that YesNoDialog renders correctly."""
    app = DialogTestApp()

    async def run_before(pilot):
        pilot.app.action_show_dialog()
        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(80, 20))
