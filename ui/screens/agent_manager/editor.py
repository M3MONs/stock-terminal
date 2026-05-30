from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea

CSS = """
AgentEditorModal {
    align: center middle;
}
AgentEditorModal > #dialog {
    width: 90;
    height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
AgentEditorModal > #dialog > #title { text-style: bold; margin-bottom: 1; }
AgentEditorModal > #dialog > #editor { height: 1fr; }
AgentEditorModal > #dialog > #buttons { height: 3; margin-top: 1; }
AgentEditorModal > #dialog > #buttons > Button { margin-right: 1; }
"""


class AgentEditorModal(ModalScreen[bool]):
    DEFAULT_CSS = CSS

    def __init__(self, name: str, file_path: str) -> None:
        super().__init__()
        self._name = name
        self._file_path = Path(file_path)

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
            self._file_path.write_text(text)
            self.dismiss(True)
        else:
            self.dismiss(False)
