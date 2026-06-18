from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

import knowledge as k


@pytest.fixture()
def knowledge_dir(tmp_path):
    with patch.object(k, "KNOWLEDGE_DIR", tmp_path):
        yield tmp_path


class TestLoadKnowledge:
    def test_missing_symbol_folder_returns_none(self, knowledge_dir):
        assert k.load_knowledge("AAPL") is None

    def test_empty_folder_returns_none(self, knowledge_dir):
        (knowledge_dir / "AAPL").mkdir()
        assert k.load_knowledge("AAPL") is None

    def test_unsupported_extension_ignored(self, knowledge_dir):
        folder = knowledge_dir / "AAPL"
        folder.mkdir()
        (folder / "notes.docx").write_text("ignored")
        assert k.load_knowledge("AAPL") is None

    def test_txt_file_returned(self, knowledge_dir):
        folder = knowledge_dir / "AAPL"
        folder.mkdir()
        (folder / "report.txt").write_text("Apple Q1 revenue up 10%")
        result = k.load_knowledge("AAPL")
        assert result is not None
        assert "Apple Q1 revenue up 10%" in result
        assert "### report.txt" in result

    def test_md_file_returned(self, knowledge_dir):
        folder = knowledge_dir / "MSFT"
        folder.mkdir()
        (folder / "analysis.md").write_text("# MSFT\nStrong cloud growth")
        result = k.load_knowledge("MSFT")
        assert result is not None
        assert "Strong cloud growth" in result

    def test_symbol_uppercased(self, knowledge_dir):
        folder = knowledge_dir / "TSLA"
        folder.mkdir()
        (folder / "notes.txt").write_text("Tesla delivery beat")
        result = k.load_knowledge("tsla")
        assert result is not None
        assert "Tesla delivery beat" in result

    def test_multiple_files_combined(self, knowledge_dir):
        folder = knowledge_dir / "NVDA"
        folder.mkdir()
        (folder / "a.txt").write_text("Data center growth")
        (folder / "b.txt").write_text("AI chip demand")
        result = k.load_knowledge("NVDA")
        assert result is not None
        assert "Data center growth" in result
        assert "AI chip demand" in result

    def test_truncation_at_max_chars(self, knowledge_dir, caplog):
        folder = knowledge_dir / "AAPL"
        folder.mkdir()
        (folder / "big.txt").write_text("x" * 100)
        with caplog.at_level(logging.WARNING, logger="knowledge"):
            result = k.load_knowledge("AAPL", max_chars=50)
        assert result is not None
        assert len(result) == 50
        assert "truncated" in caplog.text

    def test_unreadable_file_skipped(self, knowledge_dir):
        folder = knowledge_dir / "AAPL"
        folder.mkdir()
        (folder / "good.txt").write_text("valid content")
        bad = folder / "bad.txt"
        bad.write_bytes(b"\xff\xfe")  # invalid utf-8
        result = k.load_knowledge("AAPL")
        assert result is not None
        assert "valid content" in result

    def test_pdf_without_pypdf_logs_warning(self, knowledge_dir, caplog):
        folder = knowledge_dir / "AAPL"
        folder.mkdir()
        (folder / "report.pdf").write_bytes(b"%PDF-fake")
        import builtins
        real_import = builtins.__import__

        def block_pypdf(name, *args, **kwargs):
            if name == "pypdf":
                raise ImportError("no pypdf")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=block_pypdf):
            with caplog.at_level(logging.WARNING, logger="knowledge"):
                result = k.load_knowledge("AAPL")
        assert result is None
        assert "pypdf not installed" in caplog.text
