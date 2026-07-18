import logging
import threading

from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.widgets import DataTable, Footer, Header

from infra import config as app_config
from services.recommendation_evaluation_service import evaluate_all_pending as _eval_pending
from ui.components.confirm_modal import ConfirmModal
from ui.components.error_modal import ErrorModal
from ui.components.stock_grid import StockGridWidget
from ui.screens.agent_manager import AgentManagerScreen
from ui.screens.chart import ChartScreen
from ui.screens.connector_picker import ConnectorPickerScreen
from ui.screens.provider_picker import ProviderPickerScreen
from ui.screens.log_viewer import LogViewerScreen
from ui.screens.recommendation_history import RecommendationHistoryScreen
from ui.screens.signal_settings import SignalSettingsScreen
from ui.screens.symbol_manager import SymbolManagerScreen

from .constants import BINDINGS
from .help_modal import ShortcutsHelpModal

_log = logging.getLogger(__name__)


class Dashboard(App):
    TITLE = "Stock-Terminal"
    BINDINGS = BINDINGS

    _eval_thread: threading.Thread | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield StockGridWidget(id="stock-grid")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_subtitle()
        self.query_one(StockGridWidget).load()
        self.call_after_refresh(self._restore_grid_focus)
        self._run_evaluation()
        self.set_interval(15 * 60, self._run_evaluation)

    def _run_evaluation(self) -> None:
        if self._eval_thread is not None and self._eval_thread.is_alive():
            return
        thread = threading.Thread(
            target=self._do_evaluation,
            name="eval-pending",
            daemon=True,
        )
        self._eval_thread = thread
        thread.start()

    def _do_evaluation(self) -> None:
        try:
            _eval_pending()
        except Exception:
            _log.exception("background evaluation failed")
            self.call_from_thread(
                self.show_error,
                "Background evaluation failed. Check logs (l).",
            )

    def show_error(self, message: str, *, title: str = "Error") -> None:
        self.push_screen(ErrorModal(message, title=title))

    def _restore_grid_focus(self) -> None:
        grid = self.query_one(StockGridWidget)
        try:
            table = grid.query_one(DataTable)
        except NoMatches:
            grid.focus()
            return
        if table.row_count > 0:
            table.focus()
        else:
            grid.focus()

    def _refresh_subtitle(self) -> None:
        cfg = app_config.load()
        self.sub_title = f"Provider: {cfg.provider}"

    def action_show_shortcuts_help(self) -> None:
        self.push_screen(ShortcutsHelpModal())

    def action_push_symbols(self) -> None:
        def _cb(symbol: str | None) -> None:
            grid = self.query_one(StockGridWidget)
            grid.load()
            self.set_timer(0.05, self._restore_grid_focus)
            if symbol:
                self.push_screen(ChartScreen(symbol))

        self.push_screen(SymbolManagerScreen(), _cb)

    def on_stock_grid_widget_selected(self, event: StockGridWidget.Selected) -> None:
        self.push_screen(ChartScreen(event.symbol))

    def action_refresh_selected_row(self) -> None:
        if len(self.screen_stack) != 1:
            return
        self.query_one(StockGridWidget).action_refresh_signal()

    def action_request_quit(self) -> None:
        if len(self.screen_stack) == 1:

            def _on_confirm(confirmed: bool | None) -> None:
                if confirmed:
                    self.exit()

            self.push_screen(ConfirmModal("Quit the app?"), _on_confirm)

    def action_pick_provider(self) -> None:
        def _cb(provider: str | None) -> None:
            self._refresh_subtitle()
            grid = self.query_one(StockGridWidget)
            grid.load()
            self.set_timer(0.05, self._restore_grid_focus)

        self.push_screen(ProviderPickerScreen(), _cb)

    def action_push_agents(self) -> None:
        self.push_screen(AgentManagerScreen())

    def action_pick_connector(self) -> None:
        self.push_screen(ConnectorPickerScreen())

    def action_signal_settings(self) -> None:
        self.push_screen(SignalSettingsScreen())

    def action_push_history(self) -> None:
        self.push_screen(RecommendationHistoryScreen())

    def action_push_log_viewer(self) -> None:
        self.push_screen(LogViewerScreen())
