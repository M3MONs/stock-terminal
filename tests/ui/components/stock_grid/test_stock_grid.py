import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from textual.widgets import DataTable

from models.app_config import AppConfig
from models.stock_meta import StockMeta
from models.tagged_symbol import TaggedSymbol
from models.user_agent_recommendation import TradingOption, UserAgentRecommendation
from ui.components.stock_grid import StockGridWidget
from ui.components.stock_grid.constants import (
    KEY_AGE,
    KEY_CHANGE,
    KEY_PRICE,
    KEY_SIGNAL,
    KEY_SL,
    KEY_SYMBOL,
    KEY_TP,
    TABLE_ID,
)
from ui.dashboard import Dashboard


def _symbols(*syms: str) -> list[TaggedSymbol]:
    return [TaggedSymbol(symbol=s) for s in syms]


def _patch_grid_io(symbols: list[TaggedSymbol], *, connector: str = ""):
    meta = StockMeta(symbol="AAPL", price=Decimal("100"), change_pct=1.25, currency="USD")
    service = MagicMock()
    service.get_meta.return_value = meta
    cfg = AppConfig(provider="mock", connector=connector)
    return (
        patch("ui.dashboard._eval_pending"),
        patch("ui.components.stock_grid.widget.symbol_repo.get_all", return_value=symbols),
        patch("ui.components.stock_grid.widget.recommendation_repo.get_latest_by_symbol", return_value=None),
        patch("ui.components.stock_grid.widget.create_service", return_value=service),
        patch("ui.components.stock_grid.widget._fetch_signal", return_value=None),
        patch("ui.components.stock_grid.widget.app_config.load", return_value=cfg),
    )


def _cell(table: DataTable, row: str, col: str) -> str:
    return str(table.get_cell(row, col))


@pytest.mark.asyncio
async def test_table_columns_and_rows() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
            assert table.row_count == 2
            assert "AAPL" in table.rows
            assert "MSFT" in table.rows
            for key in (KEY_SYMBOL, KEY_PRICE, KEY_CHANGE, KEY_SIGNAL, KEY_AGE, KEY_SL, KEY_TP):
                assert key in table.columns


@pytest.mark.asyncio
async def test_arrow_navigation_moves_cursor() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
            table.focus()
            assert table.cursor_coordinate.row == 0
            await pilot.press("down")
            await pilot.pause()
            assert table.cursor_coordinate.row == 1
            await pilot.press("up")
            await pilot.pause()
            assert table.cursor_coordinate.row == 0


@pytest.mark.asyncio
async def test_meta_update_fills_price_and_change() -> None:
    patches = _patch_grid_io(_symbols("AAPL"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            table = grid.query_one(f"#{TABLE_ID}", DataTable)
            grid._apply_meta("AAPL", StockMeta(symbol="AAPL", price=Decimal("123.45"), change_pct=-2.5, currency="USD"))
            assert "123.45" in _cell(table, "AAPL", KEY_PRICE)
            assert "2.50%" in _cell(table, "AAPL", KEY_CHANGE)


@pytest.mark.asyncio
async def test_signal_update_fills_signal_cells() -> None:
    patches = _patch_grid_io(_symbols("AAPL"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            grid = pilot.app.query_one(StockGridWidget)
            table = grid.query_one(f"#{TABLE_ID}", DataTable)
            rec = UserAgentRecommendation(
                created_at=datetime.now(timezone.utc),
                agent="test",
                symbol="AAPL",
                option=TradingOption.BUY,
                stop_loss=Decimal("90"),
                stop_profit=Decimal("120"),
            )
            grid._apply_signal("AAPL", rec)
            assert "BUY" in _cell(table, "AAPL", KEY_SIGNAL)
            assert "ago" in _cell(table, "AAPL", KEY_AGE)
            assert "90.00" in _cell(table, "AAPL", KEY_SL)
            assert "120.00" in _cell(table, "AAPL", KEY_TP)


@pytest.mark.asyncio
async def test_r_refresh_without_connector_sets_error() -> None:
    patches = _patch_grid_io(_symbols("AAPL"), connector="")
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        app = Dashboard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
            table.focus()
            await pilot.press("r")
            await pilot.pause()
            assert "no connector" in _cell(table, "AAPL", KEY_SIGNAL).lower()


@pytest.mark.asyncio
async def test_selected_message_opens_chart_symbol() -> None:
    patches = _patch_grid_io(_symbols("AAPL", "MSFT"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        with patch("ui.screens.chart.screen.ChartScreen._load_data", lambda self, symbol: None):
            app = Dashboard()
            async with app.run_test() as pilot:
                await pilot.pause()
                table = pilot.app.query_one(f"#{TABLE_ID}", DataTable)
                table.focus()
                await pilot.press("down")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                from ui.screens.chart import ChartScreen

                assert isinstance(pilot.app.screen, ChartScreen)
                assert pilot.app.screen._symbol == "MSFT"
