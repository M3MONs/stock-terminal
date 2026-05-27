import pytest

from ui.dashboard import Dashboard
from ui.screens.symbol_manager import SymbolManagerScreen


@pytest.mark.asyncio
async def test_escape_closes_symbol_manager_and_allows_reopen() -> None:
    app = Dashboard()

    async with app.run_test() as pilot:
        await pilot.app.run_action("push_symbols")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SymbolManagerScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(pilot.app.screen, SymbolManagerScreen)

        await pilot.app.run_action("push_symbols")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SymbolManagerScreen)
