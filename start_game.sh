#!/bin/bash
# ============================================================
# 🌈 魔法跳跳橋 - 一鍵啟動腳本 🌈
# 自動建立虛擬環境、安裝 pygame、啟動遊戲
# 用法：在終端機輸入  bash start_game.sh
# ============================================================

echo ""
echo "🌈 ============================================ 🌈"
echo "   魔法跳跳橋 Magic Bouncy Bridge"
echo "   正在準備遊戲環境..."
echo "🌈 ============================================ 🌈"
echo ""

# 取得腳本所在目錄（確保在正確路徑）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 虛擬環境目錄名稱
VENV_DIR="$SCRIPT_DIR/.venv_game"

# 偵測 Python
PYTHON=""
for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ 找不到 Python！請先安裝 Python 3.10 以上版本。"
    echo "   macOS: brew install python"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo "✅ 找到 $PYTHON_VERSION"

# 如果虛擬環境已經存在且遊戲已安裝，直接啟動
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "✅ 虛擬環境已存在，直接啟動遊戲！"
    source "$VENV_DIR/bin/activate"
    
    # 確認 pygame 有安裝
    if python -c "import pygame" 2>/dev/null; then
        echo "🎮 啟動遊戲中..."
        echo ""
        python "$SCRIPT_DIR/magic_bridge_game.py"
        deactivate 2>/dev/null
        exit 0
    else
        echo "⚠️  pygame 沒裝好，重新安裝..."
        deactivate 2>/dev/null
    fi
fi

# 建立虛擬環境
echo ""
echo "📦 第一次執行，正在建立遊戲環境（只需要一次）..."
echo "   建立虛擬環境中..."

$PYTHON -m venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    echo "❌ 建立虛擬環境失敗！"
    echo "   請試試：$PYTHON -m venv $VENV_DIR"
    exit 1
fi

echo "✅ 虛擬環境建立成功！"

# 啟動虛擬環境
source "$VENV_DIR/bin/activate"

# 升級 pip
echo "   更新 pip..."
python -m pip install --upgrade pip --quiet 2>/dev/null

# 安裝 pygame（先試 pygame-ce，再試 pygame）
echo "   安裝 pygame 中（可能需要 30 秒）..."

# 先試 pygame-ce（對新版 Python 支援比較好）
python -m pip install pygame-ce --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ pygame-ce 安裝成功！"
else
    echo "   pygame-ce 安裝失敗，改試 pygame..."
    python -m pip install pygame --quiet 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ pygame 安裝成功！"
    else
        echo "❌ pygame 安裝失敗！"
        echo ""
        echo "可能的解決方式："
        echo "  1. 安裝較穩定的 Python 版本："
        echo "     brew install python@3.13"
        echo "  2. 然後重新執行此腳本"
        deactivate 2>/dev/null
        exit 1
    fi
fi

# 確認安裝成功
if python -c "import pygame; print('pygame', pygame.version.ver)" 2>/dev/null; then
    echo ""
    echo "🎉 安裝完成！"
    echo ""
    echo "🎮 啟動遊戲中..."
    echo "   （下次直接執行 bash start_game.sh 就好，不用重新安裝）"
    echo ""
    python "$SCRIPT_DIR/magic_bridge_game.py"
else
    echo "❌ pygame 匯入失敗，請手動檢查。"
fi

deactivate 2>/dev/null
