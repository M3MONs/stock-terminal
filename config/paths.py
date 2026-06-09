from pathlib import Path

_APP_DIR_NAME = ".stock-terminal"

APP_DIR = Path.home() / _APP_DIR_NAME
AGENTS_DIR = APP_DIR / "agents"
LOG_PATH = APP_DIR / "app.log"
