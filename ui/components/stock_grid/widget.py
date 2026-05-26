from textual.app import ComposeResult
from textual.containers import Grid
from textual.widget import Widget
from textual.widgets import Label, Static
from textual.worker import Worker, WorkerState

from config import config as app_config
from data import create_service
from models.stock_meta import StockMeta
from repositories import symbol_repo
from .constants import (
    CARDS_GRID_ID,
    CARD_CLASS,
    CLASS_SYMBOL,
    CLASS_PRICE,
    CLASS_CHANGE_UP,
    CLASS_CHANGE_DOWN,
    CLASS_LOADING,
    PRICE_ID_PREFIX,
    CHANGE_ID_PREFIX,
    WORKER_PREFIX,
)
from .styles import CSS


class StockCard(Widget):
    DEFAULT_CSS = CSS

    def __init__(self, symbol: str) -> None:
        super().__init__(classes=CARD_CLASS)
        self._symbol = symbol

    def compose(self) -> ComposeResult:
        yield Label(self._symbol, classes=CLASS_SYMBOL)
        yield Label("loading…", classes=CLASS_LOADING, id=f"{PRICE_ID_PREFIX}{self._symbol}")
        yield Label("", id=f"{CHANGE_ID_PREFIX}{self._symbol}")

    def update(self, meta: StockMeta) -> None:
        price_label = self.query_one(f"#{PRICE_ID_PREFIX}{self._symbol}", Label)
        change_label = self.query_one(f"#{CHANGE_ID_PREFIX}{self._symbol}", Label)

        if meta.price is not None:
            price_label.remove_class(CLASS_LOADING)
            price_label.add_class(CLASS_PRICE)
            price_label.update(f"{meta.currency} {meta.price:,.2f}")
        else:
            price_label.update("N/A")

        if meta.change_pct is not None:
            arrow = "▲" if meta.change_pct >= 0 else "▼"
            cls = CLASS_CHANGE_UP if meta.change_pct >= 0 else CLASS_CHANGE_DOWN
            change_label.remove_class(CLASS_CHANGE_UP, CLASS_CHANGE_DOWN)
            change_label.add_class(cls)
            change_label.update(f"{arrow} {abs(meta.change_pct):.2f}%")

    def set_error(self) -> None:
        self.query_one(f"#{PRICE_ID_PREFIX}{self._symbol}", Label).update("error")


class StockGridWidget(Widget):
    DEFAULT_CSS = CSS

    def compose(self) -> ComposeResult:
        yield Grid(id=CARDS_GRID_ID)

    def load(self) -> None:
        symbols = [ts.symbol for ts in symbol_repo.get_all()]
        grid = self.query_one(f"#{CARDS_GRID_ID}", Grid)
        grid.remove_children()
        if not symbols:
            grid.mount(Static("No symbols. Press [S] to add.", classes=CLASS_LOADING))
            return
        for symbol in symbols:
            grid.mount(StockCard(symbol))
        cfg = app_config.load()
        provider = cfg.provider or "mock"
        service = create_service(provider)
        for symbol in symbols:
            self.run_worker(
                lambda s=symbol: service.get_meta(s),
                thread=True,
                name=f"{WORKER_PREFIX}{symbol}",
                exclusive=False,
                exit_on_error=False,
            )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if not event.worker.name.startswith(WORKER_PREFIX):
            return
        symbol = event.worker.name[len(WORKER_PREFIX):]
        cards = self.query(StockCard)
        card = next((c for c in cards if c._symbol == symbol), None)
        if card is None:
            return
        if event.worker.state == WorkerState.SUCCESS and event.worker.result is not None:
            card.update(event.worker.result)
        elif event.worker.state == WorkerState.ERROR:
            card.set_error()
