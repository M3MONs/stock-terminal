from decimal import Decimal

from rich.text import Text

from models.user_agent_recommendation import Outcome, TradingOption

from .constants import ICON_FAILURE, ICON_NEUTRAL, ICON_SUCCESS


def format_option(option: TradingOption | str) -> Text:
    upper = str(option).upper()
    if upper == TradingOption.BUY:
        return Text(upper, style="bold green")
    if upper == TradingOption.SELL:
        return Text(upper, style="bold red")
    return Text(upper, style="yellow")


def format_price(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def format_outcome(outcome: Outcome | None) -> Text:
    if outcome is None:
        return Text("-", style="dim")
    if outcome == Outcome.SUCCESS:
        return Text(ICON_SUCCESS, style="bold green")
    if outcome == Outcome.FAILURE:
        return Text(ICON_FAILURE, style="bold red")
    return Text(ICON_NEUTRAL, style="yellow")
