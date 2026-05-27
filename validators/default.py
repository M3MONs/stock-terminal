import re

from validators.base import SymbolValidator

_DEFAULT_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


class DefaultSymbolValidator(SymbolValidator):
    def validate(self, symbol: str) -> str | None:
        if not symbol:
            return "Symbol cannot be empty"
        if not _DEFAULT_SYMBOL_RE.match(symbol):
            return "Symbol must be 1-15 chars: letters, digits, dot, or hyphen"
        return None
