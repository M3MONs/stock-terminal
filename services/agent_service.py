import sqlite3
from pathlib import Path

from db import AGENTS_DIR
from models.user_agent import UserAgent
from repositories.user_agent_repository import UserAgentRepository


class AgentService:
    def __init__(self, repository: UserAgentRepository) -> None:
        self._repository = repository

    def get_all(self) -> list[UserAgent]:
        return self._repository.get_all()

    def add(self, name: str) -> UserAgent:
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
        Path(file_path).write_text(text, encoding="utf-8")
