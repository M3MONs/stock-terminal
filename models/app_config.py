from pydantic import BaseModel

from models.timeframe import Timeframe


class AppConfig(BaseModel):
    provider: str = "yahoo"
    default_timeframe: Timeframe = Timeframe.H1
    refresh_interval: int = 300
    theme: str = "dark"
