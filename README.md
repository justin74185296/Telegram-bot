# Aster Perpetuals Trading Bot

Automated trading bot for **BTC/USDT** and **ETH/USDT** perpetual contracts on [Aster DEX](https://asterdex.com) (Binance Wallet Web Perpetuals).

Built with **CCXT** (Binance-futures compatible), **pandas_ta** for indicators, and a modular architecture designed for clarity and extensibility.

---

## Features

| Feature | Details |
|---|---|
| **Dual-direction trading** | Long & short based on EMA crossover signals |
| **Technical indicators** | EMA(9) / EMA(21) crossover + RSI(14) filter |
| **Risk management** | 1% risk per trade, 1.5% SL, 3% TP |
| **Leverage** | Fixed 5× isolated margin |
| **OpenClaw monitor** | Auto-pause after 3 consecutive losses or >5% drawdown |
| **Paper trading** | Full simulation mode with real market data |
| **Web Dashboard** | Real-time browser dashboard with auto-refresh |
| **Resilience** | Exponential-backoff retries, graceful shutdown (Ctrl+C) |

---

## Strategy

```
LONG entry  : EMA9 crosses ABOVE EMA21  AND  RSI(14) < 60
SHORT entry : EMA9 crosses BELOW EMA21  AND  RSI(14) > 40
EXIT        : Reverse EMA crossover  OR  SL/TP hit
```

- **Timeframe**: 15-minute candles
- **Stop-Loss**: ±1.5% from entry
- **Take-Profit**: ±3.0% from entry
- Only one position per symbol at a time

---

## Project Structure

```
aster_perpetuals_bot/
├── __init__.py        # Package version
├── __main__.py        # python -m entrypoint
├── config.py          # All settings & env-var loading
├── indicators.py      # EMA, RSI computation (pure pandas)
├── exchange.py        # CCXT wrapper (Binance futures / Aster)
├── risk_manager.py    # Position sizing, SL/TP, OpenClaw monitor
├── strategy.py        # Signal generation & trade execution
├── paper_engine.py    # Simulated balance tracker
├── shared_state.py    # Thread-safe state (bot ↔ dashboard)
├── dashboard.py       # Flask web dashboard (auto-refresh UI)
└── bot.py             # Main loop orchestration
```

---

## Quick Start

### 方法一：使用啟動腳本（推薦，macOS / Linux 皆適用）

```bash
# 1. 複製環境變數範本並填入你的 API Key
cp .env.example .env
nano .env    # 或用任何編輯器

# 2. 執行啟動腳本（會自動建立 venv、安裝依賴、啟動 bot）
chmod +x run.sh
./run.sh
```

### 方法二：手動設定虛擬環境

```bash
# 1. 建立虛擬環境
python3 -m venv venv

# 2. 啟動虛擬環境
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 複製並設定環境變數
cp .env.example .env
nano .env

# 5. 啟動 bot
python -m aster_perpetuals_bot
```

> **注意**：macOS Homebrew 管理的 Python 不允許直接 `pip install`，  
> **必須**先建立虛擬環境（venv），這是 [PEP 668](https://peps.python.org/pep-0668/) 的要求。

### 環境變數設定

編輯 `.env` 檔案：

```dotenv
ASTER_API_KEY=your_api_key_here
ASTER_API_SECRET=your_api_secret_here
TRADING_MODE=paper          # "paper" 模擬模式 / "live" 真實交易
# ASTER_API_URL=https://pro-api.asterdex.com  # 可選：Aster 自訂 endpoint
```

### 停止 Bot

按 **Ctrl+C** 即可優雅關機（會完成當前循環後才停止）。

---

## Configuration Reference

All parameters are in `aster_perpetuals_bot/config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `TRADING_MODE` | `paper` | `paper` = simulation, `live` = real funds |
| `ASTER_API_KEY` | *(empty)* | API key for Aster / Binance futures |
| `ASTER_API_SECRET` | *(empty)* | API secret |
| `ASTER_API_URL` | *(empty)* | Custom base URL for Aster Pro API |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Trading Parameters (in `config.py`)

| Parameter | Value | Description |
|---|---|---|
| `SYMBOLS` | BTC/USDT:USDT, ETH/USDT:USDT | Perpetual pairs to trade |
| `TIMEFRAME` | 15m | K-line interval |
| `LEVERAGE` | 5 | Isolated margin leverage |
| `RISK_PER_TRADE_PCT` | 1.0% | Max risk per trade |
| `STOP_LOSS_PCT` | 1.5% | SL distance from entry |
| `TAKE_PROFIT_PCT` | 3.0% | TP distance from entry |
| `EMA_SHORT_PERIOD` | 9 | Fast EMA |
| `EMA_LONG_PERIOD` | 21 | Slow EMA |
| `RSI_PERIOD` | 14 | RSI look-back |
| `POLL_INTERVAL_SEC` | 60 | Seconds between iterations |

---

## Web Dashboard

The bot includes a **built-in web dashboard** that launches automatically on startup.

Open your browser to **http://localhost:8080** to see:

- **Bot status** — running / paused / stopped, with cycle counter
- **Balance & PnL** — current balance, total profit/loss, percentage change
- **Open positions** — per-symbol with entry price, SL/TP, unrealised PnL
- **Live indicators** — EMA(9), EMA(21), RSI(14) with visual bars, latest signal
- **Trade history** — complete log of all executed trades with PnL
- **OpenClaw monitor** — win rate, consecutive losses, pause status
- **Live logs** — streaming log output in the browser

The dashboard auto-refreshes every 5 seconds. Change the port via `DASHBOARD_PORT` env var.

---

## Aster DEX API Compatibility

Aster Pro API is **Binance-futures compatible**. The bot uses `ccxt.binance` with `defaultType: future`.

If Aster publishes a dedicated endpoint (e.g. `https://pro-api.asterdex.com`), set the `ASTER_API_URL` environment variable and the bot will override CCXT's base URLs automatically.

Refer to the [Aster API documentation](https://docs.asterdex.com/product/aster-perpetuals/api) for specifics.

---

## OpenClaw Safety Monitor

The built-in supervisor tracks every trade and will **auto-pause** the bot when:

1. **3 consecutive losses** are recorded, OR
2. **Cumulative loss exceeds 5%** of the starting balance.

When paused, the bot logs a `CRITICAL` alert and stops opening new positions. Manual intervention (code-level `monitor.resume()`) is required to restart trading.

---

## Disclaimer

This bot is provided for **educational and research purposes only**. Cryptocurrency trading carries significant risk. Use at your own risk. Always start with paper trading to validate the strategy before deploying real funds.
