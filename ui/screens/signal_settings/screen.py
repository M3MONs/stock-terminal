from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView

from config import config as app_config
from models.timeframe import Timeframe
from repositories import user_agent_repo
from .constants import BINDINGS
from .styles import CSS

_NO_AGENT = ""
_LIST_CONFIG = {
    "agent-list": (
        "signal_agent",
        lambda value: value or _NO_AGENT,
        "agent",
    ),
    "fast-tf-list": (
        "signal_timeframe_fast",
        lambda value: Timeframe(value) if value else None,
        "fast",
    ),
    "slow-tf-list": (
        "signal_timeframe_slow",
        lambda value: Timeframe(value) if value else None,
        "slow",
    ),
}


class SignalSettingsScreen(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        self._cfg = app_config.load()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Signal Settings", id="title")
            yield Label("Agent:")
            yield ListView(*self._agent_items(), id="agent-list")
            yield Label("Interval (minutes):")
            yield Input(
                value=str(self._cfg.signal_interval),
                placeholder="60",
                id="interval-input",
            )
            yield Label("Fast timeframe (signal):")
            yield ListView(*self._tf_items("fast"), id="fast-tf-list")
            yield Label("Slow timeframe (context):")
            yield ListView(*self._tf_items("slow"), id="slow-tf-list")
        yield Footer()

    def _agent_items(self) -> list[ListItem]:
        values = [(_NO_AGENT, "(none)")]

        values.extend(
            (agent.name, agent.name)
            for agent in user_agent_repo.get_all()
        )

        return self._build_list_items(
            values,
            self._cfg.signal_agent,
        )

    def _tf_items(self, which: str) -> list[ListItem]:
        current = (
            self._cfg.signal_timeframe_fast
            if which == "fast"
            else self._cfg.signal_timeframe_slow
        )

        values = [
            (tf.value, tf.value)
            for tf in Timeframe
        ]

        return self._build_list_items(
            values,
            current.value,
        )

    def _build_list_items(
        self,
        values: list[tuple[str, str]],
        current: str,
    ) -> list[ListItem]:
        items = []

        for name, display in values:
            is_active = name == current

            item = ListItem(
                Label(f"● {display}" if is_active else f"  {display}"),
                name=name,
            )

            if is_active:
                item.add_class("active")

            items.append(item)

        return items

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id is None or event.item.name is None:
            return

        config = _LIST_CONFIG.get(event.list_view.id)

        if config is None:
            return

        cfg_field, converter, refresh_mode = config

        value = converter(event.item.name)

        if value is None:
            return

        self._update_cfg_and_refresh(
            cfg_field,
            value,
            event.list_view.id,
            refresh_mode,
        )

    def _update_cfg_and_refresh(
        self,
        cfg_field: str,
        cfg_value: Any,
        list_id: str,
        refresh_mode: str,
    ) -> None:
        self._cfg = self._cfg.model_copy(update={cfg_field: cfg_value})
        self._refresh_list(list_id, refresh_mode)

    def _refresh_list(self, list_id: str, which: str) -> None:
        lv = self.query_one(f"#{list_id}", ListView)
        lv.clear()
        self._append_list_view(lv, self._agent_items() if which == "agent" else self._tf_items(which))

    def _append_list_view(self, lv: ListView, items: list[ListItem]) -> None:
        for item in items:
            lv.append(item)

    def action_save(self) -> None:
        interval_input = self.query_one("#interval-input", Input)
        interval = self._get_interval_from_input(interval_input)
        self._save_cfg_signal(interval)
        self.dismiss(None)

    def _get_interval_from_input(self, interval_input: Input) -> int:
        try:
            return int(interval_input.value.strip())
        except ValueError:
            return self._cfg.signal_interval

    def _save_cfg_signal(self, interval: int) -> None:
        cfg = app_config.load().model_copy(
            update={
                "signal_interval": interval,
                "signal_timeframe_fast": self._cfg.signal_timeframe_fast,
                "signal_timeframe_slow": self._cfg.signal_timeframe_slow,
                "signal_agent": self._cfg.signal_agent,
            }
        )
        app_config.save(cfg)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.action_save()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
