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
        with Vertical(id="dialog"):
            yield Label("Select Data Provider", id="title")
            yield ListView(
                *[ListItem(Label(p), name=p) for p in list_sources()],
                id="provider-list",
            )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        provider = event.item.name
        if provider:
            cfg = app_config.load()
            app_config.save(cfg.model_copy(update={"provider": provider}))
            self.dismiss(provider)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
