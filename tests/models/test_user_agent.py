import pytest
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError

from models.user_agent import UserAgent
from models.user_agent_recommendation import Outcome, TradingOption, UserAgentRecommendation


def test_user_agent_defaults():
    a = UserAgent(name="MyAgent", file_path="/agents/my_agent.md")
    assert a.enabled is True
    assert a.id is None


def test_user_agent_disabled():
    a = UserAgent(name="Off", file_path="/agents/off.md", enabled=False)
    assert a.enabled is False


def test_outcome_enum_values():
    assert Outcome.SUCCESS == "success"
    assert Outcome.FAILURE == "failure"
    assert Outcome.NEUTRAL == "neutral"


def test_recommendation_optional_fields():
    r = UserAgentRecommendation(
        created_at=datetime(2024, 6, 1, 10, 0),
        agent="agent1",
        symbol="AAPL",
        option=TradingOption.BUY,
    )
    assert r.outcome is None
    assert r.stop_loss is None
    assert r.target_date is None


def test_recommendation_with_all_fields():
    r = UserAgentRecommendation(
        created_at=datetime(2024, 6, 1, 10, 0),
        agent="agent1",
        symbol="AAPL",
        option=TradingOption.BUY,
        stop_loss=Decimal("150.0"),
        stop_profit=Decimal("200.0"),
        target_date=date(2024, 12, 31),
        outcome=Outcome.SUCCESS,
    )
    assert r.outcome == Outcome.SUCCESS
    assert r.stop_loss == Decimal("150.0")


def test_invalid_outcome_raises():
    with pytest.raises(ValidationError):
        UserAgentRecommendation(
            created_at=datetime(2024, 6, 1),
            agent="a",
            symbol="X",
            option=TradingOption.BUY,
            outcome="invalid_value",  # type: ignore
        )


def test_invalid_option_raises():
    with pytest.raises(ValidationError):
        UserAgentRecommendation(
            created_at=datetime(2024, 6, 1),
            agent="a",
            symbol="X",
            option="LONG",  # type: ignore
        )


def test_trading_option_enum_values():
    assert TradingOption.BUY == "BUY"
    assert TradingOption.SELL == "SELL"
    assert TradingOption.HOLD == "HOLD"