# StockInsightBot 📈

專業級 Telegram 股票分析機器人，提供實時行情、AI 深度分析和財務指標解讀。

## 功能特點

- 🔍 **實時報價** - 獲取最新股價、漲跌幅、成交量
- 🤖 **AI 分析** - 使用 DeepSeek-V3 生成專業分析報告
- 📊 **財務指標** - PE/PB/ROE 等關鍵指標解讀
- 📰 **新聞整合** - 彙整近期相關新聞
- 🌍 **多市場支援** - 美股、港股、A股

## 快速開始

### 1. 安裝依賴

```bash
cd StockInsightBot
pip install -r requirements.txt
```

### 2. 配置環境變量

複製 `.env.example` 為 `.env` 並填入您的配置：

```bash
cp .env.example .env
```

編輯 `.env` 文件：

```env
# Telegram Bot Token (從 @BotFather 獲取)
TELEGRAM_BOT_TOKEN=your_token_here

# AI API 配置
AI_API_KEY=your_api_key_here
AI_API_BASE=https://api.siliconflow.cn/v1
AI_MODEL=deepseek-ai/DeepSeek-V3
```

### 3. 啟動機器人

```bash
python main.py
```

## 使用方法

### 基本命令

| 命令 | 說明 |
|------|------|
| `/start` | 啟動機器人，查看歡迎訊息 |
| `/help` | 查看完整使用指南 |
| `/analyze <代碼>` | 分析指定股票 |

### 股票代碼格式

- **美股**: 直接輸入代碼，如 `AAPL`, `TSLA`, `GOOGL`
- **港股**: 輸入 4 位數字，如 `0700`, `9988`
- **A股**: 輸入 6 位數字，如 `600519`, `000001`

### 快速查詢

直接發送股票代碼即可觸發分析，無需輸入命令。

## 項目結構

```
StockInsightBot/
├── config/
│   ├── __init__.py
│   └── settings.py         # 配置管理
├── core/
│   ├── __init__.py
│   ├── data_provider.py    # 數據獲取層
│   ├── financial_analyzer.py # 財務分析
│   └── report_engine.py    # AI 報告生成
├── bot/
│   ├── __init__.py
│   ├── handlers.py         # Telegram 處理器
│   └── keyboards.py        # 內聯鍵盤
├── utils/
│   ├── __init__.py
│   ├── formatters.py       # 格式化工具
│   └── loggers.py          # 日誌配置
├── .env                    # 環境變量（不要提交）
├── .env.example            # 環境變量模板
├── requirements.txt        # 依賴列表
├── main.py                 # 程式入口
└── README.md               # 說明文件
```

## 分析報告內容

每份報告包含以下部分：

1. **📈 即時快照** - 當前股價、漲跌、市場情緒
2. **📊 財務深度解析** - 估值、盈利能力、財務健康度
3. **📰 近期動態整合** - 新聞摘要與影響分析
4. **🔮 未來展望** - 上行驅動與下行風險
5. **💎 核心結論** - 投資價值判斷

## 技術棧

- **語言**: Python 3.9+
- **Telegram 框架**: python-telegram-bot v20+
- **數據獲取**: yfinance
- **AI 模型**: DeepSeek-V3 (via SiliconFlow)
- **數據處理**: pandas, numpy

## 注意事項

- 機器人需要持續運行才能回應消息
- 數據每 5 分鐘自動更新
- AI 報告生成需要 10-30 秒
- 部分股票可能缺少某些財務數據

## 部署建議

如需 24/7 運行，建議部署到：
- 雲服務器 (AWS, GCP, Azure)
- VPS
- Heroku
- Railway

## License

MIT License
