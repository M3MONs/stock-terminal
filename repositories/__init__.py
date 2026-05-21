from db import get_connection
from .symbol_repository import SymbolRepository


symbol_repo = SymbolRepository(connection_factory=get_connection)
