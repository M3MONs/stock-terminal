from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label

from models.user_agent_recommendation import UserAgentRecommendation
from repositories import recommendation_repo
from .constants import BINDINGS, COL_AGENT, COL_DATE, COL_OPTION, COL_OUTCOME, COL_SL, COL_SP, COL_SYMBOL, COL_TARGET
from .styles import CSS


class RecommendationHistoryScreen(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        self._all: list[UserAgentRecommendation] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Recommendation History", id="title")
            with Horizontal(id="filters"):
                yield Input(placeholder="Filter agent…", id="agent-filter")
                yield Input(placeholder="Filter symbol…", id="symbol-filter")
            yield DataTable(id="rec-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        self._all = recommendation_repo.list_all()
        self._build_columns()
        self._refresh_table()

    def _build_columns(self) -> None:
        table = self.query_one("#rec-table", DataTable)
        table.add_column(COL_DATE, key="date")
        table.add_column(COL_AGENT, key="agent")
        table.add_column(COL_SYMBOL, key="symbol")
        table.add_column(COL_OPTION, key="option")
        table.add_column(COL_SL, key="sl")
        table.add_column(COL_SP, key="sp")
        table.add_column(COL_TARGET, key="target")
        table.add_column(COL_OUTCOME, key="outcome")

    def _refresh_table(self) -> None:
        agent_q = self.query_one("#agent-filter", Input).value.strip().lower()
        symbol_q = self.query_one("#symbol-filter", Input).value.strip().lower()
        rows = self._get_refresh_table_rows(agent_q, symbol_q)
        table = self.query_one("#rec-table", DataTable)
        table.clear()
        self._add_rows(table, rows)

    def _get_refresh_table_rows(self, agent_q: str, symbol_q: str) -> list[UserAgentRecommendation]:
        return [r for r in self._all if (not agent_q or agent_q in r.agent.lower()) and (not symbol_q or symbol_q in r.symbol.lower())]

    @staticmethod
    def _add_rows(table: DataTable, recs: list[UserAgentRecommendation]) -> None:
        for r in recs:
            table.add_row(
                r.created_at.strftime("%Y-%m-%d %H:%M"),
                r.agent,
                r.symbol,
                r.option.value,
                str(r.stop_loss) if r.stop_loss is not None else "-",
                str(r.stop_profit) if r.stop_profit is not None else "-",
                r.target_date.isoformat() if r.target_date else "-",
                r.outcome.value if r.outcome else "-",
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in ("agent-filter", "symbol-filter"):
            self._refresh_table()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
