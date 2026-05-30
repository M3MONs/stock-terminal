from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea

from services.agent_service import AgentService
from ui.screens.agent_manager.constants import EDITOR_CSS


class AgentEditorModal(ModalScreen[bool]):
    DEFAULT_CSS = EDITOR_CSS

    def __init__(self, name: str, file_path: str, service: AgentService) -> None:
        super().__init__()
        self._name = name
        self._file_path = Path(file_path)
        self._service = service

    def compose(self) -> ComposeResult:
        content = self._file_path.read_text() if self._file_path.exists() else f"# {self._name}\n\n"
        with Vertical(id="dialog"):
            yield Label(f"Edit: {self._name}", id="title")
            yield TextArea(content, id="editor")
            with Horizontal(id="buttons"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            text = self.query_one("#editor", TextArea).text
            self._service.update_content(str(self._file_path), text)
            self.dismiss(True)
        else:
            self.dismiss(False)
