CSS = """
ProviderPickerScreen {
        align: center middle;
    }
    ProviderPickerScreen > #dialog {
        width: 50;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    ProviderPickerScreen > #dialog > #title { text-style: bold; margin-bottom: 1; }
    ProviderPickerScreen > #dialog > #key-label { margin-top: 1; }
    ProviderPickerScreen > #dialog > #status { color: $error; }
    ProviderPickerScreen ListItem.active Label { color: $success; text-style: bold; }
    ProviderPickerScreen > #dialog > #status.ok { color: $success; }
"""
