from textual.binding import Binding

BINDINGS = [
    Binding("escape", "dismiss_screen", "Close", priority=True),
]

COL_DATE = "Date"
COL_AGENT = "Agent"
COL_SYMBOL = "Symbol"
COL_OPTION = "Option"
COL_SL = "Stop Loss"
COL_SP = "Take Profit"
COL_TARGET = "Target Date"
COL_OUTCOME = "Outcome"

ICON_SUCCESS = "✓"
ICON_FAILURE = "✗"
ICON_NEUTRAL = "–"
