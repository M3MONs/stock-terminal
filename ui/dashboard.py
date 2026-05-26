from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from config import config as app_config
from ui.components.stock_grid import StockGridWidget
from ui.components.stock_grid.widget import StockCard
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
        yield StockGridWidget(id="stock-grid")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_subtitle()
        self.query_one(StockGridWidget).load()

    def _refresh_subtitle(self) -> None:
        cfg = app_config.load()
        self.sub_title = f"Provider: {cfg.provider}"

    def action_push_symbols(self) -> None:
        def _cb(symbol: str | None) -> None:
            self.query_one(StockGridWidget).load()
            if symbol:
                self.push_screen(ChartScreen(symbol))

        self.push_screen(SymbolManagerScreen(), _cb)

    def on_stock_card_selected(self, event: StockCard.Selected) -> None:
        self.push_screen(ChartScreen(event.symbol))

    def action_pick_provider(self) -> None:
        def _cb(provider: str | None) -> None:
            self._refresh_subtitle()
            self.query_one(StockGridWidget).load()

        self.push_screen(ProviderPickerScreen(), _cb)
