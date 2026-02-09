#!/usr/bin/env bash
# ============================================================
#  Aster Perpetuals Bot — one-click launcher
#
#  This script:
#    1. Creates a Python virtual environment (if not exists)
#    2. Installs / updates dependencies
#    3. Launches the trading bot
#
#  Usage:
#    chmod +x run.sh
#    ./run.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=========================================="
echo "  Aster Perpetuals Trading Bot Launcher"
echo "=========================================="

# ---- 1. Check Python3 ----
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Please install Python 3.10+ first."
    echo "  macOS:   brew install python"
    echo "  Ubuntu:  sudo apt install python3 python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[INFO] Python version: $PYTHON_VERSION"

# ---- 2. Create venv if needed ----
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    echo "[INFO] Virtual environment created."
else
    echo "[INFO] Virtual environment already exists."
fi

# ---- 3. Activate venv ----
echo "[INFO] Activating virtual environment ..."
source "$VENV_DIR/bin/activate"

# ---- 4. Install / update dependencies ----
echo "[INFO] Installing dependencies ..."
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo "[INFO] Dependencies installed."

# ---- 5. Check .env ----
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "[WARN] .env file not found!"
    echo "       Copying .env.example → .env"
    echo "       Please edit .env to add your API key/secret before live trading."
    echo ""
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

# ---- 6. Launch bot ----
echo ""
echo "=========================================="
echo "  Starting bot ... (Ctrl+C to stop)"
echo "=========================================="
echo ""

cd "$SCRIPT_DIR"
python -m aster_perpetuals_bot
