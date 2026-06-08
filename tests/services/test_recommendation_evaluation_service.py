from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest  # noqa: F401

from models.candle import Candle
from models.ohlcv_series import OHLCVSeries
from models.timeframe import Timeframe
from models.user_agent_recommendation import Outcome, TradingOption, UserAgentRecommendation
from services.recommendation_evaluation_service import RecommendationEvaluationService

_compute_outcome = RecommendationEvaluationService._compute_outcome


def _candle(low: str, high: str, ts: date = date(2024, 6, 2)) -> Candle:
    d = Decimal
    return Candle(
        timestamp=datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc),
        open=d("100"),
        high=d(high),
        low=d(low),
        close=d("100"),
        volume=1000,
    )


def _rec(
    option: TradingOption = TradingOption.BUY,
    stop_loss: Decimal | None = None,
    stop_profit: Decimal | None = None,
    created: date = date(2024, 6, 1),
    target: date = date(2024, 6, 3),
) -> UserAgentRecommendation:
    return UserAgentRecommendation(
        id=1,
        created_at=datetime(created.year, created.month, created.day, tzinfo=timezone.utc),
        agent="test",
        symbol="AAPL",
        option=option,
        stop_loss=Decimal(stop_loss) if stop_loss else None,
        stop_profit=Decimal(stop_profit) if stop_profit else None,
        target_date=target,
    )


# --- _compute_outcome unit tests ---

def test_hold_always_neutral():
    candles = [_candle("90", "110")]
    assert _compute_outcome(TradingOption.HOLD, candles, None, None) == Outcome.NEUTRAL


def test_no_candles_returns_neutral():
    assert _compute_outcome(TradingOption.BUY, [], None, None) == Outcome.NEUTRAL


def test_buy_stop_loss_hit_returns_failure():
    candles = [_candle("95", "105")]
    assert _compute_outcome(TradingOption.BUY, candles, Decimal("96"), None) == Outcome.FAILURE


def test_buy_stop_profit_hit_returns_success():
    candles = [_candle("95", "115")]
    assert _compute_outcome(TradingOption.BUY, candles, None, Decimal("110")) == Outcome.SUCCESS


def test_buy_neither_hit_returns_neutral():
    candles = [_candle("98", "102")]
    assert _compute_outcome(TradingOption.BUY, candles, Decimal("90"), Decimal("120")) == Outcome.NEUTRAL


def test_buy_stop_loss_checked_before_profit_on_same_candle():
    # stop_loss and stop_profit both triggered on same candle — stop_loss wins (checked first)
    candles = [_candle("80", "130")]
    result = _compute_outcome(TradingOption.BUY, candles, Decimal("85"), Decimal("125"))
    assert result == Outcome.FAILURE


def test_sell_stop_loss_hit_returns_failure():
    candles = [_candle("95", "115")]
    assert _compute_outcome(TradingOption.SELL, candles, Decimal("110"), None) == Outcome.FAILURE


def test_sell_stop_profit_hit_returns_success():
    candles = [_candle("85", "105")]
    assert _compute_outcome(TradingOption.SELL, candles, None, Decimal("90")) == Outcome.SUCCESS


def test_sell_neither_hit_returns_neutral():
    candles = [_candle("98", "102")]
    assert _compute_outcome(TradingOption.SELL, candles, Decimal("120"), Decimal("80")) == Outcome.NEUTRAL


# --- RecommendationEvaluationService integration ---

def _make_service(candles: list[Candle]):
    repo = MagicMock()
    data_service = MagicMock()
    series = OHLCVSeries(symbol="AAPL", timeframe=Timeframe.D1, candles=candles)
    data_service.get_ohlcv.return_value = series
    return RecommendationEvaluationService(repo, data_service), repo


def test_evaluate_skips_not_ready():
    rec = _rec(target=date(2099, 1, 1))
    service, repo = _make_service([])
    result = service.evaluate_and_save(rec)
    assert result is None
    repo.set_outcome.assert_not_called()


def test_evaluate_returns_none_when_no_candles_in_range():
    candles = [_candle("95", "105", ts=date(2024, 5, 1))]
    service, _ = _make_service(candles)
    rec = _rec(created=date(2024, 6, 1), target=date(2024, 6, 3))
    assert service.evaluate_and_save(rec) is None


def test_evaluate_and_save_sets_outcome():
    candles = [_candle("80", "100", ts=date(2024, 6, 2))]
    service, repo = _make_service(candles)
    rec = _rec(option=TradingOption.BUY, stop_loss=Decimal("85"), created=date(2024, 6, 1), target=date(2024, 6, 3))
    outcome = service.evaluate_and_save(rec)
    assert outcome == Outcome.FAILURE
    repo.set_outcome.assert_called_once_with(1, Outcome.FAILURE)


def test_evaluate_all_pending_returns_resolved():
    candles = [_candle("80", "130", ts=date(2024, 6, 2))]
    service, repo = _make_service(candles)
    rec = _rec(option=TradingOption.BUY, stop_profit=Decimal("125"), created=date(2024, 6, 1), target=date(2024, 6, 3))
    repo.list_pending.return_value = [rec]
    results = service.evaluate_all_pending()
    assert len(results) == 1
    assert results[0][1] == Outcome.SUCCESS
