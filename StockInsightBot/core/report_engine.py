"""
AI 報告生成引擎
使用大語言模型生成專業的股票分析報告
"""
import json
from typing import Dict, Any, Optional
from config.settings import settings
from utils.loggers import get_logger
from utils.formatters import Formatters

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = get_logger("ReportEngine")


class StockReportEngine:
    """
    股票報告引擎
    使用 AI 生成專業分析報告
    """
    
    # 系統角色設定
    SYSTEM_PROMPT = """你是一名經驗豐富的買方投資分析師，專注於基本面研究和投資價值分析。
你擅長從海量數據中提煉關鍵洞察，用清晰專業的語言向投資者傳達分析結論。

你的分析風格：
1. 數據驅動：所有觀點必須有數據支撐
2. 客觀中立：不帶有情緒化的判斷
3. 風險意識：始終關注潛在風險
4. 結構清晰：邏輯嚴謹，重點突出

輸出規範：
- 使用繁體中文
- 使用 Markdown 格式
- 數字需精確，並標註數據來源或時間點
- 避免模糊表述，給出具體的量化分析"""

    # 報告模板
    REPORT_TEMPLATE = """請根據以下數據，為 {symbol} ({name}) 生成一份專業的投資分析報告。

## 提供的數據

### 即時報價
{quote_data}

### 關鍵財務指標
{indicators_data}

### 近期新聞
{news_data}

### 歷史表現
{history_data}

---

## 報告要求

請嚴格按照以下結構組織報告：

### 📈 即時快照
- 當前股價與變動
- 市場表現概述
- 交易活躍度評估

### 📊 財務深度解析
- 使用表格對比關鍵指標
- 分析估值水平（PE、PB等）
- 評估盈利質量與成長性
- 判斷財務健康度

### 📰 近期動態整合
- 總結重要新聞要點
- 分析新聞對股價的潛在影響
- 識別市場情緒變化

### 🔮 未來展望與風險評估
- 列出 2-3 個核心上行驅動因素
- 列出 2-3 個主要下行風險
- 基於數據給出理性預判

### 💎 核心結論
用 3 個要點總結：
1. 投資價值判斷
2. 主要關注點
3. 建議行動

---
注意：如果某些數據缺失，請標註「數據暫缺」而非編造數據。"""

    def __init__(self):
        """初始化報告引擎"""
        self.client = None
        self.model = settings.ai_model
        self.formatter = Formatters()

        if settings.ai_enabled and OpenAI is not None:
            try:
                self.client = OpenAI(
                    api_key=settings.ai_api_key,
                    base_url=settings.ai_api_base
                )
                logger.info(f"報告引擎初始化完成，使用模型: {self.model}")
            except Exception as e:
                logger.warning(f"AI 客戶端初始化失敗: {e}，將使用基礎報告")
        else:
            logger.info("AI 未配置，報告引擎將使用基礎報告模式")
    
    def _format_quote_data(self, quote: Dict[str, Any]) -> str:
        """格式化報價數據"""
        if "error" in quote:
            return f"數據獲取失敗: {quote['error']}"
        
        return f"""- 股票代碼: {quote.get('symbol', 'N/A')}
- 公司名稱: {quote.get('name', 'N/A')}
- 當前價格: {self.formatter.format_price(quote.get('current_price'), quote.get('currency', '$'))}
- 漲跌幅: {self.formatter.format_percentage(quote.get('change_percent'))} ({self.formatter.get_trend_emoji(quote.get('change_percent'))})
- 開盤價: {self.formatter.format_price(quote.get('open'), quote.get('currency', '$'))}
- 最高價: {self.formatter.format_price(quote.get('high'), quote.get('currency', '$'))}
- 最低價: {self.formatter.format_price(quote.get('low'), quote.get('currency', '$'))}
- 前收盤價: {self.formatter.format_price(quote.get('previous_close'), quote.get('currency', '$'))}
- 成交量: {self.formatter.format_volume(quote.get('volume'))}
- 市值: {self.formatter.format_market_cap(quote.get('market_cap'))}
- 52週最高: {self.formatter.format_price(quote.get('fifty_two_week_high'), quote.get('currency', '$'))}
- 52週最低: {self.formatter.format_price(quote.get('fifty_two_week_low'), quote.get('currency', '$'))}
- 交易所: {quote.get('exchange', 'N/A')}
- 數據時間: {quote.get('timestamp', 'N/A')}"""
    
    def _format_indicators_data(self, indicators: Dict[str, Any]) -> str:
        """格式化指標數據"""
        if "error" in indicators:
            return f"數據獲取失敗: {indicators['error']}"
        
        def safe_format(value, is_percent=False, multiplier=1):
            if value is None:
                return "N/A"
            try:
                value = float(value) * multiplier
                if is_percent:
                    return f"{value:.2f}%"
                return f"{value:.2f}"
            except:
                return "N/A"
        
        return f"""**估值指標**
- P/E 比率: {safe_format(indicators.get('pe_ratio'))}
- P/B 比率: {safe_format(indicators.get('pb_ratio'))}
- P/S 比率: {safe_format(indicators.get('ps_ratio'))}
- PEG 比率: {safe_format(indicators.get('peg_ratio'))}

**盈利能力**
- EPS: {safe_format(indicators.get('eps'))}
- ROE: {safe_format(indicators.get('roe'), True, 100)}
- ROA: {safe_format(indicators.get('roa'), True, 100)}
- 淨利率: {safe_format(indicators.get('profit_margin'), True, 100)}
- 營業利潤率: {safe_format(indicators.get('operating_margin'), True, 100)}

**成長指標**
- 營收成長率: {safe_format(indicators.get('revenue_growth'), True, 100)}
- 盈利成長率: {safe_format(indicators.get('earnings_growth'), True, 100)}

**財務健康**
- 負債權益比: {safe_format(indicators.get('debt_to_equity'))}
- 流動比率: {safe_format(indicators.get('current_ratio'))}
- 速動比率: {safe_format(indicators.get('quick_ratio'))}

**現金流**
- 自由現金流: {self.formatter.format_market_cap(indicators.get('free_cash_flow'))}
- 營運現金流: {self.formatter.format_market_cap(indicators.get('operating_cash_flow'))}

**股息**
- 股息率: {safe_format(indicators.get('dividend_yield'), True, 100)}
- 股息: {safe_format(indicators.get('dividend_rate'))}

**風險**
- Beta: {safe_format(indicators.get('beta'))}"""
    
    def _format_news_data(self, news: list) -> str:
        """格式化新聞數據"""
        if not news:
            return "暫無相關新聞"
        
        lines = []
        for i, item in enumerate(news, 1):
            title = item.get('title', '無標題')
            publisher = item.get('publisher', '未知來源')
            pub_time = item.get('published_time', '')
            lines.append(f"{i}. **{title}**")
            lines.append(f"   來源: {publisher} | 時間: {pub_time}")
        
        return "\n".join(lines)
    
    def _format_history_data(self, history: Dict[str, Any]) -> str:
        """格式化歷史數據"""
        if "error" in history:
            return f"數據獲取失敗: {history['error']}"
        
        summary = history.get('summary', {})
        period = history.get('period', 'N/A')
        
        return f"""- 統計週期: {period}
- 期初價格: {self.formatter.format_price(summary.get('start_price'))}
- 期末價格: {self.formatter.format_price(summary.get('end_price'))}
- 期間漲跌幅: {self.formatter.format_percentage(summary.get('period_return'))}
- 期間最高: {self.formatter.format_price(summary.get('high'))}
- 期間最低: {self.formatter.format_price(summary.get('low'))}
- 平均成交量: {self.formatter.format_volume(summary.get('avg_volume'))}"""
    
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """
        生成股票分析報告
        
        Args:
            data: 完整的股票數據（包含 quote, indicators, news, history）
        
        Returns:
            AI 生成的分析報告
        """
        quote = data.get('quote', {})
        symbol = quote.get('symbol', 'Unknown')
        name = quote.get('name', 'Unknown')
        
        logger.info(f"開始生成 {symbol} 的分析報告...")
        
        # 構建提示詞
        prompt = self.REPORT_TEMPLATE.format(
            symbol=symbol,
            name=name,
            quote_data=self._format_quote_data(quote),
            indicators_data=self._format_indicators_data(data.get('indicators', {})),
            news_data=self._format_news_data(data.get('news', [])),
            history_data=self._format_history_data(data.get('history', {}))
        )
        
        if not self.client:
            logger.info(f"AI 未啟用，使用基礎報告: {symbol}")
            return self._generate_fallback_report(data)

        try:
            # 調用 AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            report = response.choices[0].message.content
            logger.info(f"報告生成成功: {symbol}")
            return report
            
        except Exception as e:
            logger.error(f"報告生成失敗: {e}")
            return self._generate_fallback_report(data)
    
    def _generate_fallback_report(self, data: Dict[str, Any]) -> str:
        """
        當 AI 調用失敗時生成基礎報告
        
        Args:
            data: 股票數據
        
        Returns:
            基礎報告文本
        """
        quote = data.get('quote', {})
        indicators = data.get('indicators', {})
        
        symbol = quote.get('symbol', 'Unknown')
        name = quote.get('name', 'Unknown')
        
        return f"""# {symbol} - {name} 分析報告

## 📈 即時快照

**當前價格**: {self.formatter.format_price(quote.get('current_price'))}
**漲跌幅**: {self.formatter.format_percentage(quote.get('change_percent'))} {self.formatter.get_trend_emoji(quote.get('change_percent'))}
**市值**: {self.formatter.format_market_cap(quote.get('market_cap'))}
**成交量**: {self.formatter.format_volume(quote.get('volume'))}

## 📊 關鍵指標

| 指標 | 數值 |
|------|------|
| P/E 比率 | {indicators.get('pe_ratio', 'N/A')} |
| P/B 比率 | {indicators.get('pb_ratio', 'N/A')} |
| ROE | {self.formatter.format_percentage((indicators.get('roe') or 0) * 100)} |
| 股息率 | {self.formatter.format_percentage((indicators.get('dividend_yield') or 0) * 100)} |

## 📰 近期新聞

{self._format_news_data(data.get('news', []))}

---
⚠️ *此為基礎報告，AI 分析暫時不可用*
*數據時間: {quote.get('timestamp', 'N/A')}*"""

    async def generate_quick_summary(self, quote: Dict[str, Any]) -> str:
        """
        生成快速摘要
        
        Args:
            quote: 報價數據
        
        Returns:
            簡短摘要
        """
        symbol = quote.get('symbol', 'Unknown')
        name = quote.get('name', 'Unknown')
        price = quote.get('current_price', 0)
        change = quote.get('change_percent', 0)
        volume = quote.get('volume', 0)
        market_cap = quote.get('market_cap', 0)
        
        trend = self.formatter.get_trend_emoji(change)
        
        return f"""**{symbol}** - {name} {trend}

💰 **{self.formatter.format_price(price, quote.get('currency', '$'))}** ({self.formatter.format_percentage(change)})

📊 成交量: {self.formatter.format_volume(volume)}
🏢 市值: {self.formatter.format_market_cap(market_cap)}

📅 *{quote.get('timestamp', '')}*"""
