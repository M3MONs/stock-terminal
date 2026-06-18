from config.paths import KNOWLEDGE_DIR
from models.tagged_symbol import TaggedSymbol
from validators.base import SymbolValidator
from validators.default import DefaultSymbolValidator
from repositories.symbol_repository import SymbolRepository


class SymbolService:
    def __init__(self, repository: SymbolRepository, validator: SymbolValidator | None = None) -> None:
        self._repository = repository
        self._validator = validator or DefaultSymbolValidator()

    def get_all(self) -> list[TaggedSymbol]:
        return self._repository.get_all()

    def add(self, symbol: str) -> None:
        error = self._validator.validate(symbol)
        if error:
            raise ValueError(error)
        self._repository.add(symbol)
        (KNOWLEDGE_DIR / symbol.upper()).mkdir(parents=True, exist_ok=True)

    def remove(self, symbol: str) -> None:
        self._repository.remove(symbol)

    def update_tags(self, symbol: str, tags: list[str]) -> None:
        self._repository.update_tags(symbol, tags)
