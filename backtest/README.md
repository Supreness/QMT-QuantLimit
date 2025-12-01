# Backtest framework (lightweight)

This small backtest framework is intended to be easy for AI agents to read, modify and extend. It is independent from the live strategy `打板策略.py` and `打第二板策略.py` and relies on historical data from `xtquant.xtdata`.

How to run (PowerShell):

```powershell
python -m backtest.run_backtest --start 20251101 --end 20251122 --period 1m
```

What it contains:
- core.py — light BacktestEngine that runs a strategy over a unified time index
- metrics.py — tiny helpers to summarize trades
- strategies/example_reup.py — small example strategy adapted from real strategies (keeps logic testable)
- run_backtest.py — entry point that reads `配置文件/股票池.txt` and `配置文件/{date}-limit_up_prices.json`

Notes for contributors:
- Unit tests should avoid calling `xtquant` functions directly — mock `BacktestEngine.bars` or provide small fixture DataFrames.
- For new strategies, implement `on_start`, `on_bar`, `on_finish` for maximum compatibility.
