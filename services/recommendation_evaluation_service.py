from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Callable

from data import StockDataService
from models.candle import Candle
from models.timeframe import Timeframe
from models.user_agent_recommendation import Outcome, TradingOption, UserAgentRecommendation
from repositories.user_agent_recommendation_repository import UserAgentRecommendationRepository

_log = logging.getLogger(__name__)

class RecommendationNotReadyError(Exception):
    """Raised when trying to evaluate a recommendation that is not ready yet."""
    pass

class MissingCandleDataError(Exception):
    """Raised when there is missing candle data for evaluation."""
    pass

class RecommendationEvaluationService:
    def __init__(
        self,
        repo: UserAgentRecommendationRepository,
        data_service: StockDataService,
    ) -> None:
        self._repo = repo
        self._data_service = data_service

    @staticmethod
    def _is_ready(rec: UserAgentRecommendation) -> bool:
        return rec.target_date is not None and rec.target_date <= date.today()

    @staticmethod
    def _compute_buy_outcome(candles: list[Candle], stop_loss: Decimal | None, stop_profit: Decimal | None) -> Outcome:
        for candle in candles:
            if stop_loss is not None and candle.low <= stop_loss:
                return Outcome.FAILURE
            if stop_profit is not None and candle.high >= stop_profit:
                return Outcome.SUCCESS
        return Outcome.NEUTRAL

    @staticmethod
    def _compute_sell_outcome(candles: list[Candle], stop_loss: Decimal | None, stop_profit: Decimal | None) -> Outcome:
        for candle in candles:
            if stop_loss is not None and candle.high >= stop_loss:
                return Outcome.FAILURE
            if stop_profit is not None and candle.low <= stop_profit:
                return Outcome.SUCCESS
        return Outcome.NEUTRAL

    @staticmethod
    def _compute_outcome(option: TradingOption, candles: list[Candle], stop_loss: Decimal | None, stop_profit: Decimal | None) -> Outcome:
        if option == TradingOption.HOLD or not candles:
            return Outcome.NEUTRAL

        if option == TradingOption.BUY:
            return RecommendationEvaluationService._compute_buy_outcome(candles, stop_loss, stop_profit)
        elif option == TradingOption.SELL:
            return RecommendationEvaluationService._compute_sell_outcome(candles, stop_loss, stop_profit)
        return Outcome.NEUTRAL

    def evaluate(self, rec: UserAgentRecommendation) -> Outcome | None:
        if not self._is_ready(rec):
            raise RecommendationNotReadyError("Recommendation is not ready for evaluation")

        assert rec.target_date is not None
        num_days = (rec.target_date - rec.created_at.date()).days + 10
        series = self._data_service.get_ohlcv(rec.symbol, Timeframe.D1, limit=num_days)
        candles = [
            c for c in series.candles
            if rec.created_at.date() <= c.timestamp.date() <= rec.target_date
        ]

        if not candles:
            raise MissingCandleDataError("No candle data available for evaluation")

        outcome = self._compute_outcome(rec.option, candles, rec.stop_loss, rec.stop_profit)
        _log.info("evaluation: rec=%s %s %s candles=%d → %s", rec.id, rec.symbol, rec.option, len(candles), outcome)
        return outcome

    def evaluate_and_save(self, rec: UserAgentRecommendation) -> Outcome | None:
        try:
            outcome = self.evaluate(rec)
            if outcome is None:
                return None
            assert rec.id is not None
            self._repo.set_outcome(rec.id, outcome)
            return outcome
        except (RecommendationNotReadyError, MissingCandleDataError) as e:
            _log.warning("Skipping evaluation: %s", e)
            return None

    def evaluate_all_pending(
        self,
        should_cancel: Callable[[], bool] = lambda: False,
    ) -> list[tuple[UserAgentRecommendation, Outcome]]:
        results: list[tuple[UserAgentRecommendation, Outcome]] = []
        for rec in self._repo.list_pending():
            if should_cancel():
                _log.info("evaluation cancelled after %d processed", len(results))
                break
            outcome = self.evaluate_and_save(rec)
            if outcome is not None:
                results.append((rec, outcome))
        return results


def evaluate_all_pending(
    should_cancel: Callable[[], bool] = lambda: False,
) -> list[tuple[UserAgentRecommendation, Outcome]]:
    from config import config as app_config
    from data import create_service
    from repositories import recommendation_repo
    cfg = app_config.load()
    data_service = create_service(cfg.provider or "mock")
    return RecommendationEvaluationService(recommendation_repo, data_service).evaluate_all_pending(
        should_cancel=should_cancel
    )