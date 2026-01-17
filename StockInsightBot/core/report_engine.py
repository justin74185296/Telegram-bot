"""
AI 報告生成引擎
使用大語言模型生成專業股票分析報告
"""
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)


class StockReportEngine:
    """股票報告生成引擎"""
    
    # 系統提示詞 - 定義 AI 角色
    SYSTEM_PROMPT = """你是一名嚴謹的買方投資分析師，擅長從海量信息中提煉關鍵洞察。
你的分析風格專業、客觀、數據驅動。
你需要基於提供的數據生成結構化的投資分析報告。
報告使用繁體中文撰寫。"""

    # 報告模板
    REPORT_TEMPLATE = """請基於以下股票數據，生成一份專業的投資分析報告。

## 股票數據

### 基本信息
- 股票代碼: {symbol}
- 公司名稱: {name}
- 所屬行業: {sector} - {industry}

### 實時行情
- 當前價格: {currency} {price:.2f}
- 漲跌幅: {change_pct:+.2f}%
- 成交量: {volume:,}
- 市值: {market_cap_display}
- 52週區間: {fifty_two_low:.2f} - {fifty_two_high:.2f}

### 關鍵財務指標
- 本益比 (PE): {pe:.2f}
- 股價淨值比 (PB): {pb:.2f}
- 股東權益報酬率 (ROE): {roe:.2f}%
- 利潤率: {profit_margin:.2f}%
- 負債權益比: {debt_to_equity:.2f}
- 股息率: {dividend_yield:.2f}%
- Beta: {beta:.2f}

### 近期新聞
{news_text}

---

請嚴格按照以下結構組織報告：

## 📈 即時快照
簡述當前股價表現、關鍵變化、市場情緒。（2-3句話）

## 📊 財務深度解析
分析估值水平、盈利能力、財務健康度。指出亮點和風險。

## 📰 近期動態整合
總結新聞要點，分析其對股價的潛在影響。

## 🔮 未來展望與風險評估
列出 2-3 個上行驅動因素和下行風險。

## 💎 核心結論
用 3 個要點總結投資價值判斷。

注意：語言精煉專業，數據需標明來源，避免模糊表述。"""

    def __init__(self):
        """初始化報告引擎"""
        self.client = None
        if settings.AI_API_KEY:
            self.client = OpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL
            )
    
    def generate_report(
        self,
        quote: Dict[str, Any],
        indicators: Dict[str, Any],
        profile: Dict[str, Any],
        news: list
    ) -> str:
        """
        生成完整的股票分析報告
        
        Args:
            quote: 實時報價數據
            indicators: 財務指標
            profile: 公司簡介
            news: 新聞列表
        
        Returns:
            Markdown 格式的分析報告
        """
        if not self.client:
            return self._generate_basic_report(quote, indicators, profile, news)
        
        try:
            # 格式化新聞
            news_text = self._format_news(news)
            
            # 格式化市值
            market_cap = quote.get('market_cap', 0) or 0
            if market_cap >= 1e12:
                market_cap_display = f"{market_cap/1e12:.2f}兆"
            elif market_cap >= 1e9:
                market_cap_display = f"{market_cap/1e9:.2f}億"
            elif market_cap >= 1e6:
                market_cap_display = f"{market_cap/1e6:.2f}百萬"
            else:
                market_cap_display = f"{market_cap:,.0f}"
            
            # 填充模板
            prompt = self.REPORT_TEMPLATE.format(
                symbol=quote.get('symbol', ''),
                name=quote.get('name', ''),
                sector=profile.get('sector', 'N/A'),
                industry=profile.get('industry', 'N/A'),
                currency=quote.get('currency', 'USD'),
                price=quote.get('current_price', 0) or 0,
                change_pct=quote.get('change_percent', 0) or 0,
                volume=quote.get('volume', 0) or 0,
                market_cap_display=market_cap_display,
                fifty_two_low=quote.get('fifty_two_week_low', 0) or 0,
                fifty_two_high=quote.get('fifty_two_week_high', 0) or 0,
                pe=indicators.get('pe_ratio', 0) or 0,
                pb=indicators.get('pb_ratio', 0) or 0,
                roe=(indicators.get('roe', 0) or 0) * 100,
                profit_margin=(indicators.get('profit_margin', 0) or 0) * 100,
                debt_to_equity=indicators.get('debt_to_equity', 0) or 0,
                dividend_yield=(indicators.get('dividend_yield', 0) or 0) * 100,
                beta=indicators.get('beta', 0) or 0,
                news_text=news_text
            )
            
            # 調用 AI API
            response = self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            
            # 添加標題
            header = f"# {quote.get('name', quote.get('symbol', ''))} 投資分析報告\n\n"
            header += f"**代碼**: {quote.get('symbol', '')} | "
            header += f"**價格**: {quote.get('currency', 'USD')} {quote.get('current_price', 0):.2f} "
            header += f"({quote.get('change_percent', 0):+.2f}%)\n\n"
            header += "---\n\n"
            
            return header + report
            
        except Exception as e:
            logger.error(f"AI 報告生成失敗: {e}")
            return self._generate_basic_report(quote, indicators, profile, news)
    
    def _format_news(self, news: list) -> str:
        """格式化新聞列表"""
        if not news:
            return "暫無近期新聞"
        
        lines = []
        for i, item in enumerate(news[:5], 1):
            title = item.get('title', '')
            publisher = item.get('publisher', '')
            if title:
                lines.append(f"{i}. {title} ({publisher})")
        
        return "\n".join(lines) if lines else "暫無近期新聞"
    
    def _generate_basic_report(
        self,
        quote: Dict[str, Any],
        indicators: Dict[str, Any],
        profile: Dict[str, Any],
        news: list
    ) -> str:
        """
        生成基本報告（無 AI 時使用）
        """
        symbol = quote.get('symbol', '')
        name = quote.get('name', symbol)
        price = quote.get('current_price', 0) or 0
        change_pct = quote.get('change_percent', 0) or 0
        
        # 格式化市值
        market_cap = quote.get('market_cap', 0) or 0
        if market_cap >= 1e12:
            market_cap_display = f"{market_cap/1e12:.2f}兆"
        elif market_cap >= 1e9:
            market_cap_display = f"{market_cap/1e9:.2f}億"
        else:
            market_cap_display = f"{market_cap:,.0f}"
        
        report = f"""# {name} 股票報告

## 📈 即時行情
- **代碼**: {symbol}
- **價格**: {quote.get('currency', 'USD')} {price:.2f}
- **漲跌**: {change_pct:+.2f}%
- **成交量**: {quote.get('volume', 0):,}
- **市值**: {market_cap_display}

## 📊 關鍵指標
| 指標 | 數值 |
|------|------|
| PE (本益比) | {indicators.get('pe_ratio', 0) or 0:.2f} |
| PB (股價淨值比) | {indicators.get('pb_ratio', 0) or 0:.2f} |
| ROE | {(indicators.get('roe', 0) or 0) * 100:.2f}% |
| 利潤率 | {(indicators.get('profit_margin', 0) or 0) * 100:.2f}% |
| 股息率 | {(indicators.get('dividend_yield', 0) or 0) * 100:.2f}% |
| Beta | {indicators.get('beta', 0) or 0:.2f} |

## 📰 近期新聞
"""
        
        if news:
            for item in news[:5]:
                title = item.get('title', '')
                if title:
                    report += f"- {title}\n"
        else:
            report += "暫無近期新聞\n"
        
        report += "\n---\n*報告生成時間: 即時*"
        
        return report
