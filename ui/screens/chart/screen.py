import data.mock  # noqa: F401 — registers MockDataSource
import data.adapters.mock  # noqa: F401 — registers MockAdapter

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label
from textual.worker import Worker, WorkerState

from config import config as app_config
from data import create_service
from models.timeframe import Timeframe
from ui.components.candle_chart import CandleChartWidget
from ui.components.stock_info import StockInfoPanel
from ui.screens.symbol_manager import SymbolManagerScreen
from .constants import BINDINGS, CHART_ID, INFO_PANEL_ID, STATUS_ID, TIMEFRAME_ORDER
from .styles import CSS


class ChartScreen(Screen):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self._symbol = symbol
        self._timeframe: Timeframe = Timeframe.H1

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id=STATUS_ID)
        yield StockInfoPanel(id=INFO_PANEL_ID)
        yield CandleChartWidget(id=CHART_ID)
        yield Footer()

    def on_mount(self) -> None:
        cfg = app_config.load()
        self._timeframe = cfg.default_timeframe
        self._load_data(self._symbol)

    def _load_data(self, symbol: str) -> None:
        self.query_one(f"#{STATUS_ID}", Label).update(f"Loading {symbol} {self._timeframe}…")
        service = create_service("mock")
        timeframe = self._timeframe
        self.run_worker(
            lambda: (service.get_ohlcv(symbol, timeframe), service.get_meta(symbol)),
            thread=True,
            name="load_chart",
            exclusive=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "load_chart":
            return
        if event.worker.state == WorkerState.SUCCESS:
            result = event.worker.result
            if result is not None:
                ohlcv, meta = result
                series = ohlcv.model_copy(update={"meta": meta})
                self.query_one(StockInfoPanel).update(series)
                self.query_one(CandleChartWidget).update(series)
                self.query_one(f"#{STATUS_ID}", Label).update(
                    f"{self._symbol} · {self._timeframe}"
                )
        elif event.worker.state == WorkerState.ERROR:
            self.query_one(f"#{STATUS_ID}", Label).update(f"Error loading {self._symbol}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_pick_symbol(self) -> None:
        def _cb(symbol: str | None) -> None:
            if symbol:
                self._symbol = symbol
                self._load_data(symbol)

        self.app.push_screen(SymbolManagerScreen(), _cb)

    def action_prev_timeframe(self) -> None:
        idx = TIMEFRAME_ORDER.index(self._timeframe)
        if idx > 0:
            self._timeframe = TIMEFRAME_ORDER[idx - 1]
            self._load_data(self._symbol)

    def action_next_timeframe(self) -> None:
        idx = TIMEFRAME_ORDER.index(self._timeframe)
        if idx < len(TIMEFRAME_ORDER) - 1:
            self._timeframe = TIMEFRAME_ORDER[idx + 1]
            self._load_data(self._symbol)

    def action_zoom_in(self) -> None:
        self.query_one(CandleChartWidget).zoom_in()

    def action_zoom_out(self) -> None:
        self.query_one(CandleChartWidget).zoom_out()

    def action_pan_left(self) -> None:
        self.query_one(CandleChartWidget).pan_left()

    def action_pan_right(self) -> None:
        self.query_one(CandleChartWidget).pan_right()
