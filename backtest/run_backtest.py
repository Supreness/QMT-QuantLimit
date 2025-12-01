"""Entry point: run a backtest locally.

Usage examples:
    python -m backtest.run_backtest --start 20251101 --end 20251122

By default it will use stock pool in `配置文件/股票池.txt` and limit prices file in `配置文件/{start}-limit_up_prices.json`.
"""
import argparse
import json
from backtest.core import BacktestEngine
from backtest.strategies.example_reup import ExampleReupStrategy
from backtest.metrics import summary


def read_stock_pool(path: str = "./配置文件/股票池.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        return lines
    except FileNotFoundError:
        return []


def read_limit_prices(date_str: str):
    path = f"./配置文件/{date_str}-limit_up_prices.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="Start date YYYYMMDD")
    p.add_argument("--end", required=True, help="End date YYYYMMDD")
    p.add_argument("--period", default="1m", help="Data period, e.g. 1m or 1d")
    p.add_argument("--pool", default="./配置文件/股票池.txt", help="Path to stock pool")
    p.add_argument("--limit-date", default=None, help="Which date's limit_up_prices to use (defaults to --start)")
    args = p.parse_args(argv)

    symbols = read_stock_pool(args.pool)
    if not symbols:
        print("No symbols found in pool (配置文件/股票池.txt). Exiting.")
        return 1

    limit_date = args.limit_date or args.start
    limit_prices = read_limit_prices(limit_date)

    engine = BacktestEngine(symbols, args.start, args.end, period=args.period)
    print("Loading local historical data (xtquant.xtdata) — ensure historical data is downloaded")
    engine.load_local_data()

    strat = ExampleReupStrategy(limit_prices, symbols)
    context = engine.run(strat)

    m = summary(context)
    print("Backtest finished — summary:")
    print(m)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
