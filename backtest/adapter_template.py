"""Adapter template: how to turn a realtime strategy into a backtestable class.

Guidelines to adapt `打板策略.py` / `打第二板策略.py`:

- Extract pure logic functions: `update_cache`, `calculate_factors` and any parameterized rules.
- Replace live I/O (xt_trader.order_*) with context['trades'].append(...) and return simulated fills.
- Ensure functions accept simple data structures (pandas Series for a bar) and avoid global state.

Example skeleton below — copy/paste into a new strategy file and modify for your logic.

class StrategyAdapter:
    def __init__(self, limit_prices, pool, buy_values):
        self.limit_prices = limit_prices
        self.pool = set(pool)
        self.buy_values = buy_values
        self.cache = {}

    def on_start(self, context):
        context.setdefault("positions", {})
        context.setdefault("trades", [])

    def update_cache(self, symbol, bar):
        dq = self.cache.setdefault(symbol, [])
        dq.append(bar)
        if len(dq) > 40:
            dq.pop(0)

    def calculate_factors(self, symbol):
        # implement the same logic as the realtime calculate_factors
        return True

    def on_bar(self, context, ts, bars_at_ts):
        for s, row in bars_at_ts.items():
            if s not in self.pool:
                continue
            self.update_cache(s, row)
            if self.calculate_factors(s):
                # simulate buy
                price = float(row.get("close", 0))
                qty = int((self.buy_values / price) // 100 * 100) or 100
                context["positions"][s] = {"qty": qty, "entry_price": price}
                context["trades"].append({"symbol": s, "qty": qty, "price": price, "ts": ts, "pnl": None})

    def on_finish(self, context):
        # close out positions similar to ExampleReupStrategy
        pass

"""
