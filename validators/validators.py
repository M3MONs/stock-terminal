from abc import ABC, abstractmethod


class SymbolValidator(ABC):
    @abstractmethod
    def validate(self, symbol: str) -> str | None:
        """Return error message if invalid, None if valid."""
        ...


class DefaultSymbolValidator(SymbolValidator):
    def validate(self, symbol: str) -> str | None:
        if not symbol:
            return "Symbol cannot be empty"
        if not symbol.isalpha():
            return "Symbol must contain only letters"
        if len(symbol) > 10:
            return "Symbol too long (max 10 chars)"
        return None
