from decimal import Decimal

from models.user_agent_recommendation import Outcome, TradingOption
from ui.screens.recommendation_history.constants import ICON_FAILURE, ICON_NEUTRAL, ICON_SUCCESS
from ui.screens.recommendation_history.formatters import format_option, format_outcome, format_price


def _style(text) -> str:
    return str(text.style)


def test_format_option_buy_sell_hold() -> None:
    assert format_option(TradingOption.BUY).plain == "BUY"
    assert _style(format_option(TradingOption.BUY)) == "bold green"
    assert format_option(TradingOption.SELL).plain == "SELL"
    assert _style(format_option(TradingOption.SELL)) == "bold red"
    assert format_option(TradingOption.HOLD).plain == "HOLD"
    assert _style(format_option(TradingOption.HOLD)) == "yellow"


def test_format_price() -> None:
    assert format_price(None) == "-"
    assert format_price(Decimal("10.5")) == "10.50"
    assert format_price(Decimal("100")) == "100.00"


def test_format_outcome_icons() -> None:
    success = format_outcome(Outcome.SUCCESS)
    assert success.plain == ICON_SUCCESS
    assert _style(success) == "bold green"

    failure = format_outcome(Outcome.FAILURE)
    assert failure.plain == ICON_FAILURE
    assert _style(failure) == "bold red"

    neutral = format_outcome(Outcome.NEUTRAL)
    assert neutral.plain == ICON_NEUTRAL
    assert _style(neutral) == "yellow"

    missing = format_outcome(None)
    assert missing.plain == "-"
    assert _style(missing) == "dim"
