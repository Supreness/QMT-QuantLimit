import pandas as pd
from typing import Callable, Dict, List, Optional
from datetime import datetime

try:
    from xtquant import xtdata
except Exception:
    xtdata = None


class BacktestEngine:
    """Simple bar-based backtest engine.

    Design goals:
    - Keep small and explicit so it's easy for an AI to extend.
    - Strategy implements a small interface: on_start(context), on_bar(context, time, bars), on_finish(context)

    bars: a dict of {symbol: pd.DataFrame} where each DataFrame is indexed by datetime and contains columns like 'open/high/low/close/volume'
    """

    def __init__(self, symbols: List[str], start_date: str, end_date: str, period: str = "1m"):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.bars: Dict[str, pd.DataFrame] = {}

    def load_local_data(self, field_list: Optional[List[str]] = None):
        """Load historical data using xtquant.xtdata.get_local_data.

        If xtdata is not available the method will raise ImportError.
        """
        if xtdata is None:
            raise ImportError("xtquant.xtdata not available in environment")

        if field_list is None:
            field_list = ["open", "high", "low", "close", "volume", "amount"]

        data = xtdata.get_local_data(
            field_list=field_list,
            stock_list=self.symbols,
            start_time=self.start_date,
            end_time=self.end_date,
            period=self.period,
        )

        # Expect data dict of DataFrames per symbol
        for s in self.symbols:
            if s in data:
                df = data[s].copy()
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                self.bars[s] = df

    def run(self, strategy):
        """Run backtest with supplied strategy object.

        Strategy interface (informal):
        - on_start(context)
        - on_bar(context, ts, bars_at_ts)
        - on_finish(context)
        """
        # Build global time index (intersection of all symbols is optional; we walk union)
        idx = pd.DatetimeIndex(sorted({t for s in self.bars.values() for t in s.index}))

        context = {
            "symbols": self.symbols,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "period": self.period,
            "engine": self,
            "positions": {},
            "orders": [],
            "trades": [],
            "metrics": {},
        }

        # allow strategy to initialize
        if hasattr(strategy, "on_start"):
            strategy.on_start(context)

        for ts in idx:
            # build bars at ts
            bars_at_ts = {}
            for s, df in self.bars.items():
                if ts in df.index:
                    bars_at_ts[s] = df.loc[ts]

            if not bars_at_ts:
                continue

            if hasattr(strategy, "on_bar"):
                strategy.on_bar(context, ts, bars_at_ts)

        if hasattr(strategy, "on_finish"):
            strategy.on_finish(context)

        return context
