from validators.base import SymbolValidator
from validators.default import DefaultSymbolValidator
from validators.yahoo import YahooSymbolValidator

_REGISTRY: dict[str, type[SymbolValidator]] = {
    "yahoo": YahooSymbolValidator,
}


def get_validator(provider: str) -> SymbolValidator:
    return _REGISTRY.get(provider, DefaultSymbolValidator)()


__all__ = ["SymbolValidator", "DefaultSymbolValidator", "YahooSymbolValidator", "get_validator"]
