"""
AI报告生成引擎
使用大语言模型生成专业的股票分析报告
包含精心设计的提示词模板
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from openai import AsyncOpenAI

from config.settings import settings
from .data_provider import StockQuote, FinancialData, KeyIndicators, NewsItem
from .financial_analyzer import AnalysisResult, FinancialTrend

logger = logging.getLogger(__name__)


class StockReportEngine:
    """
    股票分析报告生成引擎
    整合所有数据，调用AI生成专业分析报告
    """
    
    # 系统角色设定
    SYSTEM_PROMPT = """你是一名严谨的买方投资分析师，擅长从海量信息中提炼关键洞察。

你的分析风格：
- 数据驱动：每个观点都要有数据支撑
- 逻辑清晰：分析要有因果关系
- 客观中立：不过度乐观或悲观
- 实用导向：给出可操作的信息

你必须使用中文回复，并使用Markdown格式组织报告。"""

    # 报告生成提示词模板
    REPORT_TEMPLATE = """请基于以下数据，为 {symbol} ({company_name}) 生成一份专业的投资分析报告。

## 当前市场数据
{quote_data}

## 关键财务指标
{indicators_data}

## 财务趋势（最近季度）
{trends_data}

## 量化分析结果
{analysis_data}

## 近期相关新闻
{news_data}

---

请严格按照以下结构生成报告：

## 📈 即时快照
简要描述当前股价状态、关键变化和市场情绪。包含：
- 当前价格和涨跌情况
- 相对于52周高低点的位置
- 成交量是否异常

## 📊 财务深度解析
分析公司的财务状况，必须包含：
- 使用表格呈现关键指标（PE、PB、ROE等）
- 盈利能力评估（利润率、ROE趋势）
- 成长性分析（营收和利润增长）
- 财务健康度（负债水平、现金流）

## 📰 近期动态整合
总结新闻要点并分析其影响：
- 近期重要事件
- 潜在的催化剂或风险点
- 行业动态关联

## 🔮 未来展望与风险评估
基于数据和行业逻辑，列出：
- **上行驱动因素**（2-3个）
- **下行风险因素**（2-3个）
- 关键观察指标

## 💎 核心结论
用3个要点总结：
1. 投资价值判断
2. 当前估值评估
3. 关注建议

---

要求：
1. 语言精炼专业，避免模糊表述
2. 重要数据需注明来源时间
3. 使用emoji增强可读性
4. 报告长度控制在800-1200字"""

    def __init__(self):
        """初始化报告引擎，配置OpenAI客户端"""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model
        logger.info(f"StockReportEngine 初始化完成，使用模型: {self.model}")
    
    def _format_quote_data(self, quote: StockQuote) -> str:
        """格式化报价数据为文本"""
        change_symbol = "📈" if quote.change >= 0 else "📉"
        
        return f"""- 股票代码: {quote.symbol}
- 公司名称: {quote.name}
- 当前价格: {quote.current_price:.2f} {quote.currency}
- 涨跌幅: {change_symbol} {quote.change:+.2f} ({quote.change_percent:+.2f}%)
- 今日区间: {quote.day_low:.2f} - {quote.day_high:.2f}
- 52周区间: {quote.fifty_two_week_low:.2f} - {quote.fifty_two_week_high:.2f}
- 成交量: {quote.volume:,}
- 市值: {self._format_large_number(quote.market_cap)} {quote.currency}
- 交易所: {quote.exchange}
- 数据时间: {quote.timestamp.strftime('%Y-%m-%d %H:%M')}"""
    
    def _format_indicators_data(self, indicators: KeyIndicators) -> str:
        """格式化关键指标数据"""
        lines = []
        
        if indicators.pe_ratio is not None:
            lines.append(f"- 市盈率(PE): {indicators.pe_ratio:.2f}")
        if indicators.pb_ratio is not None:
            lines.append(f"- 市净率(PB): {indicators.pb_ratio:.2f}")
        if indicators.ps_ratio is not None:
            lines.append(f"- 市销率(PS): {indicators.ps_ratio:.2f}")
        if indicators.roe is not None:
            roe_pct = indicators.roe * 100 if abs(indicators.roe) < 1 else indicators.roe
            lines.append(f"- 净资产收益率(ROE): {roe_pct:.2f}%")
        if indicators.roa is not None:
            roa_pct = indicators.roa * 100 if abs(indicators.roa) < 1 else indicators.roa
            lines.append(f"- 总资产收益率(ROA): {roa_pct:.2f}%")
        if indicators.profit_margin is not None:
            pm_pct = indicators.profit_margin * 100 if abs(indicators.profit_margin) < 1 else indicators.profit_margin
            lines.append(f"- 净利润率: {pm_pct:.2f}%")
        if indicators.operating_margin is not None:
            om_pct = indicators.operating_margin * 100 if abs(indicators.operating_margin) < 1 else indicators.operating_margin
            lines.append(f"- 营业利润率: {om_pct:.2f}%")
        if indicators.revenue_growth is not None:
            rg_pct = indicators.revenue_growth * 100 if abs(indicators.revenue_growth) < 5 else indicators.revenue_growth
            lines.append(f"- 营收增长率: {rg_pct:.2f}%")
        if indicators.earnings_growth is not None:
            eg_pct = indicators.earnings_growth * 100 if abs(indicators.earnings_growth) < 5 else indicators.earnings_growth
            lines.append(f"- 盈利增长率: {eg_pct:.2f}%")
        if indicators.debt_to_equity is not None:
            lines.append(f"- 负债权益比: {indicators.debt_to_equity:.2f}")
        if indicators.current_ratio is not None:
            lines.append(f"- 流动比率: {indicators.current_ratio:.2f}")
        if indicators.dividend_yield is not None:
            dy_pct = indicators.dividend_yield * 100 if indicators.dividend_yield < 1 else indicators.dividend_yield
            lines.append(f"- 股息收益率: {dy_pct:.2f}%")
        if indicators.beta is not None:
            lines.append(f"- Beta系数: {indicators.beta:.2f}")
        
        return "\n".join(lines) if lines else "暂无指标数据"
    
    def _format_trends_data(self, trends: List[FinancialTrend]) -> str:
        """格式化趋势数据"""
        if not trends:
            return "暂无趋势数据"
        
        lines = []
        for trend in trends:
            values_str = " → ".join([self._format_large_number(v) for v in trend.values[:4]])
            lines.append(f"- {trend.metric_name}: {values_str}")
            lines.append(f"  趋势: {trend.trend} | 变化率: {trend.change_rate:+.1f}%")
        
        return "\n".join(lines)
    
    def _format_analysis_data(self, analysis: AnalysisResult) -> str:
        """格式化量化分析结果"""
        lines = [
            f"- 盈利能力评分: {analysis.profitability_score:.0f}/100",
            f"- 成长性评分: {analysis.growth_score:.0f}/100",
            f"- 财务安全评分: {analysis.safety_score:.0f}/100",
            f"- 估值水平: {analysis.valuation_level}",
            "",
            "核心优势:",
        ]
        
        for strength in analysis.key_strengths[:3]:
            lines.append(f"  ✅ {strength}")
        
        lines.append("")
        lines.append("主要风险:")
        
        for risk in analysis.key_risks[:3]:
            lines.append(f"  ⚠️ {risk}")
        
        return "\n".join(lines)
    
    def _format_news_data(self, news: List[NewsItem]) -> str:
        """格式化新闻数据"""
        if not news:
            return "暂无相关新闻"
        
        lines = []
        for i, item in enumerate(news[:5], 1):
            time_str = item.published_time.strftime('%m-%d') if item.published_time else "未知"
            lines.append(f"{i}. [{time_str}] {item.title}")
            if item.summary and item.summary != item.title:
                # 截取摘要前100字
                summary = item.summary[:100] + "..." if len(item.summary) > 100 else item.summary
                lines.append(f"   {summary}")
            lines.append(f"   来源: {item.publisher}")
        
        return "\n".join(lines)
    
    def _format_large_number(self, num: float) -> str:
        """将大数字格式化为易读形式"""
        if num is None:
            return "N/A"
        
        abs_num = abs(num)
        sign = "-" if num < 0 else ""
        
        if abs_num >= 1e12:
            return f"{sign}{abs_num/1e12:.2f}万亿"
        elif abs_num >= 1e8:
            return f"{sign}{abs_num/1e8:.2f}亿"
        elif abs_num >= 1e4:
            return f"{sign}{abs_num/1e4:.2f}万"
        else:
            return f"{sign}{abs_num:.2f}"
    
    async def generate_report(
        self,
        quote: StockQuote,
        indicators: KeyIndicators,
        analysis: AnalysisResult,
        news: List[NewsItem],
        trends: List[FinancialTrend] = None
    ) -> str:
        """
        生成完整的股票分析报告
        
        Args:
            quote: 实时报价数据
            indicators: 关键财务指标
            analysis: 量化分析结果
            news: 相关新闻列表
            trends: 财务趋势数据
            
        Returns:
            Markdown格式的分析报告
        """
        logger.info(f"正在为 {quote.symbol} 生成AI分析报告...")
        
        # 准备提示词
        prompt = self.REPORT_TEMPLATE.format(
            symbol=quote.symbol,
            company_name=quote.name,
            quote_data=self._format_quote_data(quote),
            indicators_data=self._format_indicators_data(indicators),
            trends_data=self._format_trends_data(trends or analysis.trends),
            analysis_data=self._format_analysis_data(analysis),
            news_data=self._format_news_data(news)
        )
        
        try:
            # 调用AI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            
            # 添加报告头部
            header = f"""# 📊 {quote.name} ({quote.symbol}) 投资分析报告

> 🕐 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 💹 当前价格: {quote.current_price:.2f} {quote.currency} ({quote.change_percent:+.2f}%)

---

"""
            full_report = header + report
            
            logger.info(f"{quote.symbol} AI报告生成完成，长度: {len(full_report)} 字符")
            return full_report
            
        except Exception as e:
            logger.error(f"AI报告生成失败: {e}")
            # 返回基础报告作为降级方案
            return self._generate_fallback_report(quote, indicators, analysis, news)
    
    def _generate_fallback_report(
        self,
        quote: StockQuote,
        indicators: KeyIndicators,
        analysis: AnalysisResult,
        news: List[NewsItem]
    ) -> str:
        """
        生成降级报告（AI不可用时）
        
        Args:
            各类数据参数
            
        Returns:
            基础格式的分析报告
        """
        logger.warning("使用降级方案生成基础报告")
        
        change_emoji = "📈" if quote.change >= 0 else "📉"
        
        report = f"""# 📊 {quote.name} ({quote.symbol}) 基础分析报告

> 🕐 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> ⚠️ 注意: AI分析暂时不可用，以下为基础数据汇总

---

## 📈 即时快照

| 指标 | 数值 |
|------|------|
| 当前价格 | {quote.current_price:.2f} {quote.currency} |
| 涨跌幅 | {change_emoji} {quote.change_percent:+.2f}% |
| 今日区间 | {quote.day_low:.2f} - {quote.day_high:.2f} |
| 52周区间 | {quote.fifty_two_week_low:.2f} - {quote.fifty_two_week_high:.2f} |
| 成交量 | {quote.volume:,} |
| 市值 | {self._format_large_number(quote.market_cap)} |

## 📊 关键指标

{self._format_indicators_data(indicators)}

## 📈 量化评分

- 🎯 盈利能力: {analysis.profitability_score:.0f}/100
- 📈 成长性: {analysis.growth_score:.0f}/100
- 🛡️ 财务安全: {analysis.safety_score:.0f}/100
- 💰 估值水平: {analysis.valuation_level}

### 核心优势
"""
        for s in analysis.key_strengths[:3]:
            report += f"\n✅ {s}"
        
        report += "\n\n### 主要风险\n"
        for r in analysis.key_risks[:3]:
            report += f"\n⚠️ {r}"
        
        if news:
            report += "\n\n## 📰 近期新闻\n"
            for item in news[:3]:
                report += f"\n- {item.title}"
        
        report += "\n\n---\n*此为基础报告，完整AI分析暂时不可用*"
        
        return report
    
    async def generate_quick_summary(self, quote: StockQuote, indicators: KeyIndicators) -> str:
        """
        生成快速摘要（用于快速查询）
        
        Args:
            quote: 报价数据
            indicators: 关键指标
            
        Returns:
            简短的摘要文本
        """
        change_emoji = "📈" if quote.change >= 0 else "📉"
        
        summary = f"""**{quote.name}** ({quote.symbol})

💰 {quote.current_price:.2f} {quote.currency} {change_emoji} {quote.change_percent:+.2f}%

📊 关键指标:
"""
        if indicators.pe_ratio:
            summary += f"• PE: {indicators.pe_ratio:.1f}\n"
        if indicators.pb_ratio:
            summary += f"• PB: {indicators.pb_ratio:.2f}\n"
        if indicators.roe:
            roe = indicators.roe * 100 if abs(indicators.roe) < 1 else indicators.roe
            summary += f"• ROE: {roe:.1f}%\n"
        
        summary += f"\n📈 市值: {self._format_large_number(quote.market_cap)}"
        
        return summary
