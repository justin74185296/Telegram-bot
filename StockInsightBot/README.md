# 📈 StockInsightBot

> 专业级股票分析 Telegram 机器人，集成实时行情、财务分析与 AI 深度报告生成

## ✨ 功能特性

- 📊 **实时行情** - 获取美股、港股、A股的实时价格和涨跌数据
- 📈 **财务分析** - 深度解析公司资产负债表、利润表、现金流量表
- 📰 **新闻整合** - 汇总近期相关新闻动态及影响分析
- 🤖 **AI报告** - 利用 GPT-4/4o 生成专业投资分析报告
- 🔄 **智能缓存** - 内置缓存机制，避免频繁API调用

## 🏗️ 项目结构

```
StockInsightBot/
│
├── config/
│   ├── __init__.py
│   └── settings.py         # 配置管理（环境变量读取）
│
├── core/
│   ├── __init__.py
│   ├── data_provider.py    # 统一数据获取层（yfinance/akshare）
│   ├── financial_analyzer.py # 财务指标计算与分析
│   └── report_engine.py    # AI报告生成核心
│
├── bot/
│   ├── __init__.py
│   ├── handlers.py         # Telegram 命令处理器
│   └── keyboards.py        # 内联键盘组件
│
├── utils/
│   ├── __init__.py
│   ├── formatters.py       # 数字、文本格式化工具
│   └── loggers.py          # 日志配置
│
├── .env.example            # 环境变量模板
├── requirements.txt        # 项目依赖
├── main.py                 # 程序入口
└── README.md               # 说明文档
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.9 或更高版本
- Telegram Bot Token（通过 @BotFather 创建）
- OpenAI API Key

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd StockInsightBot

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入您的配置
```

必须配置的环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF...` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |

可选配置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_MODEL` | 使用的模型 | `gpt-4o` |
| `CACHE_TTL` | 缓存过期时间（秒） | `300` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 4. 启动机器人

```bash
python main.py
```

启动成功后，在 Telegram 中搜索您的机器人用户名即可开始使用。

## 📱 使用指南

### 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 显示欢迎信息 | `/start` |
| `/help` | 显示帮助文档 | `/help` |
| `/analyze [代码]` | 生成深度分析报告 | `/analyze TSLA` |
| `/quote [代码]` | 获取实时报价 | `/quote AAPL` |
| `/news [代码]` | 获取相关新闻 | `/news NVDA` |

### 支持的股票代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 美股 | 直接输入代码 | `AAPL`, `TSLA`, `NVDA` |
| 港股 | 代码 + `.HK` | `0700.HK`, `9988.HK` |
| A股 | 6位数字代码 | `600519`, `000858` |

### 分析报告内容

生成的分析报告包含以下部分：

1. **📈 即时快照** - 当前股价、涨跌情况、市场情绪
2. **📊 财务深度解析** - 季度财务趋势、盈利质量、成长性
3. **📰 近期动态集成** - 新闻摘要及影响分析
4. **🔮 未来展望与风险** - 上行驱动与下行风险评估
5. **💎 核心结论** - 3点关键总结

## 🔧 高级配置

### 自定义 AI 提示词

可以在 `core/report_engine.py` 中修改 `SYSTEM_PROMPT` 和 `REPORT_TEMPLATE` 来自定义报告风格。

### 数据源切换

默认使用 `yfinance` 获取数据，A股/港股会自动尝试 `akshare` 作为备选数据源。

### 缓存配置

```python
# 在 .env 中配置
CACHE_TTL=300        # 缓存过期时间（秒）
CACHE_MAX_SIZE=100   # 最大缓存条目数
```

## 🛠️ 开发指南

### 项目架构

```
┌─────────────────┐
│   Telegram Bot  │
│   (handlers.py) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Report Engine  │
│ (report_engine) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ Data  │ │ Financial│
│Provider│ │ Analyzer │
└───────┘ └──────────┘
```

### 添加新命令

在 `bot/handlers.py` 中添加新的处理方法：

```python
async def new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /new 命令"""
    # 实现逻辑
    pass
```

然后在 `setup_handlers` 函数中注册：

```python
application.add_handler(CommandHandler("new", handlers.new_command))
```

### 运行测试

```bash
# 安装测试依赖（如果需要）
pip install pytest pytest-asyncio

# 运行测试
pytest tests/
```

## 📝 注意事项

1. **API 限制**：yfinance 和 OpenAI 都有请求频率限制，建议合理配置缓存时间
2. **数据延迟**：股票数据可能有 15-20 分钟延迟，请以官方数据为准
3. **投资建议**：本机器人生成的报告仅供参考，不构成投资建议
4. **费用**：使用 OpenAI API 会产生费用，请注意用量

## 🐛 常见问题

### Q: 启动时报错 "TELEGRAM_BOT_TOKEN 未设置"
A: 请确保 `.env` 文件存在且正确配置了 `TELEGRAM_BOT_TOKEN`

### Q: 分析报告生成很慢
A: OpenAI API 调用需要时间，通常 10-30 秒，请耐心等待

### Q: 无法获取某些股票数据
A: 部分小众股票或新上市股票可能数据不完整，请尝试其他股票

### Q: A股数据获取失败
A: 确保已安装 `akshare` 包，且网络可以访问相关数据源

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题，请通过 GitHub Issues 反馈。
