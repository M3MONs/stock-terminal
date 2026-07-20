import logging
import threading
from datetime import datetime, timezone
from enum import Enum

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual.worker import Worker, WorkerState

from connectors.base import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorNotConfiguredError,
)
from connectors.preflight import connector_preflight
from data import create_service
from data.base import SourceAuthError, SourceError, SourceRateLimitError
from infra import config as app_config
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
    SIGNAL_STAGGER_SECONDS,
    TABLE_ID,
    WorkerKind,
)
from .styles import CSS

_log = logging.getLogger(__name__)
_shutdown_event = threading.Event()


def _fetch_signal(
    symbol: str, cfg: AppConfig, delay: float = 0.0
) -> UserAgentRecommendation | None:
    """Fetch a signal for a symbol."""
    cached = recommendation_repo.get_latest_by_symbol(symbol)
    if cached is not None:
        created = (
            cached.created_at.replace(tzinfo=timezone.utc)
            if cached.created_at.tzinfo is None
            else cached.created_at
        )
        age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
        if age_minutes < cfg.signal_interval:
            return cached
    try:
        connector_preflight(cfg)
    except ConnectorNotConfiguredError:
        return cached
    except ConnectorAuthError:
        _log.warning(
            "signal skipped for %s: no API key for connector '%s'",
            symbol,
            cfg.connector,
        )
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
    """Format the age of a recommendation."""
    now = datetime.now(timezone.utc)
    created = (
        created_at.replace(tzinfo=timezone.utc)
        if created_at.tzinfo is None
        else created_at
    )
    age_seconds = int((now - created).total_seconds())
    if age_seconds < 3600:
        return f"{age_seconds // 60}m ago"
    if age_seconds < 86400:
        return f"{age_seconds // 3600}h ago"
    return f"{age_seconds // 86400}d ago"


def _signal_text(option: str) -> Text:
    """Format the signal text."""
    upper = option.upper()
    if upper == "BUY":
        return Text(upper, style="bold green")
    if upper == "SELL":
        return Text(upper, style="bold red")
    return Text(upper, style="yellow")


def _change_text(change_pct: float) -> Text:
    """Format the change text."""
    arrow = "▲" if change_pct >= 0 else "▼"
    style = "green" if change_pct >= 0 else "red"
    return Text(f"{arrow} {abs(change_pct):.2f}%", style=style)


def _weighted_column_widths(usable: int, weights: list[int]) -> list[int]:
    """Allocate integer widths by weight; last column absorbs remainder."""
    total = sum(weights)
    widths = [max(1, usable * w // total) for w in weights]
    widths[-1] += usable - sum(widths)
    return widths


class SignalErrorMessage(Enum):
    AUTH = "⚠ API key not configured"
    NOT_CONFIGURED = "⚠ no connector set"
    CONNECTOR = "⚠ connector: {err}"
    UNKNOWN = "⚠ {err}"
    FALLBACK = "⚠ error"

    @classmethod
    def from_exception(cls, err: BaseException | None) -> str:
        if isinstance(err, ConnectorAuthError):
            return cls.AUTH.value
        if isinstance(err, ConnectorNotConfiguredError):
            return cls.NOT_CONFIGURED.value
        if isinstance(err, ConnectorError):
            return cls.CONNECTOR.value.format(err=err)
        if err is not None:
            return cls.UNKNOWN.value.format(err=err)
        return cls.FALLBACK.value


class MetaErrorMessage(Enum):
    AUTH = "⚠ no API key"
    RATE_LIMIT = "⚠ rate limit"
    NOT_SUPPORTED = "⚠ not supported"
    FALLBACK = "⚠ error"

    @classmethod
    def from_exception(cls, err: BaseException | None) -> str:
        if isinstance(err, SourceAuthError):
            return cls.AUTH.value
        if isinstance(err, SourceRateLimitError):
            return cls.RATE_LIMIT.value
        if isinstance(err, SourceError):
            return cls.NOT_SUPPORTED.value
        return cls.FALLBACK.value


def _format_worker_error(kind: WorkerKind, err: BaseException | None) -> str:
    """Format the worker error."""
    if kind is WorkerKind.SIGNAL:
        return SignalErrorMessage.from_exception(err)
    return MetaErrorMessage.from_exception(err)


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
        """On mount."""
        _shutdown_event.clear()

    def on_unmount(self) -> None:
        """On unmount."""
        _shutdown_event.set()

    def on_resize(self) -> None:
        """On resize."""
        if self.is_mounted:
            self._fit_columns()

    def _table(self) -> DataTable:
        """Get the table."""
        return self.query_one(f"#{TABLE_ID}", DataTable)

    def _empty(self) -> Static:
        """Get the empty label."""
        return self.query_one(f"#{EMPTY_ID}", Static)

    def _has_row(self, symbol: str) -> bool:
        """Check if the symbol has a row."""
        return symbol in self._table().rows

    def _safe_update_cell(self, symbol: str, column_key: str, value: object) -> None:
        """Safe update a cell."""
        if not self.is_attached or not self._has_row(symbol):
            return
        self._table().update_cell(symbol, column_key, value)

    def _init_columns(self, table: DataTable) -> None:
        """Initialize the columns."""
        table.add_column(COL_SYMBOL, key=KEY_SYMBOL)
        table.add_column(COL_PRICE, key=KEY_PRICE)
        table.add_column(COL_CHANGE, key=KEY_CHANGE)
        table.add_column(COL_SIGNAL, key=KEY_SIGNAL)
        table.add_column(COL_AGE, key=KEY_AGE)
        table.add_column(COL_SL, key=KEY_SL)
        table.add_column(COL_TP, key=KEY_TP)

    def _fit_columns(self) -> None:
        """Fit the columns."""
        table = self._table()
        if not table.columns:
            return
        available = table.size.width
        if available <= 0:
            return
        keys = list(table.columns.keys())
        n = len(keys)
        usable = available - 2 * table.cell_padding * n
        if usable < n:
            return
        weights = [
            COLUMN_WEIGHTS.get("" if k.value is None else str(k.value), 1)
            for k in keys
        ]
        widths = _weighted_column_widths(usable, weights)
        self._apply_column_widths(table, keys, widths)

    def _apply_column_widths(
        self, table: DataTable, keys: list, widths: list[int]
    ) -> None:
        """Apply computed widths and refresh the table."""
        for key, width in zip(keys, widths):
            col = table.columns[key]
            col.auto_width = False
            col.width = width
        table._require_update_dimensions = True
        table.refresh()

    def _show_empty(self, empty: bool) -> None:
        """Show the empty label."""
        table = self._table()
        empty_label = self._empty()
        if empty:
            table.add_class("-hidden")
            empty_label.remove_class("-hidden")
        else:
            table.remove_class("-hidden")
            empty_label.add_class("-hidden")

    def load(self) -> None:
        """Load the symbols."""
        symbols = [ts.symbol for ts in symbol_repo.get_all()]
        table = self._table()
        table.clear(columns=True)
        if not symbols:
            self._show_empty(True)
            return
        self._show_empty(False)
        self._seed_rows(table, symbols)
        self._start_background_fetches(symbols)
        self.call_after_refresh(self._fit_columns)

    def _seed_rows(self, table: DataTable, symbols: list[str]) -> None:
        """Initialize columns and seed rows with cached signals."""
        self._init_columns(table)
        for symbol in symbols:
            table.add_row(symbol, "loading…", "", "", "", "", "", key=symbol)
            cached = recommendation_repo.get_latest_by_symbol(symbol)
            if cached is not None:
                self._apply_signal(symbol, cached)

    def _start_background_fetches(self, symbols: list[str]) -> None:
        """Kick off meta and signal workers for each symbol."""
        cfg = app_config.load()
        service = create_service(cfg.provider or "mock")
        for symbol in symbols:
            self.run_worker(
                lambda s=symbol: service.get_meta(s),
                thread=True,
                name=symbol,
                group=WorkerKind.META,
                exclusive=False,
                exit_on_error=False,
            )
        for i, symbol in enumerate(symbols):
            self.run_worker(
                lambda s=symbol, c=cfg, d=i * SIGNAL_STAGGER_SECONDS: _fetch_signal(
                    s, c, d
                ),
                thread=True,
                name=symbol,
                group=WorkerKind.SIGNAL,
                exclusive=False,
                exit_on_error=False,
            )

    def _cursor_symbol(self) -> str | None:
        """Get the cursor symbol."""
        table = self._table()
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value is None:
            return None
        return str(row_key.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle the row selected event."""
        if event.row_key.value:
            self.post_message(self.Selected(str(event.row_key.value)))

    def action_refresh_signal(self) -> None:
        """Refresh the signal for the cursor symbol."""
        symbol = self._cursor_symbol()
        if symbol is None:
            return
        self.post_message(self.SignalRefreshRequested(symbol))

    def on_stock_grid_widget_signal_refresh_requested(
        self, event: SignalRefreshRequested
    ) -> None:
        """Handle the signal refresh requested event."""
        self._refresh_signal(event.symbol)

    def _refresh_signal(self, symbol: str) -> None:
        """Refresh the signal for the symbol."""
        cfg = app_config.load()
        try:
            connector_preflight(cfg)
        except (ConnectorNotConfiguredError, ConnectorAuthError) as e:
            self._set_signal_error(symbol, SignalErrorMessage.from_exception(e))
            return
        self._set_signal_loading(symbol)
        self.run_worker(
            lambda s=symbol, c=cfg: signal_service.generate(s, c),
            thread=True,
            name=symbol,
            group=WorkerKind.SIGNAL,
            exclusive=False,
            exit_on_error=False,
        )

    def _apply_meta(self, symbol: str, meta: StockMeta) -> None:
        """Apply the meta data to the symbol."""
        if meta.price is not None:
            self._safe_update_cell(
                symbol, KEY_PRICE, f"{meta.currency} {meta.price:,.2f}"
            )
        else:
            self._safe_update_cell(symbol, KEY_PRICE, "N/A")
        if meta.change_pct is not None:
            self._safe_update_cell(symbol, KEY_CHANGE, _change_text(meta.change_pct))

    def _set_signal_status(self, symbol: str, signal: object = "") -> None:
        """Set the signal status for the symbol."""
        self._safe_update_cell(symbol, KEY_SIGNAL, signal)
        self._safe_update_cell(symbol, KEY_AGE, "")
        self._safe_update_cell(symbol, KEY_SL, "")
        self._safe_update_cell(symbol, KEY_TP, "")

    def _set_price_error(self, symbol: str, msg: str = "⚠ not supported") -> None:
        """Set the price error for the symbol."""
        self._safe_update_cell(symbol, KEY_PRICE, msg)

    def _set_signal_loading(self, symbol: str) -> None:
        """Set the signal loading for the symbol."""
        self._set_signal_status(symbol, "⟳ refreshing…")

    def _set_signal_error(self, symbol: str, msg: str = "⚠ error") -> None:
        """Set the signal error for the symbol."""
        self._set_signal_status(symbol, msg)

    def _apply_signal(self, symbol: str, rec: UserAgentRecommendation | None) -> None:
        """Apply a signal to the symbol."""
        if rec is None:
            self._set_signal_status(symbol)
            return
        self._safe_update_cell(symbol, KEY_SIGNAL, _signal_text(str(rec.option)))
        self._safe_update_cell(symbol, KEY_AGE, _format_age(rec.created_at))
        self._safe_update_cell(
            symbol, KEY_SL, f"{rec.stop_loss:.2f}" if rec.stop_loss is not None else ""
        )
        self._safe_update_cell(
            symbol,
            KEY_TP,
            f"{rec.stop_profit:.2f}" if rec.stop_profit is not None else "",
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle the state change of a worker."""
        kind = WorkerKind(event.worker.group)
        symbol = event.worker.name
        if not symbol:
            raise RuntimeError(f"{kind} worker finished with empty name")
        if not self._has_row(symbol):
            return
        self._finish_worker(kind, symbol, event.worker)

    def _finish_worker(self, kind: WorkerKind, symbol: str, worker: Worker) -> None:
        """Finish a worker and call the appropriate function."""
        if worker.state == WorkerState.SUCCESS:
            if kind.require_result and worker.result is None:
                raise RuntimeError(
                    f"{kind} worker for {symbol!r} succeeded with no result"
                )
            self.call_after_refresh(self._success_fn(kind), symbol, worker.result)
        elif worker.state == WorkerState.ERROR:
            self.call_after_refresh(
                self._error_fn(kind),
                symbol,
                _format_worker_error(kind, worker.error),
            )

    def _success_fn(self, kind: WorkerKind):
        """Return the function to call when a worker succeeds."""
        return {
            WorkerKind.META: self._apply_meta,
            WorkerKind.SIGNAL: self._apply_signal,
        }[kind]

    def _error_fn(self, kind: WorkerKind):
        """Return the function to call when a worker fails."""
        return {
            WorkerKind.META: self._set_price_error,
            WorkerKind.SIGNAL: self._set_signal_error,
        }[kind]
