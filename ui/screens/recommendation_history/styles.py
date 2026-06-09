CSS = """
RecommendationHistoryScreen {
    align: center middle;
}
RecommendationHistoryScreen > #dialog {
    width: 120;
    height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
RecommendationHistoryScreen > #dialog > #title { text-style: bold; margin-bottom: 1; }
RecommendationHistoryScreen > #dialog > #filters { height: 3; }
RecommendationHistoryScreen > #dialog > #filters > Input { width: 1fr; margin-right: 1; }
RecommendationHistoryScreen > #dialog > #rec-table { height: 1fr; }
"""
