from textual.binding import Binding

EDITOR_CSS = """
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

BINDINGS = [
    Binding("escape", "dismiss_screen", "Close", priority=True),
    Binding("a", "add_agent", "Add"),
    Binding("e", "edit_agent", "Edit"),
    Binding("d", "delete_agent", "Delete"),
    Binding("t", "toggle_agent", "Toggle"),
]

COL_NAME = "Name"
COL_FILE = "File"
COL_STATUS = "Status"
