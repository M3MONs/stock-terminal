import sqlite3
from pathlib import Path

from config.config import Config
from config.paths import AGENTS_DIR
from models.user_agent import UserAgent
from repositories.user_agent_repository import UserAgentRepository


def _validate_agent_name(name: str) -> None:
    if not name:
        raise ValueError("Agent name cannot be empty")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError("Agent name must not contain path separators or '..'")
    if Path(name).name != name:
        raise ValueError("Agent name must be a plain filename with no path components")


class AgentService:
    def __init__(self, repository: UserAgentRepository, cfg: Config | None = None) -> None:
        self._repository = repository
        self._cfg = cfg

    def get_all(self) -> list[UserAgent]:
        return self._repository.get_all()

    def add(self, name: str) -> UserAgent:
        _validate_agent_name(name)
        file_path = AGENTS_DIR / f"{name}.md"
        if not file_path.exists():
            file_path.write_text(f"# {name}\n\n")
        try:
            return self._repository.add(name, str(file_path))
        except sqlite3.IntegrityError:
            raise ValueError(f"Agent '{name}' already exists")

    def remove(self, agent_id: int) -> None:
        self._repository.remove(agent_id)

    def set_enabled(self, agent_id: int, enabled: bool) -> None:
        if enabled:
            self._repository.disable_all()
            self._repository.set_enabled(agent_id, True)
            agent = next((a for a in self._repository.get_all() if a.id == agent_id), None)
            agent_name = agent.name if agent else ""
        else:
            self._repository.set_enabled(agent_id, False)
            agent_name = ""
        if self._cfg is not None:
            cfg = self._cfg.load()
            self._cfg.save(cfg.model_copy(update={"signal_agent": agent_name}))

    def update_content(self, file_path: str, text: str) -> None:
        resolved = Path(file_path).resolve()
        if not resolved.is_relative_to(AGENTS_DIR.resolve()):
            raise ValueError(f"Refusing to write outside agents directory: {resolved}")
        resolved.write_text(text, encoding="utf-8")
