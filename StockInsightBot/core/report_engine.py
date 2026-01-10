# -*- coding: utf-8 -*-
"""
AI报告生成引擎
使用大语言模型生成专业的股票分析报告
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI

from config import settings
from .data_provider import StockQuote, FinancialData, KeyIndicators, NewsItem
from .financial_analyzer import AnalysisResult


class StockReportEngine:
    """
    股票分析报告生成引擎
    
    核心功能:
    - 整合多源数据构建分析上下文
    - 使用精心设计的提示词模板
    - 调用GPT-4/4o生成专业报告
    - 支持报告分段以适应Telegram消息长度限制
    """
    
    # ========================================
    # 系统角色设定提示词
    # ========================================
    SYSTEM_PROMPT = """你是一名严谨的买方投资分析师，拥有超过15年的证券研究经验。

你的专业特点：
1. 擅长从海量信息中提炼关键洞察
2. 注重数据驱动，每个结论都有数据支撑
3. 表达精炼专业，避免模糊表述
4. 能够识别财务数据中的异常信号
5. 善于将复杂概念用简洁语言解释

你的分析原则：
- 客观中立，不过度乐观或悲观
- 明确区分事实与推测
- 风险与机会并重
- 引用具体数据时注明来源或时间点"""

    # ========================================
    # 报告结构模板提示词
    # ========================================
    REPORT_TEMPLATE = """请根据以下数据，生成一份专业的股票分析报告。

## 待分析股票信息
{stock_data}

## 报告要求

请严格按照以下结构组织报告，使用Markdown格式：

### 📈 即时快照
- 当前股价及今日涨跌情况
- 相对于52周高低点的位置
- 当前市场情绪简述（根据成交量、涨跌幅判断）

### 📊 财务深度解析
- 使用表格呈现近几个季度的关键财务指标趋势
- 分析盈利质量（利润率变化、ROE水平）
- 评估成长性（营收/利润增速）
- 判断财务健康度（负债水平、现金流状况）

### 📰 近期动态集成
- 总结近期重要新闻要点
- 分析这些事件对公司的潜在影响
- 如果没有新闻，说明"近期无重大公开披露"

### 🔮 未来展望与风险评估
**上行驱动因素**（2-3个）：
- 基于数据和行业逻辑列出可能推动股价上涨的因素

**下行风险因素**（2-3个）：
- 基于数据和行业逻辑列出需要警惕的风险点

### 💎 核心结论
用3个要点总结你对这只股票的核心看法，每个要点需简洁有力。

## 输出格式要求
1. 使用Markdown格式
2. 数据需注明时间点或来源
3. 语言精炼专业
4. 表格使用Markdown表格语法
5. 总字数控制在800-1200字"""

    def __init__(self):
        """初始化报告引擎，配置OpenAI客户端"""
        # 配置OpenAI客户端
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_api_base:
            client_kwargs["base_url"] = settings.openai_api_base
        
        self.client = AsyncOpenAI(**client_kwargs)
        self.model = settings.openai_model
    
    async def generate_report(
        self,
        quote: Optional[StockQuote],
        financials: Optional[FinancialData],
        indicators: Optional[KeyIndicators],
        news: List[NewsItem],
        analysis: Optional[AnalysisResult]
    ) -> str:
        """
        生成完整的股票分析报告
        
        参数:
            quote: 实时报价数据
            financials: 财务报表数据
            indicators: 关键财务指标
            news: 新闻列表
            analysis: 财务分析结果
        返回:
            Markdown格式的分析报告
        """
        # 构建数据上下文
        stock_data = self._build_data_context(
            quote, financials, indicators, news, analysis
        )
        
        # 构建完整的用户提示词
        user_prompt = self.REPORT_TEMPLATE.format(stock_data=stock_data)
        
        try:
            # 调用OpenAI API生成报告
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # 适度的创造性
                max_tokens=2000,  # 控制输出长度
                top_p=0.9
            )
            
            report = response.choices[0].message.content
            
            # 添加报告头部信息
            header = self._generate_report_header(quote)
            
            return f"{header}\n\n{report}"
            
        except Exception as e:
            # 生成失败时返回错误报告
            return self._generate_error_report(quote, str(e))
    
    def _build_data_context(
        self,
        quote: Optional[StockQuote],
        financials: Optional[FinancialData],
        indicators: Optional[KeyIndicators],
        news: List[NewsItem],
        analysis: Optional[AnalysisResult]
    ) -> str:
        """
        构建提供给AI的数据上下文
        
        将各类数据整合为结构化的文本描述
        """
        sections = []
        
        # 1. 实时行情数据
        if quote:
            quote_section = f"""
### 实时行情（数据时间：{quote.timestamp.strftime('%Y-%m-%d %H:%M')}）
- **股票代码**：{quote.symbol}
- **公司名称**：{quote.name}
- **当前价格**：{quote.currency} {quote.current_price:.2f}
- **今日涨跌**：{quote.change:+.2f} ({quote.change_percent:+.2f}%)
- **今日区间**：{quote.day_low:.2f} - {quote.day_high:.2f}
- **开盘价**：{quote.open_price:.2f}
- **昨收价**：{quote.previous_close:.2f}
- **成交量**：{self._format_volume(quote.volume)}
- **平均成交量**：{self._format_volume(quote.avg_volume) if quote.avg_volume else 'N/A'}"""
            
            if quote.market_cap:
                quote_section += f"\n- **总市值**：{self._format_market_cap(quote.market_cap)}"
            if quote.fifty_two_week_high and quote.fifty_two_week_low:
                quote_section += f"\n- **52周区间**：{quote.fifty_two_week_low:.2f} - {quote.fifty_two_week_high:.2f}"
            
            sections.append(quote_section)
        
        # 2. 关键财务指标
        if indicators:
            indicators_section = """
### 关键财务指标"""
            indicator_items = []
            
            if indicators.pe_ratio is not None:
                indicator_items.append(f"- **市盈率(TTM)**：{indicators.pe_ratio:.2f}")
            if indicators.forward_pe is not None:
                indicator_items.append(f"- **预期市盈率**：{indicators.forward_pe:.2f}")
            if indicators.pb_ratio is not None:
                indicator_items.append(f"- **市净率**：{indicators.pb_ratio:.2f}")
            if indicators.ps_ratio is not None:
                indicator_items.append(f"- **市销率**：{indicators.ps_ratio:.2f}")
            if indicators.peg_ratio is not None:
                indicator_items.append(f"- **PEG比率**：{indicators.peg_ratio:.2f}")
            if indicators.roe is not None:
                roe_pct = indicators.roe * 100 if indicators.roe < 1 else indicators.roe
                indicator_items.append(f"- **ROE**：{roe_pct:.2f}%")
            if indicators.roa is not None:
                roa_pct = indicators.roa * 100 if indicators.roa < 1 else indicators.roa
                indicator_items.append(f"- **ROA**：{roa_pct:.2f}%")
            if indicators.profit_margin is not None:
                margin_pct = indicators.profit_margin * 100 if indicators.profit_margin < 1 else indicators.profit_margin
                indicator_items.append(f"- **净利润率**：{margin_pct:.2f}%")
            if indicators.gross_margin is not None:
                gross_pct = indicators.gross_margin * 100 if indicators.gross_margin < 1 else indicators.gross_margin
                indicator_items.append(f"- **毛利率**：{gross_pct:.2f}%")
            if indicators.debt_to_equity is not None:
                indicator_items.append(f"- **负债权益比**：{indicators.debt_to_equity:.2f}")
            if indicators.current_ratio is not None:
                indicator_items.append(f"- **流动比率**：{indicators.current_ratio:.2f}")
            if indicators.dividend_yield is not None:
                div_pct = indicators.dividend_yield * 100 if indicators.dividend_yield < 1 else indicators.dividend_yield
                indicator_items.append(f"- **股息率**：{div_pct:.2f}%")
            if indicators.beta is not None:
                indicator_items.append(f"- **Beta系数**：{indicators.beta:.2f}")
            if indicators.eps is not None:
                indicator_items.append(f"- **每股收益**：{indicators.eps:.2f}")
            if indicators.revenue_growth is not None:
                rev_growth = indicators.revenue_growth * 100 if abs(indicators.revenue_growth) < 10 else indicators.revenue_growth
                indicator_items.append(f"- **营收增长率**：{rev_growth:+.2f}%")
            if indicators.earnings_growth is not None:
                earn_growth = indicators.earnings_growth * 100 if abs(indicators.earnings_growth) < 10 else indicators.earnings_growth
                indicator_items.append(f"- **盈利增长率**：{earn_growth:+.2f}%")
            
            if indicator_items:
                indicators_section += "\n" + "\n".join(indicator_items)
                sections.append(indicators_section)
        
        # 3. 季度财务数据趋势
        if financials:
            fin_section = self._build_financials_section(financials)
            if fin_section:
                sections.append(fin_section)
        
        # 4. 分析评分摘要
        if analysis:
            analysis_section = """
### 量化分析评分（满分10分）"""
            score_items = []
            
            if analysis.valuation_score is not None:
                score_items.append(f"- **估值评分**：{analysis.valuation_score:.1f}/10 - {analysis.valuation_summary}")
            if analysis.profitability_score is not None:
                score_items.append(f"- **盈利能力**：{analysis.profitability_score:.1f}/10 - {analysis.profitability_summary}")
            if analysis.growth_score is not None:
                score_items.append(f"- **成长性**：{analysis.growth_score:.1f}/10 - {analysis.growth_summary}")
            if analysis.health_score is not None:
                score_items.append(f"- **财务健康**：{analysis.health_score:.1f}/10 - {analysis.health_summary}")
            if analysis.overall_score is not None:
                score_items.append(f"- **综合评分**：{analysis.overall_score:.1f}/10")
            
            if score_items:
                analysis_section += "\n" + "\n".join(score_items)
                sections.append(analysis_section)
        
        # 5. 近期新闻
        if news:
            news_section = """
### 近期新闻动态"""
            for i, item in enumerate(news[:5], 1):
                pub_date = item.published.strftime('%Y-%m-%d') if item.published else '未知日期'
                news_section += f"\n{i}. **{item.title}**"
                news_section += f"\n   - 来源：{item.source or '未知'} | 时间：{pub_date}"
                if item.summary:
                    summary = item.summary[:150] + "..." if len(item.summary) > 150 else item.summary
                    news_section += f"\n   - 摘要：{summary}"
            sections.append(news_section)
        else:
            sections.append("\n### 近期新闻动态\n近期无相关新闻披露。")
        
        return "\n".join(sections)
    
    def _build_financials_section(self, financials: FinancialData) -> str:
        """
        构建财务数据表格部分
        """
        lines = ["\n### 季度财务数据趋势"]
        
        # 检查是否有足够数据构建表格
        has_revenue = bool(financials.revenue)
        has_income = bool(financials.net_income)
        has_cash_flow = bool(financials.operating_cash_flow)
        
        if not (has_revenue or has_income or has_cash_flow):
            return ""
        
        # 构建利润表数据表格
        if has_revenue or has_income:
            lines.append("\n**利润表数据（单位：百万）**")
            
            # 获取所有日期
            dates = []
            if financials.revenue:
                dates = [item['date'] for item in financials.revenue[:4]]
            elif financials.net_income:
                dates = [item['date'] for item in financials.net_income[:4]]
            
            if dates:
                header = "| 指标 | " + " | ".join(dates) + " |"
                separator = "|---" + "|---" * len(dates) + "|"
                lines.append(header)
                lines.append(separator)
                
                # 营收行
                if financials.revenue:
                    values = [self._format_millions(item.get('value')) for item in financials.revenue[:4]]
                    lines.append("| 营业收入 | " + " | ".join(values) + " |")
                
                # 毛利行
                if financials.gross_profit:
                    values = [self._format_millions(item.get('value')) for item in financials.gross_profit[:4]]
                    lines.append("| 毛利润 | " + " | ".join(values) + " |")
                
                # 营业利润行
                if financials.operating_income:
                    values = [self._format_millions(item.get('value')) for item in financials.operating_income[:4]]
                    lines.append("| 营业利润 | " + " | ".join(values) + " |")
                
                # 净利润行
                if financials.net_income:
                    values = [self._format_millions(item.get('value')) for item in financials.net_income[:4]]
                    lines.append("| 净利润 | " + " | ".join(values) + " |")
        
        # 构建资产负债表关键数据
        if financials.total_assets or financials.cash_and_equivalents:
            lines.append("\n**资产负债关键数据（单位：百万）**")
            
            dates = []
            if financials.total_assets:
                dates = [item['date'] for item in financials.total_assets[:4]]
            
            if dates:
                header = "| 指标 | " + " | ".join(dates) + " |"
                separator = "|---" + "|---" * len(dates) + "|"
                lines.append(header)
                lines.append(separator)
                
                if financials.total_assets:
                    values = [self._format_millions(item.get('value')) for item in financials.total_assets[:4]]
                    lines.append("| 总资产 | " + " | ".join(values) + " |")
                
                if financials.total_liabilities:
                    values = [self._format_millions(item.get('value')) for item in financials.total_liabilities[:4]]
                    lines.append("| 总负债 | " + " | ".join(values) + " |")
                
                if financials.total_equity:
                    values = [self._format_millions(item.get('value')) for item in financials.total_equity[:4]]
                    lines.append("| 股东权益 | " + " | ".join(values) + " |")
                
                if financials.cash_and_equivalents:
                    values = [self._format_millions(item.get('value')) for item in financials.cash_and_equivalents[:4]]
                    lines.append("| 现金及等价物 | " + " | ".join(values) + " |")
        
        # 构建现金流数据
        if has_cash_flow:
            lines.append("\n**现金流量数据（单位：百万）**")
            
            dates = [item['date'] for item in financials.operating_cash_flow[:4]]
            
            if dates:
                header = "| 指标 | " + " | ".join(dates) + " |"
                separator = "|---" + "|---" * len(dates) + "|"
                lines.append(header)
                lines.append(separator)
                
                if financials.operating_cash_flow:
                    values = [self._format_millions(item.get('value')) for item in financials.operating_cash_flow[:4]]
                    lines.append("| 经营现金流 | " + " | ".join(values) + " |")
                
                if financials.free_cash_flow:
                    values = [self._format_millions(item.get('value')) for item in financials.free_cash_flow[:4]]
                    lines.append("| 自由现金流 | " + " | ".join(values) + " |")
        
        return "\n".join(lines)
    
    def _generate_report_header(self, quote: Optional[StockQuote]) -> str:
        """
        生成报告头部
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if quote:
            # 根据涨跌添加emoji
            if quote.change_percent > 2:
                emoji = "🚀"
            elif quote.change_percent > 0:
                emoji = "📈"
            elif quote.change_percent < -2:
                emoji = "📉"
            elif quote.change_percent < 0:
                emoji = "🔻"
            else:
                emoji = "➡️"
            
            return f"""# {emoji} {quote.name} ({quote.symbol}) 深度分析报告

> 📅 报告生成时间：{timestamp}
> 💰 当前价格：{quote.currency} {quote.current_price:.2f} ({quote.change_percent:+.2f}%)

---"""
        else:
            return f"""# 📊 股票深度分析报告

> 📅 报告生成时间：{timestamp}

---"""
    
    def _generate_error_report(self, quote: Optional[StockQuote], error: str) -> str:
        """
        生成错误报告
        """
        symbol = quote.symbol if quote else "未知"
        return f"""# ⚠️ 报告生成失败

**股票代码**：{symbol}

**错误信息**：{error}

**建议操作**：
1. 请检查股票代码是否正确
2. 稍后重试
3. 如问题持续，请联系管理员

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*"""
    
    @staticmethod
    def _format_volume(volume: Optional[int]) -> str:
        """格式化成交量显示"""
        if volume is None:
            return "N/A"
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.2f}B"
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.2f}K"
        return str(volume)
    
    @staticmethod
    def _format_market_cap(market_cap: float) -> str:
        """格式化市值显示"""
        if market_cap >= 1_000_000_000_000:
            return f"${market_cap / 1_000_000_000_000:.2f}T"
        if market_cap >= 1_000_000_000:
            return f"${market_cap / 1_000_000_000:.2f}B"
        if market_cap >= 1_000_000:
            return f"${market_cap / 1_000_000:.2f}M"
        return f"${market_cap:,.0f}"
    
    @staticmethod
    def _format_millions(value) -> str:
        """将数值格式化为百万单位"""
        if value is None:
            return "N/A"
        try:
            val = float(value)
            millions = val / 1_000_000
            if abs(millions) >= 1000:
                return f"{millions / 1000:,.1f}B"
            return f"{millions:,.1f}M"
        except (ValueError, TypeError):
            return "N/A"
    
    def split_report(self, report: str, max_length: int = None) -> List[str]:
        """
        将长报告分割为多个消息
        
        参数:
            report: 完整报告文本
            max_length: 单条消息最大长度，默认使用配置值
        返回:
            分割后的消息列表
        """
        if max_length is None:
            max_length = settings.max_message_length
        
        if len(report) <= max_length:
            return [report]
        
        messages = []
        current = ""
        
        # 按段落分割
        paragraphs = report.split("\n\n")
        
        for para in paragraphs:
            # 如果单个段落就超长，需要进一步分割
            if len(para) > max_length:
                # 先保存当前累积的内容
                if current:
                    messages.append(current.strip())
                    current = ""
                
                # 按行分割超长段落
                lines = para.split("\n")
                for line in lines:
                    if len(current) + len(line) + 1 > max_length:
                        if current:
                            messages.append(current.strip())
                        current = line + "\n"
                    else:
                        current += line + "\n"
            else:
                # 检查是否会超长
                if len(current) + len(para) + 2 > max_length:
                    messages.append(current.strip())
                    current = para + "\n\n"
                else:
                    current += para + "\n\n"
        
        # 添加最后一部分
        if current.strip():
            messages.append(current.strip())
        
        # 添加分页标识
        total = len(messages)
        if total > 1:
            messages = [
                f"{msg}\n\n`[{i+1}/{total}]`"
                for i, msg in enumerate(messages)
            ]
        
        return messages
