from unittest.mock import MagicMock, patch

import pytest

from models.tagged_symbol import TaggedSymbol
from services.symbol_service import SymbolService


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo) -> SymbolService:
    return SymbolService(repository=repo)


def test_get_all_delegates_to_repo(service, repo):
    repo.get_all.return_value = [TaggedSymbol(symbol="AAPL", tags=[])]
    result = service.get_all()
    repo.get_all.assert_called_once()
    assert result[0].symbol == "AAPL"


def test_add_valid_symbol_calls_repo(service, repo):
    service.add("AAPL")
    repo.add.assert_called_once_with("AAPL")


def test_add_invalid_symbol_raises_and_not_calls_repo(service, repo):
    with pytest.raises(ValueError):
        service.add("aapl")
    repo.add.assert_not_called()


def test_add_empty_symbol_raises(service, repo):
    with pytest.raises(ValueError):
        service.add("")
    repo.add.assert_not_called()


def test_remove_delegates_to_repo(service, repo):
    service.remove("AAPL")
    repo.remove.assert_called_once_with("AAPL")


def test_update_tags_delegates_to_repo(service, repo):
    service.update_tags("AAPL", ["tech", "large-cap"])
    repo.update_tags.assert_called_once_with("AAPL", ["tech", "large-cap"])


def test_add_creates_knowledge_folder(repo, tmp_path):
    with patch("services.knowledge.KNOWLEDGE_DIR", tmp_path):
        service = SymbolService(repository=repo)
        service.add("AAPL")
    assert (tmp_path / "AAPL").is_dir()
