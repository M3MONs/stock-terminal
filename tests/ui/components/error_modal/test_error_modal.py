import pytest
from textual.app import App, ComposeResult
from textual.widgets import Label

from ui.components.error_modal import ErrorModal
from ui.components.error_modal.constants import TITLE_ID


class _TestApp(App):
    def compose(self) -> ComposeResult:
        return iter([])


@pytest.mark.asyncio
async def test_ok_dismisses():
    app = _TestApp()
    async with app.run_test() as pilot:
        result: list[None] = []
        await pilot.app.push_screen(
            ErrorModal("boom"),
            lambda x: result.append(x),
        )
        await pilot.click("#error-ok")
        assert result == [None]


@pytest.mark.asyncio
async def test_message_visible():
    app = _TestApp()
    async with app.run_test() as pilot:
        await pilot.app.push_screen(ErrorModal("boom", title="Failure"))
        title = pilot.app.screen.query_one(f"#{TITLE_ID}", Label)
        assert title.content == "Failure"
        labels = [label.content for label in pilot.app.screen.query(Label)]
        assert "boom" in labels
