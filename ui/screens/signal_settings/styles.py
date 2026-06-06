CSS = """
SignalSettingsScreen {
    align: center middle;
}
SignalSettingsScreen > #dialog {
    width: 50;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
SignalSettingsScreen > #dialog > Label { margin-top: 1; }
SignalSettingsScreen > #dialog > #title { text-style: bold; margin-top: 0; margin-bottom: 1; }
SignalSettingsScreen ListItem.active Label { color: $success; text-style: bold; }
"""
