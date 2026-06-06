import re

import yfinance as yf

from validators.base import SymbolValidator

_YAHOO_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


class YahooSymbolValidator(SymbolValidator):
    def validate(self, symbol: str) -> str | None:
        symbol = symbol.strip().upper()
        if not symbol:
            return "Symbol cannot be empty"
        
        if not _YAHOO_SYMBOL_RE.match(symbol):
            return "Symbol must be 1-15 chars: letters, digits, dot, or hyphen"
        
        if self._symbol_exists(symbol):
            return None

        return f"Symbol not found on Yahoo Finance: {symbol}"
    
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
