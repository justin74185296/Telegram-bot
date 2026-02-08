#!/bin/bash
# StockInsightBot 啟動腳本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${RED}錯誤: .env 文件不存在${NC}"
    echo "請複製 .env.example 並配置您的 API 密鑰"
    echo "cp .env.example .env"
    exit 1
fi

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}錯誤: python3 未安裝${NC}"
    exit 1
fi

# 檢查依賴
echo -e "${YELLOW}檢查依賴...${NC}"
pip3 install -r requirements.txt -q

case "$1" in
    start)
        echo -e "${GREEN}啟動 StockInsightBot...${NC}"
        
        # 檢查是否已在運行
        if pgrep -f "python3.*main.py" > /dev/null; then
            echo -e "${YELLOW}Bot 已在運行中${NC}"
            exit 0
        fi
        
        # 啟動 Bot
        nohup python3 main.py > bot.log 2>&1 &
        echo $! > bot.pid
        echo -e "${GREEN}Bot 已啟動，PID: $(cat bot.pid)${NC}"
        echo "日誌文件: bot.log"
        ;;
    
    stop)
        echo -e "${YELLOW}停止 StockInsightBot...${NC}"
        
        if [ -f "bot.pid" ]; then
            kill $(cat bot.pid) 2>/dev/null
            rm -f bot.pid
        fi
        
        pkill -f "python3.*main.py" 2>/dev/null
        echo -e "${GREEN}Bot 已停止${NC}"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if pgrep -f "python3.*main.py" > /dev/null; then
            echo -e "${GREEN}Bot 正在運行${NC}"
            ps aux | grep -E "[p]ython.*main"
        else
            echo -e "${RED}Bot 未運行${NC}"
        fi
        ;;
    
    logs)
        if [ -f "bot.log" ]; then
            tail -f bot.log
        else
            echo "日誌文件不存在"
        fi
        ;;
    
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "  start   - 啟動機器人"
        echo "  stop    - 停止機器人"
        echo "  restart - 重啟機器人"
        echo "  status  - 查看運行狀態"
        echo "  logs    - 查看日誌"
        exit 1
        ;;
esac
