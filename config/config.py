import logging

from pydantic import ValidationError

from models.app_config import AppConfig
from repositories.config_repository import ConfigRepository

_log = logging.getLogger(__name__)


class Config:
    def __init__(self, repo: ConfigRepository) -> None:
        self.repo = repo

    def load(self) -> AppConfig:
        data = self.repo.get_all()
        if not data:
            return AppConfig()
        try:
            return AppConfig.model_validate(data)
        except ValidationError:
            _log.error("corrupt app_config in DB, falling back to defaults")
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        items = {k: str(v) for k, v in config.model_dump().items()}
        self.repo.save_all(items)
