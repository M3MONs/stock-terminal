import pytest
from textual.app import App, ComposeResult

from ui.components.confirm_modal import ConfirmModal


class _TestApp(App):
    def compose(self) -> ComposeResult:
        return iter([])


@pytest.mark.asyncio
async def test_confirm_returns_true():
    app = _TestApp()
    async with app.run_test() as pilot:
        result: list[bool] = []
        await pilot.app.push_screen(ConfirmModal("Delete?"), lambda x: result.append(x) if x is not None else None)
        await pilot.click("#confirm")
        assert result == [True]


@pytest.mark.asyncio
async def test_cancel_returns_false():
    app = _TestApp()
    async with app.run_test() as pilot:
        result: list[bool] = []
        await pilot.app.push_screen(ConfirmModal("Delete?"), lambda x: result.append(x) if x is not None else None)
        await pilot.click("#cancel")
        assert result == [False]
