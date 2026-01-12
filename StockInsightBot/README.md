# 📊 StockInsightBot

一个专业的股票分析 Telegram 机器人，使用 AI 生成深度投资分析报告。

## ✨ 功能特点

- 🌍 **多市场支持**：美股、港股、A股
- 📈 **实时行情**：股价、涨跌幅、成交量、市值
- 📊 **财务分析**：PE、PB、ROE 等关键指标
- 🤖 **AI 报告**：深度分析报告，包含投资建议
- 📰 **新闻整合**：近期相关新闻汇总
- ⚡ **智能缓存**：避免重复 API 调用

## 🚀 快速开始

### 1. 克隆项目

```bash
cd StockInsightBot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制配置模板并填入你的密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenAI API 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
```

### 4. 启动机器人

```bash
python main.py
```

## 📝 使用方法

### Telegram 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 显示欢迎信息 | `/start` |
| `/analyze <代码>` | 分析股票 | `/analyze TSLA` |
| `/help` | 查看帮助 | `/help` |

### 股票代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 美股 | 代码 | `AAPL`, `TSLA`, `NVDA` |
| 港股 | 代码.HK | `0700.HK`, `9988.HK` |
| 上证 | 代码.SS | `600519.SS` |
| 深证 | 代码.SZ | `000858.SZ` |

### 快速分析

直接发送股票代码即可分析：

```
TSLA
AAPL
0700.HK
```

## 📁 项目结构

```
StockInsightBot/
├── config/
│   ├── __init__.py
│   └── settings.py         # 配置管理
├── core/
│   ├── __init__.py
│   ├── data_provider.py    # 数据获取
│   ├── financial_analyzer.py # 财务分析
│   └── report_engine.py    # AI报告生成
├── bot/
│   ├── __init__.py
│   ├── handlers.py         # 命令处理
│   └── keyboards.py        # 交互键盘
├── utils/
│   ├── __init__.py
│   ├── formatters.py       # 格式化工具
│   └── loggers.py          # 日志配置
├── .env                    # 环境变量（不要提交）
├── .env.example            # 环境变量模板
├── requirements.txt        # 依赖列表
├── main.py                 # 程序入口
└── README.md
```

## 📊 报告内容

每份分析报告包含：

1. **📈 即时快照** - 当前股价、涨跌、市场情绪
2. **📊 财务深度解析** - 关键指标、盈利质量、成长性
3. **📰 近期动态** - 新闻要点及潜在影响
4. **🔮 未来展望** - 上行驱动与下行风险
5. **💎 核心结论** - 投资价值判断

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram 机器人令牌 | 必填 |
| `OPENAI_API_KEY` | AI API 密钥 | 必填 |
| `OPENAI_BASE_URL` | API 端点 | `https://api.siliconflow.cn/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-ai/DeepSeek-V3` |
| `CACHE_TTL_QUOTE` | 报价缓存时间(秒) | `60` |
| `CACHE_TTL_FINANCIALS` | 财务数据缓存时间(秒) | `3600` |
| `CACHE_TTL_NEWS` | 新闻缓存时间(秒) | `1800` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 🛠️ 技术栈

- **Python 3.9+**
- **python-telegram-bot** - Telegram Bot 框架
- **yfinance** - 股票数据获取
- **openai** - AI 接口
- **pandas** - 数据处理
- **cachetools** - 缓存管理

## ⚠️ 注意事项

1. **API 限制**：yfinance 有请求频率限制，已内置缓存机制
2. **数据延迟**：实时数据可能有 15-20 分钟延迟
3. **投资建议**：AI 生成的报告仅供参考，不构成投资建议
4. **Token 安全**：请勿将 `.env` 文件提交到版本控制

## 📜 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**免责声明**：本机器人生成的分析报告仅供参考，不构成任何投资建议。投资有风险，请谨慎决策。
