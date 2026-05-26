from validators.base import SymbolValidator


class DefaultSymbolValidator(SymbolValidator):
    def validate(self, symbol: str) -> str | None:
        if not symbol:
            return "Symbol cannot be empty"
        if not symbol.isalpha():
            return "Symbol must contain only letters"
        if len(symbol) > 10:
            return "Symbol too long (max 10 chars)"
        return None
