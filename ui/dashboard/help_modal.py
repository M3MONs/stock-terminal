from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from .constants import help_text

CSS = """
ShortcutsHelpModal {
    align: center middle;
}
ShortcutsHelpModal > Static#help-content {
    width: 50;
    height: auto;
    max-height: 80%;
    background: $surface;
    border: solid $accent;
    padding: 1 2;
}
"""


class ShortcutsHelpModal(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Static(help_text(), id="help-content")

    def action_dismiss(self) -> None:
        self.dismiss(None)
