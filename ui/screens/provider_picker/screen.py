from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, ListView, ListItem

from config import config as app_config
from data.registry import list_sources
from .styles import CSS
from .constants import BINDINGS


class ProviderPickerScreen(ModalScreen[str | None]):
    DEFAULT_CSS = CSS

    BINDINGS = BINDINGS

    def compose(self) -> ComposeResult:
        cfg = app_config.load()
        current = cfg.provider
        items = self._generate_items(current)
        with Vertical(id="dialog"):
            yield Label("Select Data Provider", id="title")
            yield ListView(*items, id="provider-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        provider = event.item.name

        if not provider:
            return

        cfg = app_config.load()
        app_config.save(cfg.model_copy(update={"provider": provider}))
        self.dismiss(provider)

    def _generate_items(self, current: str) -> list[ListItem]:
        items = []
        for p in list_sources():
            label = f"● {p}" if p == current else f"  {p}"
            item = ListItem(Label(label), name=p)
            if p == current:
                item.add_class("active")
            items.append(item)
        return items

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
