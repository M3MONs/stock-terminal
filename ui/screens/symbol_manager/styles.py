CSS = """
SymbolManagerScreen {
    align: center middle;
}
SymbolManagerScreen > #dialog {
    width: 70;
    height: auto;
    max-height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
SymbolManagerScreen > #dialog > #symbol-table { height: 1fr; }
SymbolManagerScreen > #dialog > #title { text-style: bold; margin-bottom: 1; }
SymbolManagerScreen > #dialog > #status { color: $error; }
"""
