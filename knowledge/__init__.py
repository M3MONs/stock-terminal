from __future__ import annotations

import logging
from pathlib import Path

from config.paths import KNOWLEDGE_DIR

_log = logging.getLogger(__name__)

_SUPPORTED = {".txt", ".md", ".pdf"}
_DEFAULT_MAX_CHARS = 10000


def load_knowledge(symbol: str, max_chars: int = _DEFAULT_MAX_CHARS) -> str | None:
    folder = KNOWLEDGE_DIR / symbol.upper()
    if not folder.is_dir():
        return None

    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in _SUPPORTED)

    if not files:
        _log.info("knowledge: no supported files found for %s", symbol)
        return None

    parts = _load_parts(files)

    if not parts:
        _log.info("knowledge: no readable content found for %s", symbol)
        return None

    combined = "\n\n".join(parts)

    if len(combined) > max_chars:
        _log.warning("knowledge: %s truncated from %d to %d chars", symbol, len(combined), max_chars)
        combined = combined[:max_chars]

    return combined


def _read_file(path: Path) -> str | None:
    try:
        if path.suffix.lower() == ".pdf":
            return _read_pdf(path)
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        _log.warning("knowledge: cannot read %s — %s", path, e)
        return None


def _load_parts(files: list[Path]) -> list[str]:
    parts: list[str] = []
    for path in files:
        text = _read_file(path)
        if text:
            parts.append(f"### {path.name}\n{text}")
    return parts


def _read_pdf(path: Path) -> str | None:
    try:
        import pypdf
    except ImportError:
        _log.warning("knowledge: pypdf not installed, skipping %s", path.name)
        return None
    try:
        reader = pypdf.PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip() or None
    except Exception as e:
        _log.warning("knowledge: failed to parse PDF %s — %s", path.name, e)
        return None
