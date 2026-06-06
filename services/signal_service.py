from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from connectors.registry import get_connector, get_connector_key_field
from data import create_service
from models.app_config import AppConfig
from models.user_agent_recommendation import UserAgentRecommendation
from repositories import recommendation_repo, user_agent_repo
from security.keystore import get_secret

_log = logging.getLogger(__name__)


class _SignalResponse(BaseModel):
    option: str
    stop_loss: float | None = None
    stop_profit: float | None = None
    target_date: date | None = None


_PROMPT_TEMPLATE = """\
You are a professional trading signal analyst.

Analyze the following candlestick data for {symbol} and provide a trading signal.

## {fast_tf} candles (recent, for signal timing):
{fast_candles}

## {slow_tf} candles (context, for trend direction):
{slow_candles}

Based on this multi-timeframe analysis, provide a trading signal for the {fast_tf} timeframe.

Respond with:
- option: one of "BUY", "SELL", or "HOLD"
- stop_loss: price level for stop loss (optional)
- stop_profit: price level for take profit (optional)
- target_date: estimated date to close the position in YYYY-MM-DD format — always provide a specific date
"""


def _load_agent_context(agent_name: str) -> str:
    if not agent_name:
        return ""
    agents = user_agent_repo.get_all()
    agent = next((a for a in agents if a.name == agent_name), None)
    if agent is None:
        return ""
    try:
        return Path(agent.file_path).read_text()
    except OSError:
        return ""


def _format_candles(series) -> str:
    lines = ["date,open,high,low,close,volume"]
    for c in series.candles[-50:]:
        lines.append(f"{c.timestamp},{c.open:.4f},{c.high:.4f},{c.low:.4f},{c.close:.4f},{c.volume}")
    return "\n".join(lines)


def generate(symbol: str, cfg: AppConfig) -> UserAgentRecommendation:
    _log.info("signal: generating %s via %s (fast=%s slow=%s)", symbol, cfg.connector, cfg.signal_timeframe_fast.value, cfg.signal_timeframe_slow.value)
    service = create_service(cfg.provider)
    fast_ohlcv = service.get_ohlcv(symbol, cfg.signal_timeframe_fast, limit=100)
    slow_ohlcv = service.get_ohlcv(symbol, cfg.signal_timeframe_slow, limit=50)

    base_prompt = _PROMPT_TEMPLATE.format(
        symbol=symbol,
        fast_tf=cfg.signal_timeframe_fast.value,
        slow_tf=cfg.signal_timeframe_slow.value,
        fast_candles=_format_candles(fast_ohlcv),
        slow_candles=_format_candles(slow_ohlcv),
    )
    agent_context = _load_agent_context(cfg.signal_agent)
    prompt = f"{agent_context}\n\n---\n{base_prompt}" if agent_context else base_prompt

    key_field = get_connector_key_field(cfg.connector)
    api_key = get_secret(key_field) if key_field else ""
    _log.debug("signal: connector=%s key_field=%s has_key=%s", cfg.connector, key_field, bool(api_key))
    connector = get_connector(cfg.connector, api_key=api_key)

    try:
        response = connector.generate_structured(prompt, _SignalResponse)
    except Exception as e:
        _log.error("signal: %s failed via %s — %s", symbol, cfg.connector, e, exc_info=True)
        raise

    _log.info("signal: %s → %s sl=%s tp=%s", symbol, response.option, response.stop_loss, response.stop_profit)
    return recommendation_repo.add(
        agent=cfg.connector,
        symbol=symbol,
        option=response.option,
        stop_loss=response.stop_loss,
        stop_profit=response.stop_profit,
        target_date=response.target_date,
    )
