import pandas as pd
from datetime import datetime, timedelta

from backtest.core import BacktestEngine
from backtest.strategies.example_reup import ExampleReupStrategy


def make_minute_df(start: datetime, n=3, start_price=10.0):
    idx = [start + timedelta(minutes=i) for i in range(n)]
    df = pd.DataFrame({
        "open": [start_price + i * 0.5 for i in range(n)],
        "high": [start_price + i * 0.6 for i in range(n)],
        "low": [start_price + i * 0.4 for i in range(n)],
        "close": [start_price + i * 0.5 for i in range(n)],
        "volume": [100 + i for i in range(n)],
    }, index=pd.DatetimeIndex(idx))
    return df


def test_engine_and_strategy_buy_hold():
    # build engine with two symbols and synthetic data
    symbols = ["000001.SZ", "000002.SZ"]
    start = "20250101"
    end = "20250101"
    engine = BacktestEngine(symbols, start, end, period="1m")

    t0 = datetime(2025, 1, 2, 9, 30)
    engine.bars = {
        "000001.SZ": make_minute_df(t0, n=3, start_price=9.8),
        "000002.SZ": make_minute_df(t0, n=3, start_price=11.0),
    }

    limit_prices = {"000001.SZ": 10.0, "000002.SZ": 11.0}
    pool = symbols
    strat = ExampleReupStrategy(limit_prices, pool, buy_values=1000)

    context = engine.run(strat)

    # trades should contain buys then sells
    trades = context.get("trades", [])
    # we expect at least one buy and one sell for matched conditions
    assert isinstance(trades, list)
    assert any(t.get("qty", 0) > 0 for t in trades)
    assert any(t.get("pnl") is not None for t in trades if t.get("qty", 0) < 0 or t.get("pnl") is not None)
