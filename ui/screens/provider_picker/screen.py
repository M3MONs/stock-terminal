from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView

from infra import config as app_config
from data.registry import get_source_key_field, list_sources
from infra.security.keystore import get_secret, set_secret
from .constants import BINDINGS
from .styles import CSS


class ProviderPickerScreen(ModalScreen[str | None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        self._cfg = app_config.load()

    def compose(self) -> ComposeResult:
        items = self._build_items()
        with Vertical(id="dialog"):
            yield Label("Select Data Provider", id="title")
            yield ListView(*items, id="provider-list")
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
        for name in list_sources():
            label = f"● {name}" if name == self._cfg.provider else f"  {name}"
            item = ListItem(Label(label), name=name)
            if name == self._cfg.provider:
                item.add_class("active")
            items.append(item)
        return items

    def _current_key(self) -> str:
        field = get_source_key_field(self._cfg.provider)
        return get_secret(field) if field else ""

    def _has_key_field(self) -> bool:
        return bool(get_source_key_field(self._cfg.provider))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        provider = event.item.name
        if not provider:
            return
        self._cfg = self._cfg.model_copy(update={"provider": provider})
        key_input = self.query_one("#api-key-input", Input)
        key_input.value = self._current_key()
        has_key = self._has_key_field()
        self.query_one("#key-label", Label).display = has_key
        key_input.display = has_key
        self.query_one("#status", Label).update("")
        if has_key:
            key_input.focus()
        else:
            self.action_save()

    def on_mount(self) -> None:
        has_key = self._has_key_field()
        self.query_one("#key-label", Label).display = has_key
        self.query_one("#api-key-input", Input).display = has_key

    def action_save(self) -> None:
        field = get_source_key_field(self._cfg.provider)
        if field:
            key = self.query_one("#api-key-input", Input).value.strip()
            set_secret(field, key)
            if not key:
                status = self.query_one("#status", Label)
                status.remove_class("ok")
                status.update(f"Saved. Warning: no API key set for {self._cfg.provider}")
                cfg = app_config.load().model_copy(update={"provider": self._cfg.provider})
                app_config.save(cfg)
                return
        cfg = app_config.load().model_copy(update={"provider": self._cfg.provider})
        app_config.save(cfg)
        self.dismiss(self._cfg.provider)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.action_save()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
