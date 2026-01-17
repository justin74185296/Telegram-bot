# StockInsightBot

專業股票分析 Telegram 機器人，使用 AI 生成深度投資分析報告。

## 功能特點

- 📊 **即時行情** - 獲取股票最新價格和漲跌
- 📈 **深度分析** - AI 生成專業投資報告
- 📰 **新聞整合** - 獲取相關市場新聞
- 💹 **財務指標** - PE、PB、ROE 等關鍵數據

## 支持市場

- 🇺🇸 美股：AAPL, TSLA, GOOGL, MSFT
- 🇭🇰 港股：0700, 9988
- 🇨🇳 A股：600519, 000001

## 安裝

```bash
# 安裝依賴
pip install -r requirements.txt

# 配置環境變量
cp .env.example .env
# 編輯 .env 填入你的 Token 和 API Key
```

## 配置

在 `.env` 文件中設置：

```
TELEGRAM_BOT_TOKEN=你的Telegram Bot Token
AI_API_KEY=你的AI API Key
AI_BASE_URL=https://api.siliconflow.cn/v1
AI_MODEL=deepseek-ai/DeepSeek-V3
```

## 啟動

```bash
python main.py
```

## 使用方法

在 Telegram 中：

1. 搜索並開啟 Bot
2. 發送 `/start` 開始使用
3. 發送 `/analyze TSLA` 分析特斯拉
4. 或直接發送股票代碼如 `AAPL`

## 命令列表

| 命令 | 說明 |
|------|------|
| `/start` | 開始使用，顯示歡迎信息 |
| `/analyze <代碼>` | 分析指定股票 |
| `/help` | 顯示幫助信息 |

## 專案結構

```
StockInsightBot/
├── config/           # 配置管理
├── core/             # 核心功能
│   ├── data_provider.py    # 數據獲取
│   ├── financial_analyzer.py # 財務分析
│   └── report_engine.py    # AI報告生成
├── bot/              # Telegram Bot
│   ├── handlers.py   # 命令處理
│   └── keyboards.py  # 內聯鍵盤
├── utils/            # 工具模組
├── main.py           # 程序入口
└── requirements.txt  # 依賴列表
```

## 技術棧

- Python 3.9+
- python-telegram-bot 20.x
- yfinance (股票數據)
- OpenAI API (DeepSeek-V3)
