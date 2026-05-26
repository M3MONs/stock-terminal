from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label

from config import config as app_config
from repositories import symbol_repo
from services.symbol_service import SymbolService
from ui.components.confirm_modal import ConfirmModal
from validators import get_validator
from .constants import BINDINGS, COL_SYMBOL, COL_TAGS
from .styles import CSS


class SymbolManagerScreen(ModalScreen[str | None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        cfg = app_config.load()
        self._service = SymbolService(symbol_repo, get_validator(cfg.provider))

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Manage Symbols", id="title")
            yield DataTable(id="symbol-table", cursor_type="row")
            yield Input(placeholder="Add symbol…", id="symbol-input")
            yield Label("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#symbol-table", DataTable)
        table.clear(columns=True)
        table.add_column(COL_SYMBOL, key="symbol")
        table.add_column(COL_TAGS, key="tags")
        for ts in self._service.get_all():
            table.add_row(ts.symbol, ", ".join(ts.tags), key=ts.symbol)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        symbol = event.value.strip().upper()
        status = self.query_one("#status", Label)
        status.update(f"Validating {symbol}…")
        try:
            self._service.add(symbol)
        except ValueError as e:
            status.update(str(e))
            return
        event.input.clear()
        status.update("")
        self._refresh_table()

    def action_delete_symbol(self) -> None:
        table = self.query_one("#symbol-table", DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value is None:
            return
        symbol = row_key.value

        def _on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._service.remove(symbol)
                self._refresh_table()

        self.app.push_screen(ConfirmModal(f"Remove {symbol}?"), _on_confirm)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            self.dismiss(event.row_key.value)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
