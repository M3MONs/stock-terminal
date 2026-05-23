from textual.binding import Binding

from models.timeframe import Timeframe

TIMEFRAME_ORDER = [
    Timeframe.M5, Timeframe.M15, Timeframe.M30,
    Timeframe.H1, Timeframe.H4, Timeframe.D1, Timeframe.W1,
]

BINDINGS = [
    Binding("escape", "pop_screen", "Back"),
    Binding("s", "pick_symbol", "Symbol"),
    Binding("[", "prev_timeframe", "TF◄"),
    Binding("]", "next_timeframe", "TF►"),
    Binding("+", "zoom_in", "Zoom+"),
    Binding("-", "zoom_out", "Zoom-"),
    Binding("left", "pan_left", "◄"),
    Binding("right", "pan_right", "►"),
]

INFO_PANEL_ID = "info-panel"
CHART_ID = "chart"
STATUS_ID = "status"
