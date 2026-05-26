CSS = """
StockGridWidget {
    height: 1fr;
    overflow-y: auto;
}
#stock-cards {
    grid-size: 4;
    grid-gutter: 1;
    padding: 1;
    height: auto;
}
.stock-card {
    height: 5;
    border: solid $panel;
    padding: 0 1;
    background: $surface;
}
.stock-card:hover {
    border: solid $accent;
}
.stock-card:focus {
    border: solid $accent;
}
.stock-card .card-symbol {
    text-style: bold;
}
.stock-card .card-price {
    color: $text;
}
.stock-card .card-change-up {
    color: $success;
}
.stock-card .card-change-down {
    color: $error;
}
.stock-card .card-loading {
    color: $text-muted;
}
"""
