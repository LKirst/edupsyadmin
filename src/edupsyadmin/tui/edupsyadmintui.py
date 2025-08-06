from textual.app import App, ComposeResult
from textual.containers import (
    CenterMiddle,
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    Vertical,
    VerticalScroll,
)
from textual.widgets import Footer, Header, Placeholder


class EdupsyadminTui(App):
    CSS_PATH = "edupsyadmintui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            ScrollableContainer(
                Placeholder("Clients Overview (p1)", id="p1"),
                classes="with-border",
                id="clientsoverviewcontainer",
            ),
            Vertical(
                VerticalScroll(
                    Placeholder("Edit Client (p2)", id="p2"),
                    id="editclientcontainer",
                ),
                CenterMiddle(
                    HorizontalGroup(
                        Placeholder("Speichern", id="save"),
                        Placeholder("Abbrechen", id="cancel"),
                        Placeholder("Formular füllen", id="filldocumentation"),
                        id="buttonscontainer-inner",
                    ),
                    classes="with-border",
                    id="buttonscontainer-outer",
                ),
                classes="with-border",
                id="editclientandbuttonscontainer",
            ),
        )
        yield Footer()


if __name__ == "__main__":
    app = EdupsyadminTui()
    app.run()
