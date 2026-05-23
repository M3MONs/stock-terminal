from rich.text import Text
from textual.app import RenderResult
from textual.widget import Widget

from models.ohlcv_series import OHLCVSeries
from models.candle import Candle
from .styles import CSS

PRICE_AXIS_WIDTH = 9
LABEL_INTERVAL_ROWS = 5
ZOOM_STEP = 10
PAN_STEP = 10
MIN_VISIBLE = 10
DATE_LABEL_LEN = 5
DATE_ROW = 1

_Grid = list[list[tuple[str, str]]]


class CandleChartWidget(Widget):
    DEFAULT_CSS = CSS

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._series: OHLCVSeries | None = None
        self._visible_count: int | None = None
        self._offset: int = 0

    def update(self, series: OHLCVSeries) -> None:
        self._series = series
        self._visible_count = None
        self._offset = 0
        self.refresh()

    def zoom_in(self) -> None:
        chart_w = max(1, self.size.width - PRICE_AXIS_WIDTH)
        current = self._visible_count or chart_w
        self._visible_count = max(MIN_VISIBLE, current - ZOOM_STEP)
        self.refresh()

    def zoom_out(self) -> None:
        if self._series is None:
            return
        chart_w = max(1, self.size.width - PRICE_AXIS_WIDTH)
        current = self._visible_count or chart_w
        self._visible_count = min(len(self._series.candles), current + ZOOM_STEP)
        self.refresh()

    def pan_left(self) -> None:
        if self._series is None:
            return
        chart_w = max(1, self.size.width - PRICE_AXIS_WIDTH)
        visible = self._visible_count or chart_w
        max_offset = max(0, len(self._series.candles) - visible)
        self._offset = min(self._offset + PAN_STEP, max_offset)
        self.refresh()

    def pan_right(self) -> None:
        self._offset = max(0, self._offset - PAN_STEP)
        self.refresh()

    def render(self) -> RenderResult:
        if self._series is None or not self._series.candles:
            return Text("No data", justify="center")
        W = self.size.width
        H = self.size.height
        if W == 0 or H <= DATE_ROW:
            return Text("")
        return self._build_chart(self._series, W, H)

    # --- private helpers ---

    def _get_visible_candles(self, series: OHLCVSeries, chart_w: int) -> list[Candle]:
        total = len(series.candles)
        visible = self._visible_count or chart_w
        end = total - self._offset
        start = max(0, end - visible)
        return series.candles[start:end]

    @staticmethod
    def _price_bounds(candles: list[Candle]) -> tuple[float, float, float]:
        lows = [float(c.low) for c in candles]
        highs = [float(c.high) for c in candles]
        price_min = min(lows)
        price_max = max(highs)
        price_range = price_max - price_min or 1e-9
        return price_min, price_max, price_range

    @staticmethod
    def _build_grid(
        candles: list[Candle],
        chart_w: int,
        chart_h: int,
        price_max: float,
        price_range: float,
    ) -> _Grid:
        def to_row(price: float) -> int:
            return int((price_max - price) / price_range * (chart_h - 1))

        grid: _Grid = [[(" ", "")] * chart_w for _ in range(chart_h)]
        n = len(candles)

        for i, candle in enumerate(candles):
            col_start = int(i * chart_w / n)
            col_end = int((i + 1) * chart_w / n)
            center = (col_start + col_end - 1) // 2

            o, h, l, c = (  # noqa: E741
                float(candle.open),
                float(candle.high),
                float(candle.low),
                float(candle.close),
            )
            color = "green" if c >= o else "red"
            wick_top = to_row(h)
            wick_bottom = to_row(l)
            body_top = min(to_row(o), to_row(c))
            body_bottom = max(to_row(o), to_row(c))

            for row in range(chart_h):
                if wick_top <= row <= wick_bottom:
                    grid[row][center] = ("│", color)
                if body_top <= row <= body_bottom:
                    for col in range(col_start, col_end):
                        grid[row][col] = ("█", color)

        return grid

    @staticmethod
    def _build_chart_text(
        grid: _Grid,
        chart_h: int,
        has_axis: bool,
        price_max: float,
        price_range: float,
    ) -> Text:
        label_interval = max(1, chart_h // LABEL_INTERVAL_ROWS)
        text = Text()
        for row_idx, row in enumerate(grid):
            for char, style in row:
                text.append(char, style=style or None)
            if has_axis:
                text.append("│", style="dim")
                price = price_max - (row_idx / max(chart_h - 1, 1)) * price_range
                if row_idx % label_interval == 0:
                    text.append(f"{price:>8.2f}")
                else:
                    text.append(" " * 8)
            text.append("\n")
        return text

    @staticmethod
    def _append_date_row(
        text: Text,
        candles: list[Candle],
        chart_w: int,
        has_axis: bool,
    ) -> None:
        all_same_day = candles[0].timestamp.date() == candles[-1].timestamp.date()
        date_fmt = "%H:%M" if all_same_day else "%m/%d"
        n = len(candles)
        chars_per_candle = chart_w / n
        label_every = max(1, int((DATE_LABEL_LEN + 2) / chars_per_candle) + 1)

        date_chars = [" "] * chart_w
        for i, candle in enumerate(candles):
            if i % label_every == 0:
                col_start = int(i * chart_w / n)
                col_end = int((i + 1) * chart_w / n)
                center = (col_start + col_end - 1) // 2
                label = candle.timestamp.strftime(date_fmt)
                lstart = center - DATE_LABEL_LEN // 2
                for j, ch in enumerate(label):
                    pos = lstart + j
                    if 0 <= pos < chart_w:
                        date_chars[pos] = ch

        for ch in date_chars:
            text.append(ch, style="dim")
        if has_axis:
            text.append("│", style="dim")
            text.append(" " * 8)

    def _build_chart(self, series: OHLCVSeries, W: int, H: int) -> Text:
        has_axis = W > PRICE_AXIS_WIDTH
        chart_w = W - PRICE_AXIS_WIDTH if has_axis else W
        chart_h = H - DATE_ROW

        candles = self._get_visible_candles(series, chart_w)
        if not candles:
            return Text("")

        _, price_max, price_range = self._price_bounds(candles)
        grid = self._build_grid(candles, chart_w, chart_h, price_max, price_range)
        text = self._build_chart_text(grid, chart_h, has_axis, price_max, price_range)
        self._append_date_row(text, candles, chart_w, has_axis)
        return text
