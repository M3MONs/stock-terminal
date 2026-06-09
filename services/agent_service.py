import sqlite3
from pathlib import Path

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
    def __init__(self, repository: UserAgentRepository) -> None:
        self._repository = repository

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
        self._repository.set_enabled(agent_id, enabled)

    def update_content(self, file_path: str, text: str) -> None:
        resolved = Path(file_path).resolve()
        if not resolved.is_relative_to(AGENTS_DIR.resolve()):
            raise ValueError(f"Refusing to write outside agents directory: {resolved}")
        resolved.write_text(text, encoding="utf-8")
