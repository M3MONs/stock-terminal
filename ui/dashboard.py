from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from ui.screens.symbol_manager import SymbolManagerScreen


class Dashboard(App):
    TITLE = "Stock-Terminal"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "push_symbols", "Symbols"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_push_symbols(self) -> None:
        self.push_screen(SymbolManagerScreen())
