import yfinance as yf

from validators.default import DefaultSymbolValidator


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

        except Exception:
            return False
