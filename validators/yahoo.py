import logging

import yfinance as yf

from validators.default import DefaultSymbolValidator

_log = logging.getLogger(__name__)


class YahooSymbolValidator(DefaultSymbolValidator):
    def validate(self, symbol: str) -> str | None:
        symbol = symbol.strip().upper()
        err = super().validate(symbol)
        if err:
            return err
        return None if self._symbol_exists(symbol) else f"Symbol not found on Yahoo Finance: {symbol}"

    def _symbol_exists(self, symbol: str) -> bool:
        try:
            ticker = yf.Ticker(symbol)

            if ticker.fast_info.last_price is not None:
                return True

            info = ticker.info
            return any(
                info.get(field)
                for field in ("symbol", "longName", "shortName")
            )

        except Exception as e:
            _log.warning("yfinance lookup failed for %s: %s", symbol, e)
            return False
