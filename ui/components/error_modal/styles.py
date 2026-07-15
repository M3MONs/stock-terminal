CSS = """
ErrorModal {
    align: center middle;
}
ErrorModal > Vertical#error-dialog {
    width: 50;
    height: auto;
    background: $surface;
    border: solid $error;
    padding: 1 2;
}
ErrorModal Label#error-title {
    text-style: bold;
    margin-bottom: 1;
}
ErrorModal Label {
    color: $error;
    margin-bottom: 1;
}
ErrorModal Horizontal { align: center middle; height: auto; }
ErrorModal Button { margin: 0 1; }
"""
