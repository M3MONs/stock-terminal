from textual.binding import Binding

# (group, key, action, footer_desc, show_in_footer)
_SHORTCUTS: list[tuple[str, str, str, str, bool]] = [
    ("Watchlist", "r", "refresh_selected_row", "Refresh", True),
    ("Configuration", "s", "push_symbols", "Symbols", False),
    ("Configuration", "p", "pick_provider", "Provider", False),
    ("Configuration", "c", "pick_connector", "Connector", False),
    ("Configuration", "a", "push_agents", "Agents", False),
    ("Configuration", "i", "signal_settings", "Signals", False),
    ("Tools", "h", "push_history", "History", False),
    ("Tools", "l", "push_log_viewer", "Logs", False),
    ("App", "question_mark", "show_shortcuts_help", "Help", True),
    ("App", "q", "request_quit", "Quit", True),
]

BINDINGS = [
    Binding(
        key,
        action,
        desc,
        show=show,
        key_display="?" if key == "question_mark" else None,
    )
    for _, key, action, desc, show in _SHORTCUTS
]


def help_text() -> str:
    lines = ["Keyboard shortcuts", ""]
    group: str | None = None
    for g, key, _, desc, _ in _SHORTCUTS:
        if g != group:
            if group is not None:
                lines.append("")
            lines.append(g)
            group = g
        display = "?" if key == "question_mark" else key
        lines.append(f"  {display:<8}{desc}")
    lines.extend(
        [
            "",
            "  Enter    Open chart for selected symbol",
            "  Ctrl+P   Command palette (Keys, Quit, …)",
        ]
    )
    return "\n".join(lines)
