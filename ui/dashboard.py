from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class Dashboard(App):
    TITLE = "Stock-Terminal"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
