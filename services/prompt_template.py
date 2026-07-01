PROMPT_TEMPLATE = """\
You are a professional trading signal analyst.

Analyze the following candlestick data for {symbol} and provide a trading signal.

## {fast_tf} candles (recent, for signal timing):
{fast_candles}

## {slow_tf} candles (context, for trend direction):
{slow_candles}
{fundamentals}
Based on this multi-timeframe analysis, provide a trading signal for the {fast_tf} timeframe.

Respond with:
- option: one of "BUY", "SELL", or "HOLD"
- stop_loss: price level for stop loss (optional)
- stop_profit: price level for take profit (optional)
- target_date: estimated date to close the position in YYYY-MM-DD format — always provide a specific date
"""