CSS = """
ConnectorPickerScreen {
    align: center middle;
}
ConnectorPickerScreen > #dialog {
    width: 50;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
ConnectorPickerScreen > #dialog > #title { text-style: bold; margin-bottom: 1; }
ConnectorPickerScreen > #dialog > #key-label { margin-top: 1; }
ConnectorPickerScreen > #dialog > #status { color: $error; }
ConnectorPickerScreen ListItem.active Label { color: $success; text-style: bold; }
ConnectorPickerScreen > #dialog > #status.ok { color: $success; }
"""
