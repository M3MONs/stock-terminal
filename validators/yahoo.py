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
        try:
            price = yf.Ticker(symbol).fast_info.last_price
        except Exception:
            return f"Symbol not found on Yahoo Finance: {symbol}"
        if price is None:
            return f"Symbol not found on Yahoo Finance: {symbol}"
        return None
