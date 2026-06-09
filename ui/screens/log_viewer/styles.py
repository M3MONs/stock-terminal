CSS = """
LogViewerScreen {
    align: center middle;
}
LogViewerScreen > #dialog {
    width: 90%;
    height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
LogViewerScreen > #dialog > #title {
    text-style: bold;
    margin-bottom: 1;
}
LogViewerScreen > #dialog > #log-scroll {
    height: 1fr;
    border: solid $panel;
}
LogViewerScreen > #dialog > #log-scroll > #log-content {
    padding: 0 1;
}
"""
