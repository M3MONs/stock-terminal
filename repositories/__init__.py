from db import get_connection
from .symbol_repository import SymbolRepository
from .user_agent_repository import UserAgentRepository


symbol_repo = SymbolRepository(connection_factory=get_connection)
user_agent_repo = UserAgentRepository(connection_factory=get_connection)
