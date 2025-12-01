"""Example backtest-friendly strategy inspired by 打第二板策略.py

This strategy demonstrates the callback interface for BacktestEngine.
It follows a simplified rule:
 - if the minute close >= supplied `limit_up_price` and symbol is in stock pool -> place a buy
 - buy quantity is derived from `buy_values` in context
 - position is held until `on_finish`, then PnL is calculated using last price available

This example is meant to be easily testable and modified by AI agents.
"""
from typing import Dict


class ExampleReupStrategy:
    def __init__(self, limit_up_prices: Dict[str, float], stock_pool: list, buy_values: int = 10000):
        self.limit_up_prices = limit_up_prices
        self.stock_pool = set(stock_pool)
        self.buy_values = buy_values

    def on_start(self, context):
        context.setdefault("positions", {})
        context.setdefault("trades", [])

    def on_bar(self, context, ts, bars_at_ts):
        # bars_at_ts: {symbol: pd.Series}
        for s, row in bars_at_ts.items():
            if s not in self.stock_pool:
                continue

            close = float(row.get("close", row.get("lastPrice", 0)))
            limit_price = self.limit_up_prices.get(s)
            if limit_price is None:
                continue

            # If price reaches or exceeds limit price: buy if not held yet
            if close >= limit_price and s not in context["positions"]:
                qty = int((self.buy_values / close) // 100 * 100) or 100
                context["positions"][s] = {"qty": qty, "entry_price": close}
                context["trades"].append({"symbol": s, "qty": qty, "price": close, "ts": ts, "pnl": None})

    def on_finish(self, context):
        # Close remaining positions at last available price
        for s, pos in list(context["positions"].items()):
            # find last price in engine bars
            df = context["engine"].bars.get(s)
            if df is None or len(df) == 0:
                last_price = pos["entry_price"]
            else:
                last_price = float(df.iloc[-1]["close"])

            entry_price = pos["entry_price"]
            qty = pos["qty"]
            pnl = (last_price - entry_price) * qty
            context["trades"].append({"symbol": s, "qty": -qty, "price": last_price, "ts": None, "pnl": pnl})
            # remove position
            del context["positions"][s]
