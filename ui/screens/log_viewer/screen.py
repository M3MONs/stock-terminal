from __future__ import annotations

from collections import deque

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Static

from db import LOG_PATH
from .constants import BINDINGS, MAX_LINES
from .styles import CSS


class LogViewerScreen(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"App Log  (last {MAX_LINES} lines · {LOG_PATH})", id="title")
            with ScrollableContainer(id="log-scroll"):
                yield Static("", id="log-content", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self._load_log()
        self.call_after_refresh(self._scroll_to_bottom)

    def _load_log(self) -> None:
        content = self.query_one("#log-content", Static)
        if not LOG_PATH.exists():
            content.update("No log file yet.")
            return
        with LOG_PATH.open(encoding="utf-8", errors="replace") as f:
            lines = deque(f, maxlen=MAX_LINES)
        content.update("".join(lines).rstrip())

    def _scroll_to_bottom(self) -> None:
        self.query_one("#log-scroll", ScrollableContainer).scroll_end(animate=False)

    def action_refresh_log(self) -> None:
        self._load_log()
        self.call_after_refresh(self._scroll_to_bottom)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
