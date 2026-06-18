from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel

from connectors.registry import get_connector, get_connector_key_field
from data import create_service
from knowledge import load_knowledge
from .prompt_template import PROMPT_TEMPLATE as _PROMPT_TEMPLATE
from models.app_config import AppConfig
from models.user_agent_recommendation import TradingOption, UserAgentRecommendation
from repositories.user_agent_recommendation_repository import UserAgentRecommendationRepository
from repositories.user_agent_repository import UserAgentRepository
from security.keystore import get_secret

_log = logging.getLogger(__name__)


class _SignalResponse(BaseModel):
    option: TradingOption
    stop_loss: Decimal | None = None
    stop_profit: Decimal | None = None
    target_date: date | None = None



def _format_candles(series) -> str:
    lines = ["date,open,high,low,close,volume"]
    for c in series.candles[-50:]:
        lines.append(f"{c.timestamp},{c.open:.4f},{c.high:.4f},{c.low:.4f},{c.close:.4f},{c.volume}")
    return "\n".join(lines)


class SignalService:
    def __init__(
        self,
        recommendation_repo: UserAgentRecommendationRepository,
        user_agent_repo: UserAgentRepository,
    ) -> None:
        self._recommendation_repo = recommendation_repo
        self._user_agent_repo = user_agent_repo

    def generate(self, symbol: str, cfg: AppConfig) -> UserAgentRecommendation:
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

        active_agent = next((a for a in self._user_agent_repo.get_all() if a.enabled), None)
        agent_name = active_agent.name if active_agent else ""
        agent_context = ""
        if active_agent:
            try:
                agent_context = Path(active_agent.file_path).read_text(encoding="utf-8")
            except OSError:
                _log.warning("agent file missing or unreadable: %s", active_agent.file_path)

        knowledge = load_knowledge(symbol)
        if knowledge:
            _log.debug("signal: injecting knowledge for %s (%d chars)", symbol, len(knowledge))
            base_prompt = f"## Company Knowledge Base\n{knowledge}\n\n---\n{base_prompt}"

        prompt = f"{agent_context}\n\n---\n{base_prompt}" if agent_context else base_prompt

        key_field = get_connector_key_field(cfg.connector)
        api_key = get_secret(key_field) if key_field else ""
        _log.debug("signal: connector=%s key_field=%s has_key=%s agent=%s", cfg.connector, key_field, bool(api_key), agent_name)
        connector = get_connector(cfg.connector, api_key=api_key)

        try:
            response = connector.generate_structured(prompt, _SignalResponse)
        except Exception as e:
            _log.error("signal: %s failed via %s — %s", symbol, cfg.connector, e, exc_info=True)
            raise

        _log.info("signal: %s → %s sl=%s tp=%s agent=%s", symbol, response.option, response.stop_loss, response.stop_profit, agent_name)
        return self._recommendation_repo.add(
            agent=agent_name,
            symbol=symbol,
            option=response.option,
            stop_loss=response.stop_loss,
            stop_profit=response.stop_profit,
            target_date=response.target_date,
        )


def generate(symbol: str, cfg: AppConfig) -> UserAgentRecommendation:
    from repositories import recommendation_repo, user_agent_repo
    return SignalService(recommendation_repo, user_agent_repo).generate(symbol, cfg)
