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
├── indicators.py      # EMA, RSI computation (pandas_ta)
├── exchange.py        # CCXT wrapper (Binance futures / Aster)
├── risk_manager.py    # Position sizing, SL/TP, OpenClaw monitor
├── strategy.py        # Signal generation & trade execution
├── paper_engine.py    # Simulated balance tracker
└── bot.py             # Main loop orchestration
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example env file and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
ASTER_API_KEY=your_api_key_here
ASTER_API_SECRET=your_api_secret_here
TRADING_MODE=paper          # "paper" or "live"
# ASTER_API_URL=https://pro-api.asterdex.com  # optional custom endpoint
```

### 3. Run the bot

```bash
# Paper trading (default)
python -m aster_perpetuals_bot

# Or directly
python aster_perpetuals_bot/bot.py
```

Press **Ctrl+C** for graceful shutdown.

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
