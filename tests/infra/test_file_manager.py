from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import infra.file_manager as fm


class TestRevealInFileManager:
    def test_creates_folder_before_opening(self, tmp_path: Path) -> None:
        target = tmp_path / "AAPL"
        with patch.object(fm, "os") as mock_os, patch.object(fm, "sys") as mock_sys:
            mock_sys.platform = "win32"
            mock_os.startfile = lambda path: None
            fm.reveal_in_file_manager(target)
        assert target.is_dir()

    def test_win32_uses_startfile(self, tmp_path: Path) -> None:
        target = tmp_path / "AAPL"
        target.mkdir()
        with patch.object(fm, "os") as mock_os, patch.object(fm, "sys") as mock_sys:
            mock_sys.platform = "win32"
            opened: list[Path] = []
            mock_os.startfile = lambda path: opened.append(Path(path))
            fm.reveal_in_file_manager(target)
        assert opened == [target.resolve()]

    def test_darwin_uses_open(self, tmp_path: Path) -> None:
        target = tmp_path / "AAPL"
        target.mkdir()
        with patch.object(fm, "subprocess") as mock_subprocess, patch.object(fm, "sys") as mock_sys:
            mock_sys.platform = "darwin"
            fm.reveal_in_file_manager(target)
        mock_subprocess.run.assert_called_once_with(["open", str(target.resolve())], check=False)

    def test_linux_uses_xdg_open(self, tmp_path: Path) -> None:
        target = tmp_path / "AAPL"
        target.mkdir()
        with patch.object(fm, "subprocess") as mock_subprocess, patch.object(fm, "sys") as mock_sys:
            mock_sys.platform = "linux"
            fm.reveal_in_file_manager(target)
        mock_subprocess.run.assert_called_once_with(["xdg-open", str(target.resolve())], check=False)

    def test_current_platform_branch_runs(self, tmp_path: Path) -> None:
        target = tmp_path / "AAPL"
        if sys.platform == "win32":
            with patch.object(fm.os, "startfile") as mock_startfile:
                fm.reveal_in_file_manager(target)
                mock_startfile.assert_called_once_with(target.resolve())
        else:
            with patch.object(fm.subprocess, "run") as mock_run:
                fm.reveal_in_file_manager(target)
                assert mock_run.call_count == 1
