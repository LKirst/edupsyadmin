from textual.app import App, ComposeResult
from textual.containers import (
    CenterMiddle,
    Container,
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    Vertical,
    VerticalScroll,
)
from textual.widgets import Button, Footer, Header, Placeholder, TabbedContent, TabPane


class EdupsyadminTui(App):
    CSS_PATH = "edupsyadmintui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ScrollableContainer(
                Placeholder("Clients Overview (p1)", id="p1"),
                classes="with-border",
                id="clientsoverviewcontainer",
            )
            with Vertical(id="editclientandbuttonscontainer", classes="with-border"):
                with Container(), TabbedContent(initial="clientdata", id="clienttabs"):
                    yield TabPane(
                        "Klientendaten",
                        VerticalScroll(
                            Placeholder("Edit Client (p2)", id="p2"),
                            id="editclientcontainer",
                        ),
                        id="clientdata",
                    )
                    yield TabPane(
                        "Sitzungen",
                        VerticalScroll(
                            Placeholder("Sessions", id="sessions"),
                        ),
                    )
                yield CenterMiddle(
                    HorizontalGroup(
                        Button("Speichern", id="save"),
                        Button("Abbrechen", id="cancel"),
                        Button("Formular(e) füllen", id="filldocumentation"),
                        id="buttonscontainer-inner",
                    ),
                    classes="with-border",
                    id="buttonscontainer-outer",
                )
        yield Footer()


if __name__ == "__main__":
    app = EdupsyadminTui()
    app.run()
