import logging
import threading
from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.css.query import NoMatches
from textual.events import Click, Key
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Static
from textual.worker import Worker, WorkerState

from config import config as app_config
from connectors.base import ConnectorAuthError, ConnectorError, ConnectorNotConfiguredError
from connectors.registry import get_connector_key_field
from security.keystore import get_secret
from data import create_service
from data.base import SourceAuthError, SourceError, SourceRateLimitError
from models.app_config import AppConfig
from models.stock_meta import StockMeta
from models.user_agent_recommendation import UserAgentRecommendation
from repositories import recommendation_repo, symbol_repo
from services import signal_service
from .constants import (
    CARDS_GRID_ID,
    CARD_CLASS,
    CLASS_SYMBOL,
    CLASS_PRICE,
    CLASS_CHANGE_UP,
    CLASS_CHANGE_DOWN,
    CLASS_LOADING,
    CLASS_SIGNAL_BUY,
    CLASS_SIGNAL_SELL,
    CLASS_SIGNAL_HOLD,
    CLASS_SIGNAL_NEUTRAL,
    PRICE_ID_PREFIX,
    CHANGE_ID_PREFIX,
    SIGNAL_ID_PREFIX,
    SLTP_ID_PREFIX,
    CLASS_SLTP,
    WORKER_PREFIX,
    SIGNAL_WORKER_PREFIX,
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


class StockCard(Widget):
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

    def __init__(self, symbol: str, initial_signal: UserAgentRecommendation | None = None) -> None:
        super().__init__(classes=CARD_CLASS)
        self._symbol = symbol
        self._safe_id = symbol.replace(".", "-")
        self._initial_signal = initial_signal
        self._pending_error: str | None = None
        self._pending_meta: StockMeta | None = None

    def on_mount(self) -> None:
        if self._pending_meta is not None:
            self.update(self._pending_meta)
        elif self._pending_error is not None:
            self._apply_error(self._pending_error)
        elif self._initial_signal is not None:
            self.update_signal(self._initial_signal)

    def on_click(self, event: Click) -> None:
        self.post_message(self.Selected(self._symbol))

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self.post_message(self.Selected(self._symbol))
        elif event.key == "r":
            self.post_message(self.SignalRefreshRequested(self._symbol))

    def compose(self) -> ComposeResult:
        yield Label(self._symbol, classes=CLASS_SYMBOL)
        yield Label("loading…", classes=CLASS_LOADING, id=f"{PRICE_ID_PREFIX}{self._safe_id}")
        yield Label("", id=f"{CHANGE_ID_PREFIX}{self._safe_id}")
        with Horizontal(classes="signal-row"):
            yield Label("", id=f"{SIGNAL_ID_PREFIX}{self._safe_id}", classes=CLASS_SIGNAL_NEUTRAL)
            yield Button("⟳", id=f"refresh-{self._safe_id}", classes="refresh-btn")
        yield Label("", id=f"{SLTP_ID_PREFIX}{self._safe_id}", classes=CLASS_SLTP)

    def update(self, meta: StockMeta) -> None:
        if not self.is_attached:
            return
        try:
            price_label = self.query_one(f"#{PRICE_ID_PREFIX}{self._safe_id}", Label)
            change_label = self.query_one(f"#{CHANGE_ID_PREFIX}{self._safe_id}", Label)
        except NoMatches:
            self._pending_meta = meta
            return

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.SignalRefreshRequested(self._symbol))

    def _apply_error(self, msg: str) -> None:
        label = self.query_one(f"#{PRICE_ID_PREFIX}{self._safe_id}", Label)
        label.remove_class(CLASS_LOADING)
        label.update(msg)

    def set_error(self, msg: str = "⚠ not supported") -> None:
        if not self.is_attached:
            return
        try:
            self._apply_error(msg)
        except NoMatches:
            self._pending_error = msg

    def set_signal_loading(self) -> None:
        if not self.is_attached:
            return
        label = self.query_one(f"#{SIGNAL_ID_PREFIX}{self._safe_id}", Label)
        label.remove_class(CLASS_SIGNAL_BUY, CLASS_SIGNAL_SELL, CLASS_SIGNAL_HOLD, CLASS_SIGNAL_NEUTRAL)
        label.add_class(CLASS_SIGNAL_NEUTRAL)
        label.update("⟳ refreshing…")
        self.query_one(f"#{SLTP_ID_PREFIX}{self._safe_id}", Label).update("")
        self.query_one(f"#refresh-{self._safe_id}", Button).disabled = True

    def set_signal_error(self, msg: str = "⚠ error") -> None:
        if not self.is_attached:
            return
        label = self.query_one(f"#{SIGNAL_ID_PREFIX}{self._safe_id}", Label)
        label.remove_class(CLASS_SIGNAL_BUY, CLASS_SIGNAL_SELL, CLASS_SIGNAL_HOLD, CLASS_SIGNAL_NEUTRAL)
        label.add_class(CLASS_SIGNAL_NEUTRAL)
        label.update(msg)
        self.query_one(f"#refresh-{self._safe_id}", Button).disabled = False

    def update_signal(self, rec: UserAgentRecommendation | None) -> None:
        if not self.is_attached:
            return
        label = self.query_one(f"#{SIGNAL_ID_PREFIX}{self._safe_id}", Label)
        sltp_label = self.query_one(f"#{SLTP_ID_PREFIX}{self._safe_id}", Label)
        label.remove_class(CLASS_SIGNAL_BUY, CLASS_SIGNAL_SELL, CLASS_SIGNAL_HOLD, CLASS_SIGNAL_NEUTRAL)
        if rec is None:
            label.add_class(CLASS_SIGNAL_NEUTRAL)
            label.update("")
            sltp_label.update("")
            return
        now = datetime.now(timezone.utc)
        created = rec.created_at.replace(tzinfo=timezone.utc) if rec.created_at.tzinfo is None else rec.created_at
        age_seconds = int((now - created).total_seconds())
        if age_seconds < 3600:
            age_str = f"{age_seconds // 60}m ago"
        elif age_seconds < 86400:
            age_str = f"{age_seconds // 3600}h ago"
        else:
            age_str = f"{age_seconds // 86400}d ago"
        option = rec.option.upper()
        if option == "BUY":
            label.add_class(CLASS_SIGNAL_BUY)
        elif option == "SELL":
            label.add_class(CLASS_SIGNAL_SELL)
        else:
            label.add_class(CLASS_SIGNAL_HOLD)
        label.update(f"▶ {option}  {age_str}")
        parts = []
        if rec.stop_loss is not None:
            parts.append(f"SL {rec.stop_loss:.2f}")
        if rec.stop_profit is not None:
            parts.append(f"TP {rec.stop_profit:.2f}")
        sltp_label.update("  ".join(parts))
        self.query_one(f"#refresh-{self._safe_id}", Button).disabled = False


class StockGridWidget(Widget):
    DEFAULT_CSS = CSS
    can_focus = True

    def compose(self) -> ComposeResult:
        yield Grid(id=CARDS_GRID_ID)

    def on_mount(self) -> None:
        _shutdown_event.clear()

    def on_unmount(self) -> None:
        _shutdown_event.set()

    def load(self) -> None:
        symbols = [ts.symbol for ts in symbol_repo.get_all()]
        grid = self.query_one(f"#{CARDS_GRID_ID}", Grid)
        grid.remove_children()
        if not symbols:
            grid.mount(Static("No symbols. Press [S] to add.", classes=CLASS_LOADING))
            return
        for symbol in symbols:
            cached = recommendation_repo.get_latest_by_symbol(symbol)
            grid.mount(StockCard(symbol, initial_signal=cached))
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
        for i, symbol in enumerate(symbols):
            self.run_worker(
                lambda s=symbol, c=cfg, d=i * 5.0: _fetch_signal(s, c, d),
                thread=True,
                name=f"{SIGNAL_WORKER_PREFIX}{symbol}",
                exclusive=False,
                exit_on_error=False,
            )

    def on_stock_card_signal_refresh_requested(self, event: StockCard.SignalRefreshRequested) -> None:
        cards = self.query(StockCard)
        card = next((c for c in cards if c._symbol == event.symbol), None)
        cfg = app_config.load()
        if not cfg.connector:
            if card is not None:
                card.set_signal_error("⚠ no connector set")
            return
        key_field = get_connector_key_field(cfg.connector)
        if key_field and not get_secret(key_field):
            if card is not None:
                card.set_signal_error(f"⚠ no API key for {cfg.connector}")
            return
        if card is not None:
            card.set_signal_loading()
        self.run_worker(
            lambda s=event.symbol, c=cfg: signal_service.generate(s, c),
            thread=True,
            name=f"{SIGNAL_WORKER_PREFIX}{event.symbol}",
            exclusive=False,
            exit_on_error=False,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        name = event.worker.name
        if name.startswith(SIGNAL_WORKER_PREFIX):
            symbol = name[len(SIGNAL_WORKER_PREFIX) :]
            cards = self.query(StockCard)
            card = next((c for c in cards if c._symbol == symbol), None)
            if card is None:
                return
            if event.worker.state == WorkerState.SUCCESS:
                self.call_after_refresh(card.update_signal, event.worker.result)
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
                self.call_after_refresh(card.set_signal_error, msg)
            return
        if not name.startswith(WORKER_PREFIX):
            return
        symbol = name[len(WORKER_PREFIX) :]
        cards = self.query(StockCard)
        card = next((c for c in cards if c._symbol == symbol), None)
        if card is None:
            return
        if event.worker.state == WorkerState.SUCCESS and event.worker.result is not None:
            self.call_after_refresh(card.update, event.worker.result)
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
            self.call_after_refresh(card.set_error, msg)
