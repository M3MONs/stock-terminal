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
        current = self._cfg.signal_agent
        items = []
        none_label = "● (none)" if current == _NO_AGENT else "  (none)"
        none_item = ListItem(Label(none_label), name=_NO_AGENT)
        if current == _NO_AGENT:
            none_item.add_class("active")
        items.append(none_item)
        for agent in user_agent_repo.get_all():
            label = f"● {agent.name}" if agent.name == current else f"  {agent.name}"
            item = ListItem(Label(label), name=agent.name)
            if agent.name == current:
                item.add_class("active")
            items.append(item)
        return items

    def _tf_items(self, which: str) -> list[ListItem]:
        current = self._cfg.signal_timeframe_fast if which == "fast" else self._cfg.signal_timeframe_slow
        items = []
        for tf in Timeframe:
            label = f"● {tf.value}" if tf == current else f"  {tf.value}"
            item = ListItem(Label(label), name=tf.value)
            if tf == current:
                item.add_class("active")
            items.append(item)
        return items

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not event.item.name and event.list_view.id != "agent-list":
            return
        list_id = event.list_view.id
        if list_id == "agent-list":
            self._cfg = self._cfg.model_copy(update={"signal_agent": event.item.name or _NO_AGENT})
            self._refresh_list("agent-list", "agent")
            return
        tf = Timeframe(event.item.name)
        if list_id == "fast-tf-list":
            self._cfg = self._cfg.model_copy(update={"signal_timeframe_fast": tf})
            self._refresh_list("fast-tf-list", "fast")
        elif list_id == "slow-tf-list":
            self._cfg = self._cfg.model_copy(update={"signal_timeframe_slow": tf})
            self._refresh_list("slow-tf-list", "slow")

    def _refresh_list(self, list_id: str, which: str) -> None:
        lv = self.query_one(f"#{list_id}", ListView)
        lv.clear()
        if which == "agent":
            for item in self._agent_items():
                lv.append(item)
        else:
            for item in self._tf_items(which):
                lv.append(item)

    def action_save(self) -> None:
        interval_input = self.query_one("#interval-input", Input)
        try:
            interval = int(interval_input.value.strip())
        except ValueError:
            interval = self._cfg.signal_interval
        cfg = app_config.load().model_copy(update={
            "signal_interval": interval,
            "signal_timeframe_fast": self._cfg.signal_timeframe_fast,
            "signal_timeframe_slow": self._cfg.signal_timeframe_slow,
            "signal_agent": self._cfg.signal_agent,
        })
        app_config.save(cfg)
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.action_save()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
