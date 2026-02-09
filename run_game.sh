#!/bin/bash
# ============================================
# 🐰 一二三木頭人 - 一鍵啟動腳本
# 適用於 macOS / Linux
# ============================================

# 取得腳本所在的資料夾路徑
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/game_venv"
GAME_FILE="$SCRIPT_DIR/red_light_green_light.py"

echo ""
echo "🐰 一二三木頭人 - 啟動中..."
echo "=========================================="

# 檢查遊戲檔案是否存在
if [ ! -f "$GAME_FILE" ]; then
    echo "❌ 找不到 red_light_green_light.py"
    echo "   請確認此腳本和遊戲檔案放在同一個資料夾"
    exit 1
fi

# 如果虛擬環境不存在，自動建立
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 首次執行，正在建立遊戲環境..."
    python3 -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo "❌ 建立虛擬環境失敗"
        echo "   請確認已安裝 Python 3：brew install python3"
        exit 1
    fi
    
    echo "📥 正在安裝 Pygame..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install pygame --quiet
    
    if [ $? -ne 0 ]; then
        echo "❌ 安裝 Pygame 失敗"
        exit 1
    fi
    
    echo "✅ 安裝完成！"
else
    echo "✅ 遊戲環境已就緒"
fi

echo "🎮 啟動遊戲！玩得開心喔～"
echo "=========================================="
echo ""

# 用虛擬環境的 Python 執行遊戲
"$VENV_DIR/bin/python3" "$GAME_FILE"
