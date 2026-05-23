CSS = """
StockInfoPanel {
    layout: vertical;
    width: 20;
    height: 1fr;
    border-right: solid $accent;
    padding: 1;
}
StockInfoPanel > Rule {
    height: 1fr;
}
StockInfoPanel > #stock-name {
    text-style: bold;
    width: 1fr;
}
StockInfoPanel > #stock-price {
    width: 1fr;
}
"""
