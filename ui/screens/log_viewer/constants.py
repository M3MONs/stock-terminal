from textual.binding import Binding

MAX_LINES = 500

BINDINGS = [
    Binding("escape", "dismiss_screen", "Close", priority=True),
    Binding("r", "action_refresh_log", "Refresh"),
]
