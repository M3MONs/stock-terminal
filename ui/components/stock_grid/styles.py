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
    height: 7;
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
.stock-card .card-signal-buy {
    color: $success;
    text-style: bold;
}
.stock-card .card-signal-sell {
    color: $error;
    text-style: bold;
}
.stock-card .card-signal-hold {
    color: $warning;
}
.stock-card .card-signal-neutral {
    color: $text-muted;
}
.stock-card .card-sltp {
    color: $text-muted;
}
.stock-card .signal-row {
    height: 1;
}
.stock-card .signal-row Label {
    width: 1fr;
}
.stock-card .refresh-btn {
    width: 3;
    min-width: 3;
    height: 1;
    border: none;
    background: transparent;
    color: $text-muted;
    padding: 0;
}
.stock-card .refresh-btn:hover {
    color: $accent;
    background: transparent;
}
"""
