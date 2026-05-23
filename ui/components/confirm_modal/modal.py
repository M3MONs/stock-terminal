from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from .constants import CANCEL_BUTTON_ID, CONFIRM_BUTTON_ID, DIALOG_ID
from .styles import CSS


class ConfirmModal(ModalScreen[bool]):
    DEFAULT_CSS = CSS

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id=DIALOG_ID):
            yield Label(self._message)
            with Horizontal():
                yield Button("Yes", id=CONFIRM_BUTTON_ID, variant="error")
                yield Button("No", id=CANCEL_BUTTON_ID, variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == CONFIRM_BUTTON_ID)
