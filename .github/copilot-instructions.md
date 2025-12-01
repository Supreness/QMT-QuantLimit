# QMT-QuantLimit — Copilot / AI agent instructions

Short, actionable notes so an AI assistant can be immediately productive in this repository.

## Big picture — architecture & runtime
- This repo implements a quantitative “打板 / limit‑up capture” strategy for the A‑share market.
- Two execution surfaces:
  - Realtime strategies (top-level scripts like `打板策略.py`, `打第二板策略.py`) that subscribe to market quotes and place live orders via the local QMT client (`xtquant.xttrader`).
  - Backtests and research (`backtest/`) that run offline using `backtest.core.BacktestEngine` and local historical data obtained through `xtquant.xtdata`.

Design rationale (what agents should know): prefer modifying/backtesting logic first (safe, testable), then mirror changes to realtime scripts guarded by dry-run support and explicit testing. Realtime scripts are callback-driven and should avoid blocking operations.

## Key files / places to read (fast path)
- `README.md` — first stop for developer setup (virtualenv, Playwright). See examples.
- `配置文件/config.ini` — runtime configuration used by realtime scripts (must contain `qmt_path`, `stock_account`, `buy_values`). Realtime scripts expect `qmt_path` to point at the QMT client userdata (often `...\userdata_mini`).
- `策略数据初始化.py` — generates `配置文件/{YYYYMMDD}-limit_up_prices.json` (limit prices) by reading local historical data and calculating limit-up prices.
- `配置文件/股票池.txt` — newline-delimited list of stock codes used by strategies and backtests.
- `打板策略.py` and `打第二板策略.py` — realtime, callback-driven strategies that:
  - read `股票池.txt` and `{YYYYMMDD}-limit_up_prices.json`
  - use `xtdata.subscribe_whole_quote` for streaming quotes
  - place orders with `xt_trader.order_stock_async` and receive callbacks via `XtQuantTraderCallback`
- `backtest/core.py` — minimal, explicit backtest engine (Bar-based loop). Good anchor for test-friendly changes.
- `backtest/run_backtest.py` and `backtest/strategies/example_reup.py` — how backtests are wired and example strategy implementing the engine interface (`on_start`, `on_bar`, `on_finish`).
- `tests/test_backtest_core.py` — unit test showing how to synthesize minute bars for the engine; use as a test pattern for strategy code.

## Setup & developer workflows (exact commands)
Windows (PowerShell):
```
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
python -m playwright install  # one-time for selection pipelines
```

Daily dev / run commands:
- Generate daily limit prices (required before live or backtest):
  python 策略数据初始化.py

- Run realtime strategy (live; needs QMT client configured in `配置文件/config.ini`):
  python 打板策略.py
  or
  python 打第二板策略.py

- Run a backtest (uses `配置文件/股票池.txt` and `{start}-limit_up_prices.json`):
  python -m backtest.run_backtest --start 20251101 --end 20251122

- Run unit tests (pytest):
  pytest -q

## Project conventions & common pitfalls (AI agent specifics)
- Language / naming: source files and user text are Chinese — preserve this when adding customer-facing messages, comments, or README snippets.
- Data files: always use relative `./配置文件/*` paths. Two important artifacts:
  - `配置文件/{YYYYMMDD}-limit_up_prices.json` — daily limit prices produced by `策略数据初始化.py`.
  - `配置文件/股票池.txt` — newline-separated stock pool used by realtime/backtests.
- Realtime patterns: callback-driven subscribe -> update caches -> compute factors -> place async order. Do not block the callback thread; heavy work must be moved off callbacks.
- Backtest differences: backtests run offline using local historical data (`xtdata.get_local_data`). Use `backtest/core.py` and `backtest/strategies/example_reup.py` as canonical, testable patterns.
- Order safety: live-order functions are `xt_trader.order_stock_async`. Avoid touching live order calls without adding a `--dry-run` mode or clear simulation harness. Prefer adding unit/backtest coverage before changing order logic.

## Safety & testing notes for AI edits (must-follow)
- Always iterate through backtests first. Backtest code is intentionally small and easy to extend — implement and test new logic in `backtest/` before touching live scripts.
- Add a `--dry-run` or `SIMULATE=true` switch before any change touching `xt_trader.order_*`. Realtime scripts currently call `order_stock_async` directly in `打板策略.py` / `打第二板策略.py`.
- When editing real-time callback code, keep operations non-blocking: use short, deterministic computations inside `on_tick` or offload long-running work to background threads/processes.
- Unit testing pattern: tests synthesize bar DataFrames (see `tests/test_backtest_core.py`); follow that style for new tests.

## Useful change ideas for AI agents (low-risk → high-value)
- Add a `--dry-run` CLI flag to `打板策略.py` and `打第二板策略.py` to avoid placing orders during development.
- Turn `calculate_factors()` and other logic into pure functions with unit tests (easy to add in `tests/`).
- Provide a small simulator that wraps `xt_trader.order_*` calls for dry-run mode and replaying historical ticks for integration tests.
- Improve backtest metrics and plumbing (`backtest/metrics.py`) to support automated regression checks.

## Quick references (files & functions to read)
- `策略数据初始化.py` — limit price generation (`calc_limit_up_price`) and historical data download.
- `打板策略.py` / `打第二板策略.py` — entry points for live trading: `on_tick()`, `update_cache()`, `calculate_factors()`, `XtQuantTrader` usage.
- `backtest/core.py` & `backtest/strategies/example_reup.py` — canonical small backtest design and a test-friendly strategy example.
- `tests/test_backtest_core.py` — unit test style for new agents to follow.

If anything above is unclear or you want me to expand a particular section (backtest flow, safe‑deploy checklist, or examples), tell me which area to deepen and I’ll iterate.
