from pydantic import BaseModel

from models.timeframe import Timeframe


class AppConfig(BaseModel):
    provider: str = "yahoo"
    default_timeframe: Timeframe = Timeframe.H1
    refresh_interval: int = 300
    theme: str = "dark"
    connector: str = "gemini"
    signal_interval: int = 60
    signal_timeframe_fast: Timeframe = Timeframe.M15
    signal_timeframe_slow: Timeframe = Timeframe.H4
    signal_agent: str = ""
