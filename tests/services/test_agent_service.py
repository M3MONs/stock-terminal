import pytest
from unittest.mock import MagicMock, patch

from services.agent_service import AgentService, _validate_agent_name


class TestValidateAgentName:
    def test_valid_names(self):
        for name in ("my-agent", "Agent1", "foo_bar", "a"):
            _validate_agent_name(name)  # must not raise

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_agent_name("")

    def test_forward_slash_raises(self):
        with pytest.raises(ValueError, match="path separators"):
            _validate_agent_name("../../evil")

    def test_backslash_raises(self):
        with pytest.raises(ValueError, match="path separators"):
            _validate_agent_name("..\\evil")

    def test_dotdot_raises(self):
        with pytest.raises(ValueError, match="path separators"):
            _validate_agent_name("..evil")

    def test_path_component_raises(self):
        with pytest.raises(ValueError):
            _validate_agent_name("subdir/agent")


class TestAgentServiceAdd:
    def _make_service(self):
        repo = MagicMock()
        repo.add.return_value = MagicMock(id=1, name="test", file_path="/tmp/test.md", enabled=True)
        return AgentService(repo), repo

    def test_traversal_name_rejected(self):
        service, repo = self._make_service()
        with pytest.raises(ValueError, match="path separators"):
            service.add("../../etc/passwd")
        repo.add.assert_not_called()

    def test_valid_name_accepted(self, tmp_path):
        service, repo = self._make_service()
        with patch("services.agent_service.AGENTS_DIR", tmp_path):
            service.add("valid-agent")
        repo.add.assert_called_once()


class TestAgentServiceUpdateContent:
    def test_write_inside_agents_dir(self, tmp_path):
        service = AgentService(MagicMock())
        target = tmp_path / "agent.md"
        with patch("services.agent_service.AGENTS_DIR", tmp_path):
            service.update_content(str(target), "hello")
        assert target.read_text() == "hello"

    def test_write_outside_agents_dir_rejected(self, tmp_path):
        service = AgentService(MagicMock())
        outside = tmp_path.parent / "evil.md"
        with patch("services.agent_service.AGENTS_DIR", tmp_path):
            with pytest.raises(ValueError, match="outside agents directory"):
                service.update_content(str(outside), "evil")
