from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Rule

from models.ohlcv_series import OHLCVSeries
from ui.components.stock_info.styles import CSS

_CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "PLN": "zł",
    "CHF": "Fr",
    "CAD": "C$",
    "AUD": "A$",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
}


class StockInfoPanel(Widget):
    DEFAULT_CSS = CSS

    def compose(self) -> ComposeResult:
        yield Label("—", id="stock-name")
        yield Rule()
        yield Label("—", id="stock-price")

    def update(self, series: OHLCVSeries) -> None:
        name = series.symbol
        if series.meta and series.meta.name:
            name = series.meta.name

        currency = series.meta.currency if series.meta else "USD"
        symbol = _CURRENCY_SYMBOLS.get(currency, f"{currency} ")

        price = "—"
        if series.candles:
            price = f"{symbol}{series.candles[-1].close:,.2f}"

        self.query_one("#stock-name", Label).update(name)
        self.query_one("#stock-price", Label).update(price)
