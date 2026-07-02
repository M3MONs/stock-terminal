from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label

from models.user_agent import UserAgent
from infra import config as app_config
from persistence.repositories import user_agent_repo
from services.agent_service import AgentService
from ui.components.confirm_modal import ConfirmModal
from .constants import BINDINGS, COL_FILE, COL_NAME, COL_STATUS
from .editor import AgentEditorModal
from .styles import CSS


class AgentManagerScreen(ModalScreen[None]):
    DEFAULT_CSS = CSS
    BINDINGS = BINDINGS

    def __init__(self) -> None:
        super().__init__()
        self._service = AgentService(user_agent_repo, app_config)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Manage Agents", id="title")
            yield DataTable(id="agent-table", cursor_type="row")
            yield Input(placeholder="Agent name…", id="name-input")
            yield Label("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#agent-table", DataTable)
        table.clear(columns=True)
        table.add_column(COL_NAME, key="name")
        table.add_column(COL_FILE, key="file")
        table.add_column(COL_STATUS, key="status")
        for agent in self._service.get_all():
            status = "active" if agent.enabled else "inactive"
            table.add_row(agent.name, Path(agent.file_path).name, status, key=str(agent.id))

    def _selected_agent_id(self) -> int | None:
        table = self.query_one("#agent-table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value is None:
            return None
        return int(row_key.value)

    def _selected_agent(self) -> tuple[UserAgent, int] | None:
        agent_id = self._selected_agent_id()
        if agent_id is None:
            return None
        agent = next((a for a in self._service.get_all() if a.id == agent_id), None)
        if agent is None or agent.id is None:
            return None
        return agent, agent.id

    def action_add_agent(self) -> None:
        try:
            name_input = self.query_one("#name-input", Input)
            status = self.query_one("#status", Label)
            name = self._get_name_from_input(name_input)
            self._add_agent(name)
            name_input.clear()
            status.update("")
        except ValueError as e:
            status.update(str(e))
            return
        except Exception as e:
            status.update(f"Error: {e}")
            return
    
    def _get_name_from_input(self, name_input: Input) -> str:
        name = name_input.value.strip()
        if not name:
            raise ValueError("Name cannot be empty")
        return name
    
    def _add_agent(self, name: str) -> None:
        self._service.add(name)
        self._refresh_table()

    def action_edit_agent(self) -> None:
        result = self._selected_agent()
        if result is None:
            return
        agent, _ = result
        self.app.push_screen(AgentEditorModal(agent.name, agent.file_path, self._service))

    def action_delete_agent(self) -> None:
        result = self._selected_agent()
        if result is None:
            return
        agent, agent_id = result

        def _on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._service.remove(agent_id)
                self._refresh_table()

        self.app.push_screen(ConfirmModal(f"Remove {agent.name}?"), _on_confirm)

    def action_toggle_agent(self) -> None:
        result = self._selected_agent()
        if result is None:
            return
        agent, agent_id = result
        self._service.set_enabled(agent_id, not agent.enabled)
        self._refresh_table()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "name-input":
            event.stop()
            self.action_add_agent()

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            event.stop()
            self.dismiss(None)
