import pytest
from unittest.mock import MagicMock, patch

from models.app_config import AppConfig
from models.user_agent import UserAgent
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


class TestAgentServiceSetEnabled:
    def _make_agent(self, agent_id: int, name: str, enabled: bool) -> UserAgent:
        return UserAgent(id=agent_id, name=name, file_path=f"/tmp/{name}.md", enabled=enabled)

    def _make_service(self, agents: list[UserAgent]):
        repo = MagicMock()
        repo.get_all.return_value = agents
        cfg = MagicMock()
        cfg.load.return_value = AppConfig()
        return AgentService(repo, cfg), repo, cfg

    def test_enable_disables_all_others_first(self):
        agent = self._make_agent(1, "alpha", False)
        service, repo, _ = self._make_service([agent])
        service.set_enabled(1, True)
        repo.disable_all.assert_called_once()
        repo.set_enabled.assert_called_once_with(1, True)

    def test_enable_saves_agent_name_to_config(self):
        agent = self._make_agent(1, "alpha", True)
        service, repo, cfg = self._make_service([agent])
        service.set_enabled(1, True)
        saved = cfg.save.call_args[0][0]
        assert saved.signal_agent == "alpha"

    def test_disable_saves_empty_signal_agent(self):
        agent = self._make_agent(1, "alpha", True)
        service, repo, cfg = self._make_service([agent])
        service.set_enabled(1, False)
        repo.disable_all.assert_not_called()
        saved = cfg.save.call_args[0][0]
        assert saved.signal_agent == ""

    def test_no_config_injected_does_not_crash(self):
        repo = MagicMock()
        repo.get_all.return_value = [self._make_agent(1, "alpha", True)]
        service = AgentService(repo)
        service.set_enabled(1, True)  # must not raise


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
