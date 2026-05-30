CSS = """
AgentManagerScreen {
    align: center middle;
}
AgentManagerScreen > #dialog {
    width: 80;
    height: auto;
    max-height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
AgentManagerScreen > #dialog > #agent-table { height: 1fr; }
AgentManagerScreen > #dialog > #title { text-style: bold; margin-bottom: 1; }
AgentManagerScreen > #dialog > #status { color: $error; }
"""
