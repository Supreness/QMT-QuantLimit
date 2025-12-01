"""Lightweight backtest metrics helpers.

These helpers operate on the `context` object produced by BacktestEngine.run.
"""
from typing import Dict, Any


def summary(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a small performance summary.

    Expects context to contain `trades` list of dicts with at least: symbol, qty, price, pnl
    """
    trades = context.get("trades", [])
    metrics = {}
    metrics["n_trades"] = len(trades)
    metrics["total_pnl"] = sum(t.get("pnl", 0) for t in trades)
    metrics["avg_pnl"] = (metrics["total_pnl"] / metrics["n_trades"]) if metrics["n_trades"] else 0
    if trades:
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        metrics["win_rate"] = len(wins) / len(trades)
    else:
        metrics["win_rate"] = 0

    return metrics
