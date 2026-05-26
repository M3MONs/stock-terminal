from abc import ABC, abstractmethod


class SymbolValidator(ABC):
    @abstractmethod
    def validate(self, symbol: str) -> str | None:
        """Return error message if invalid, None if valid."""
        ...
