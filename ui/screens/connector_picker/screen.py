from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView
from textual.worker import Worker, WorkerState

from infra import config as app_config
from connectors.registry import get_connector, get_connector_key_field, list_connectors
from infra.security.keystore import get_secret, set_secret
from .constants import BINDINGS
from .styles import CSS


class ConnectorPickerScreen(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        self._cfg = app_config.load()

    def compose(self) -> ComposeResult:
        items = self._build_items()
        with Vertical(id="dialog"):
            yield Label("Select AI Connector", id="title")
            yield ListView(*items, id="connector-list")
            yield Label("API Key:", id="key-label")
            yield Input(
                value=self._current_key(),
                placeholder="Paste API key…",
                id="api-key-input",
                password=True,
            )
            yield Label("", id="status")
        yield Footer()

    def _build_items(self) -> list[ListItem]:
        items = []
        for name in list_connectors():
            label = f"● {name}" if name == self._cfg.connector else f"  {name}"
            item = ListItem(Label(label), name=name)
            if name == self._cfg.connector:
                item.add_class("active")
            items.append(item)
        return items

    def _current_key(self) -> str:
        field = get_connector_key_field(self._cfg.connector)
        return get_secret(field) if field else ""

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        connector = event.item.name
        if not connector:
            return
        self._cfg = self._cfg.model_copy(update={"connector": connector})
        key_input = self.query_one("#api-key-input", Input)
        key_input.value = self._current_key()
        self.query_one("#status", Label).update("")

    def action_save(self) -> None:
        key_input = self.query_one("#api-key-input", Input)
        status = self.query_one("#status", Label)
        field = get_connector_key_field(self._cfg.connector)
        key = key_input.value.strip()
        if field:
            set_secret(field, key)
        cfg = app_config.load().model_copy(update={"connector": self._cfg.connector})
        app_config.save(cfg)
        if field and not key:
            status.remove_class("ok")
            status.update(f"Saved. Warning: no API key set for {self._cfg.connector}")
        else:
            self.dismiss(None)

    def action_test_connection(self) -> None:
        key = self.query_one("#api-key-input", Input).value.strip()
        status = self.query_one("#status", Label)
        status.remove_class("ok")
        status.update("Testing…")
        connector_name = self._cfg.connector
        self.run_worker(
            lambda: get_connector(connector_name, api_key=key).ping(),
            thread=True,
            name="ping_connector",
            exclusive=True,
            exit_on_error=False,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "ping_connector":
            return
        status = self.query_one("#status", Label)
        if event.worker.state == WorkerState.SUCCESS:
            status.add_class("ok")
            status.update("✓ Connected")
        elif event.worker.state == WorkerState.ERROR:
            status.remove_class("ok")
            status.update(str(event.worker.error))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.action_save()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
