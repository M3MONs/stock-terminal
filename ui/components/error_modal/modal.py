from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from .constants import DIALOG_ID, OK_BUTTON_ID, TITLE_ID
from .styles import CSS


class ErrorModal(ModalScreen[None]):
    DEFAULT_CSS = CSS

    def __init__(self, message: str, *, title: str = "Error") -> None:
        super().__init__()
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id=DIALOG_ID):
            yield Label(self._title, id=TITLE_ID)
            yield Label(self._message)
            with Horizontal():
                yield Button("OK", id=OK_BUTTON_ID, variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == OK_BUTTON_ID:
            self.dismiss(None)
