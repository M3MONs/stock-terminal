from textual.binding import Binding

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
