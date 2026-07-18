import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.widgets import DataTable

from models.stock_meta import StockMeta
from models.tagged_symbol import TaggedSymbol
from ui.components.stock_grid import StockGridWidget
from ui.components.error_modal import ErrorModal
from ui.components.stock_grid.constants import EMPTY_ID, TABLE_ID
from ui.dashboard import Dashboard
from ui.dashboard.help_modal import ShortcutsHelpModal
from ui.screens.chart import ChartScreen
from ui.screens.symbol_manager import SymbolManagerScreen


def _symbols(*syms: str) -> list[TaggedSymbol]:
    return [TaggedSymbol(symbol=s) for s in syms]


def _patch_grid_io(symbols: list[TaggedSymbol]):
    meta = StockMeta(symbol="AAPL", price=Decimal("100"), change_pct=1.25, currency="USD")
    service = MagicMock()
    service.get_meta.return_value = meta
    return (
        patch("ui.dashboard.app._eval_pending"),
        patch("ui.components.stock_grid.widget.symbol_repo.get_all", return_value=symbols),
        patch("ui.components.stock_grid.widget.recommendation_repo.get_latest_by_symbol", return_value=None),
        patch("ui.components.stock_grid.widget.create_service", return_value=service),
        patch("ui.components.stock_grid.widget._fetch_signal", return_value=None),
        patch("ui.screens.chart.screen.ChartScreen._load_data", lambda self, symbol: None),
    )


@pytest.mark.asyncio
async def test_dashboard_mounts_table_and_focuses() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            table = grid.query_one(f"#{TABLE_ID}", DataTable)
            assert table.row_count == 2
            assert isinstance(pilot.app.focused, DataTable)


@pytest.mark.asyncio
async def test_enter_opens_chart_for_cursor_symbol() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
            table.focus()
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ChartScreen)
            assert pilot.app.screen._symbol == "AAPL"


@pytest.mark.asyncio
async def test_restore_grid_focus_after_reload() -> None:
    patches = _patch_grid_io(_symbols("AAPL"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            grid.load()
            pilot.app._restore_grid_focus()
            await pilot.pause()
            table = grid.query_one(f"#{TABLE_ID}", DataTable)
            assert isinstance(pilot.app.focused, DataTable)
            assert table.cursor_coordinate.row == 0


@pytest.mark.asyncio
async def test_empty_state_shows_message() -> None:
    patches = _patch_grid_io([])
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            empty = grid.query_one(f"#{EMPTY_ID}")
            assert "-hidden" not in empty.classes
            table = grid.query_one(f"#{TABLE_ID}", DataTable)
            assert "-hidden" in table.classes
            assert table.row_count == 0
            await pilot.press("enter")
            await pilot.pause()
            assert not isinstance(pilot.app.screen, ChartScreen)


@pytest.mark.asyncio
async def test_hidden_symbol_shortcut_opens_symbol_manager() -> None:
    patches = _patch_grid_io(_symbols("AAPL"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(pilot.app.screen, SymbolManagerScreen)


@pytest.mark.asyncio
async def test_help_shortcut_opens_shortcuts_modal() -> None:
    patches = _patch_grid_io(_symbols("AAPL"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("?")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ShortcutsHelpModal)
            content = pilot.app.screen.query_one("#help-content")
            assert "Configuration" in str(content.render())
            assert "Symbols" in str(content.render())


@pytest.mark.asyncio
async def test_k_opens_knowledge_folder_for_cursor_symbol() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patch("ui.dashboard.app.ensure_knowledge_dir") as ensure_dir,
        patch("ui.dashboard.app.reveal_in_file_manager") as reveal,
    ):
        ensure_dir.return_value = Path("/tmp/AAPL")
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
            table.focus()
            await pilot.press("k")
            await pilot.pause()
            ensure_dir.assert_called_once_with("AAPL")
            reveal.assert_called_once_with(Path("/tmp/AAPL"))


@pytest.mark.asyncio
async def test_k_with_empty_watchlist_shows_error() -> None:
    patches = _patch_grid_io([])
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            assert "-hidden" not in grid.query_one(f"#{EMPTY_ID}").classes
            await pilot.press("k")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ErrorModal)
