from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from ui.screens.chart import ChartScreen
from ui.screens.provider_picker import ProviderPickerScreen
from ui.screens.symbol_manager import SymbolManagerScreen


class Dashboard(App):
    TITLE = "Stock-Terminal"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "push_symbols", "Symbols"),
        ("p", "pick_provider", "Provider"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_push_symbols(self) -> None:
        def _cb(symbol: str | None) -> None:
            if symbol:
                self.push_screen(ChartScreen(symbol))

        self.push_screen(SymbolManagerScreen(), _cb)

    def action_pick_provider(self) -> None:
        self.push_screen(ProviderPickerScreen())
