from textual.binding import Binding

BINDINGS = [
    Binding("escape", "dismiss_screen", "Close", priority=True),
    Binding("d", "delete_symbol", "Delete"),
]

COL_SYMBOL = "Symbol"
COL_TAGS = "Tags"
