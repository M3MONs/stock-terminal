import logging
import threading
from datetime import datetime, timezone

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual.worker import Worker, WorkerState

from connectors.base import ConnectorAuthError, ConnectorError, ConnectorNotConfiguredError
from connectors.registry import get_connector_key_field
from data import create_service
from data.base import SourceAuthError, SourceError, SourceRateLimitError
from infra import config as app_config
from infra.security.keystore import get_secret
from models.app_config import AppConfig
from models.stock_meta import StockMeta
from models.user_agent_recommendation import UserAgentRecommendation
from persistence.repositories import recommendation_repo, symbol_repo
from services import signal_service

from .constants import (
    COL_AGE,
    COL_CHANGE,
    COL_PRICE,
    COL_SIGNAL,
    COL_SL,
    COL_SYMBOL,
    COL_TP,
    COLUMN_WEIGHTS,
    EMPTY_ID,
    KEY_AGE,
    KEY_CHANGE,
    KEY_PRICE,
    KEY_SIGNAL,
    KEY_SL,
    KEY_SYMBOL,
    KEY_TP,
    SIGNAL_WORKER_PREFIX,
    TABLE_ID,
    WORKER_PREFIX,
)
from .styles import CSS

_log = logging.getLogger(__name__)
_shutdown_event = threading.Event()


def _fetch_signal(symbol: str, cfg: AppConfig, delay: float = 0.0) -> UserAgentRecommendation | None:
    cached = recommendation_repo.get_latest_by_symbol(symbol)
    if cached is not None:
        created = cached.created_at.replace(tzinfo=timezone.utc) if cached.created_at.tzinfo is None else cached.created_at
        age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
        if age_minutes < cfg.signal_interval:
            return cached
    if not cfg.connector:
        return cached
    key_field = get_connector_key_field(cfg.connector)
    if key_field and not get_secret(key_field):
        _log.warning("signal skipped for %s: no API key for connector '%s'", symbol, cfg.connector)
        return cached
    if delay > 0:
        _shutdown_event.wait(timeout=delay)
        if _shutdown_event.is_set():
            return cached
    try:
        return signal_service.generate(symbol, cfg)
    except ConnectorAuthError:
        _log.warning("signal failed for %s: auth error via '%s'", symbol, cfg.connector)
        return cached
    except ConnectorNotConfiguredError:
        return cached


def _format_age(created_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    created = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
    age_seconds = int((now - created).total_seconds())
    if age_seconds < 3600:
        return f"{age_seconds // 60}m ago"
    if age_seconds < 86400:
        return f"{age_seconds // 3600}h ago"
    return f"{age_seconds // 86400}d ago"


def _signal_text(option: str) -> Text:
    upper = option.upper()
    if upper == "BUY":
        return Text(upper, style="bold green")
    if upper == "SELL":
        return Text(upper, style="bold red")
    return Text(upper, style="yellow")


def _change_text(change_pct: float) -> Text:
    arrow = "▲" if change_pct >= 0 else "▼"
    style = "green" if change_pct >= 0 else "red"
    return Text(f"{arrow} {abs(change_pct):.2f}%", style=style)


class StockGridWidget(Widget):
    DEFAULT_CSS = CSS
    can_focus = True

    class Selected(Message):
        def __init__(self, symbol: str) -> None:
            super().__init__()
            self.symbol = symbol

    class SignalRefreshRequested(Message):
        def __init__(self, symbol: str) -> None:
            super().__init__()
            self.symbol = symbol

    def compose(self) -> ComposeResult:
        yield DataTable(id=TABLE_ID, cursor_type="row")
        yield Static("No symbols. Press [S] to add.", id=EMPTY_ID, classes="-hidden")

    def on_mount(self) -> None:
        _shutdown_event.clear()

    def on_unmount(self) -> None:
        _shutdown_event.set()

    def on_resize(self) -> None:
        if self.is_mounted:
            self._fit_columns()

    def _table(self) -> DataTable:
        return self.query_one(f"#{TABLE_ID}", DataTable)

    def _empty(self) -> Static:
        return self.query_one(f"#{EMPTY_ID}", Static)

    def _has_row(self, symbol: str) -> bool:
        return symbol in self._table().rows

    def _safe_update_cell(self, symbol: str, column_key: str, value: object) -> None:
        if not self.is_attached or not self._has_row(symbol):
            return
        self._table().update_cell(symbol, column_key, value)

    def _init_columns(self, table: DataTable) -> None:
        table.add_column(COL_SYMBOL, key=KEY_SYMBOL)
        table.add_column(COL_PRICE, key=KEY_PRICE)
        table.add_column(COL_CHANGE, key=KEY_CHANGE)
        table.add_column(COL_SIGNAL, key=KEY_SIGNAL)
        table.add_column(COL_AGE, key=KEY_AGE)
        table.add_column(COL_SL, key=KEY_SL)
        table.add_column(COL_TP, key=KEY_TP)

    def _fit_columns(self) -> None:
        table = self._table()
        if not table.columns:
            return
        available = table.size.width
        if available <= 0:
            return
        keys = list(table.columns.keys())
        n = len(keys)
        padding = 2 * table.cell_padding * n
        usable = available - padding
        if usable < n:
            return
        weights = [
            COLUMN_WEIGHTS.get(str(k.value) if k.value is not None else '', 1) for k in keys
        ]
        total = sum(weights)
        widths = [max(1, usable * w // total) for w in weights]
        widths[-1] += usable - sum(widths)
        for key, width in zip(keys, widths):
            col = table.columns[key]
            col.auto_width = False
            col.width = width
        table._require_update_dimensions = True
        table.refresh()

    def _show_empty(self, empty: bool) -> None:
        table = self._table()
        empty_label = self._empty()
        if empty:
            table.add_class("-hidden")
            empty_label.remove_class("-hidden")
        else:
            table.remove_class("-hidden")
            empty_label.add_class("-hidden")


    def load(self) -> None:
        symbols = [ts.symbol for ts in symbol_repo.get_all()]
        table = self._table()
        table.clear(columns=True)
        if not symbols:
            self._show_empty(True)
            return
        self._show_empty(False)
        self._init_columns(table)
        for symbol in symbols:
            table.add_row(symbol, "loading…", "", "", "", "", "", key=symbol)
            cached = recommendation_repo.get_latest_by_symbol(symbol)
            if cached is not None:
                self._apply_signal(symbol, cached)
        cfg = app_config.load()
        provider = cfg.provider or "mock"
        service = create_service(provider)
        for symbol in symbols:
            self.run_worker(lambda s=symbol: service.get_meta(s), thread=True, name=f"{WORKER_PREFIX}{symbol}", exclusive=False, exit_on_error=False)
        for i, symbol in enumerate(symbols):
            self.run_worker(lambda s=symbol, c=cfg, d=i * 5.0: _fetch_signal(s, c, d), thread=True, name=f"{SIGNAL_WORKER_PREFIX}{symbol}", exclusive=False, exit_on_error=False)
        self.call_after_refresh(self._fit_columns)

    def _cursor_symbol(self) -> str | None:
        table = self._table()
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value is None:
            return None
        return str(row_key.value)

    def cursor_symbol(self) -> str | None:
        return self._cursor_symbol()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            self.post_message(self.Selected(str(event.row_key.value)))

    def action_refresh_signal(self) -> None:
        symbol = self._cursor_symbol()
        if symbol is None:
            return
        self.post_message(self.SignalRefreshRequested(symbol))

    def on_stock_grid_widget_signal_refresh_requested(self, event: SignalRefreshRequested) -> None:
        self._refresh_signal(event.symbol)

    def _refresh_signal(self, symbol: str) -> None:
        cfg = app_config.load()
        if not cfg.connector:
            self._set_signal_error(symbol, "⚠ no connector set")
            return
        key_field = get_connector_key_field(cfg.connector)
        if key_field and not get_secret(key_field):
            self._set_signal_error(symbol, f"⚠ no API key for {cfg.connector}")
            return
        self._set_signal_loading(symbol)
        self.run_worker(lambda s=symbol, c=cfg: signal_service.generate(s, c), thread=True, name=f"{SIGNAL_WORKER_PREFIX}{symbol}", exclusive=False, exit_on_error=False)

    def _apply_meta(self, symbol: str, meta: StockMeta) -> None:
        if meta.price is not None:
            self._safe_update_cell(symbol, KEY_PRICE, f"{meta.currency} {meta.price:,.2f}")
        else:
            self._safe_update_cell(symbol, KEY_PRICE, "N/A")
        if meta.change_pct is not None:
            self._safe_update_cell(symbol, KEY_CHANGE, _change_text(meta.change_pct))

    def _set_price_error(self, symbol: str, msg: str = "⚠ not supported") -> None:
        self._safe_update_cell(symbol, KEY_PRICE, msg)

    def _set_signal_loading(self, symbol: str) -> None:
        self._safe_update_cell(symbol, KEY_SIGNAL, "⟳ refreshing…")
        self._safe_update_cell(symbol, KEY_AGE, "")
        self._safe_update_cell(symbol, KEY_SL, "")
        self._safe_update_cell(symbol, KEY_TP, "")

    def _set_signal_error(self, symbol: str, msg: str = "⚠ error") -> None:
        self._safe_update_cell(symbol, KEY_SIGNAL, msg)
        self._safe_update_cell(symbol, KEY_AGE, "")
        self._safe_update_cell(symbol, KEY_SL, "")
        self._safe_update_cell(symbol, KEY_TP, "")

    def _apply_signal(self, symbol: str, rec: UserAgentRecommendation | None) -> None:
        if rec is None:
            self._safe_update_cell(symbol, KEY_SIGNAL, "")
            self._safe_update_cell(symbol, KEY_AGE, "")
            self._safe_update_cell(symbol, KEY_SL, "")
            self._safe_update_cell(symbol, KEY_TP, "")
            return
        option = rec.option.value if hasattr(rec.option, "value") else str(rec.option)
        self._safe_update_cell(symbol, KEY_SIGNAL, _signal_text(option))
        self._safe_update_cell(symbol, KEY_AGE, _format_age(rec.created_at))
        self._safe_update_cell(symbol, KEY_SL, f"{rec.stop_loss:.2f}" if rec.stop_loss is not None else "")
        self._safe_update_cell(symbol, KEY_TP, f"{rec.stop_profit:.2f}" if rec.stop_profit is not None else "")


    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        name = event.worker.name
        if name.startswith(SIGNAL_WORKER_PREFIX):
            symbol = name[len(SIGNAL_WORKER_PREFIX) :]
            if not self._has_row(symbol):
                return
            if event.worker.state == WorkerState.SUCCESS:
                self.call_after_refresh(self._apply_signal, symbol, event.worker.result)
            elif event.worker.state == WorkerState.ERROR:
                err = event.worker.error
                if isinstance(err, ConnectorAuthError):
                    msg = "⚠ API key not configured"
                elif isinstance(err, ConnectorNotConfiguredError):
                    msg = "⚠ no connector set"
                elif isinstance(err, ConnectorError):
                    msg = f"⚠ connector: {err}"
                else:
                    msg = f"⚠ {err}" if err else "⚠ error"
                self.call_after_refresh(self._set_signal_error, symbol, msg)
            return
        if not name.startswith(WORKER_PREFIX):
            return
        symbol = name[len(WORKER_PREFIX) :]
        if not self._has_row(symbol):
            return
        if event.worker.state == WorkerState.SUCCESS and event.worker.result is not None:
            self.call_after_refresh(self._apply_meta, symbol, event.worker.result)
        elif event.worker.state == WorkerState.ERROR:
            err = event.worker.error
            if isinstance(err, SourceAuthError):
                msg = "⚠ no API key"
            elif isinstance(err, SourceRateLimitError):
                msg = "⚠ rate limit"
            elif isinstance(err, SourceError):
                msg = "⚠ not supported"
            else:
                msg = "⚠ error"
            self.call_after_refresh(self._set_price_error, symbol, msg)
