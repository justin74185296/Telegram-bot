"""
财务分析模块
处理和分析财务数据，计算各种财务指标和趋势
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

from .data_provider import StockQuote, FinancialData, KeyIndicators

logger = logging.getLogger(__name__)


@dataclass
class FinancialTrend:
    """财务趋势分析结果"""
    metric_name: str
    values: List[float]
    periods: List[str]
    trend: str  # "上升", "下降", "稳定"
    change_rate: float  # 总变化率


@dataclass
class AnalysisResult:
    """综合分析结果"""
    symbol: str
    profitability_score: float  # 盈利能力评分 0-100
    growth_score: float  # 成长性评分 0-100
    safety_score: float  # 财务安全评分 0-100
    valuation_level: str  # "低估", "合理", "高估"
    key_strengths: List[str]
    key_risks: List[str]
    trends: List[FinancialTrend]


class FinancialAnalyzer:
    """
    财务分析器
    对股票财务数据进行深度分析，生成结构化的分析结果
    """
    
    def __init__(self):
        """初始化财务分析器"""
        logger.info("FinancialAnalyzer 初始化完成")
    
    def analyze_profitability(self, indicators: KeyIndicators) -> Tuple[float, List[str]]:
        """
        分析盈利能力
        
        Args:
            indicators: 关键指标数据
            
        Returns:
            (评分, 分析要点列表)
        """
        score = 50.0  # 基础分
        insights = []
        
        # ROE 分析 (15% 以上优秀)
        if indicators.roe is not None:
            roe_pct = indicators.roe * 100 if indicators.roe < 1 else indicators.roe
            if roe_pct > 20:
                score += 20
                insights.append(f"ROE {roe_pct:.1f}% 表现优异，资本回报率高")
            elif roe_pct > 15:
                score += 10
                insights.append(f"ROE {roe_pct:.1f}% 良好")
            elif roe_pct > 10:
                score += 5
                insights.append(f"ROE {roe_pct:.1f}% 处于中等水平")
            elif roe_pct > 0:
                insights.append(f"ROE {roe_pct:.1f}% 偏低，盈利能力有待提升")
            else:
                score -= 10
                insights.append(f"ROE {roe_pct:.1f}% 为负，盈利能力较差")
        
        # 利润率分析
        if indicators.profit_margin is not None:
            margin_pct = indicators.profit_margin * 100 if indicators.profit_margin < 1 else indicators.profit_margin
            if margin_pct > 20:
                score += 15
                insights.append(f"净利润率 {margin_pct:.1f}% 较高，盈利质量好")
            elif margin_pct > 10:
                score += 5
                insights.append(f"净利润率 {margin_pct:.1f}% 处于健康水平")
            elif margin_pct > 0:
                insights.append(f"净利润率 {margin_pct:.1f}% 偏薄")
            else:
                score -= 10
                insights.append(f"净利润率为负，处于亏损状态")
        
        # 营业利润率
        if indicators.operating_margin is not None:
            op_margin = indicators.operating_margin * 100 if indicators.operating_margin < 1 else indicators.operating_margin
            if op_margin > 25:
                score += 10
                insights.append(f"营业利润率 {op_margin:.1f}% 优秀，经营效率高")
            elif op_margin > 15:
                score += 5
        
        return min(max(score, 0), 100), insights
    
    def analyze_growth(self, indicators: KeyIndicators) -> Tuple[float, List[str]]:
        """
        分析成长性
        
        Args:
            indicators: 关键指标数据
            
        Returns:
            (评分, 分析要点列表)
        """
        score = 50.0
        insights = []
        
        # 营收增长
        if indicators.revenue_growth is not None:
            growth_pct = indicators.revenue_growth * 100 if abs(indicators.revenue_growth) < 5 else indicators.revenue_growth
            if growth_pct > 30:
                score += 25
                insights.append(f"营收增长 {growth_pct:.1f}% 高速成长")
            elif growth_pct > 15:
                score += 15
                insights.append(f"营收增长 {growth_pct:.1f}% 稳健增长")
            elif growth_pct > 5:
                score += 5
                insights.append(f"营收增长 {growth_pct:.1f}% 温和增长")
            elif growth_pct > 0:
                insights.append(f"营收增长 {growth_pct:.1f}% 增速放缓")
            else:
                score -= 15
                insights.append(f"营收下滑 {growth_pct:.1f}%，需关注")
        
        # 盈利增长
        if indicators.earnings_growth is not None:
            eg_pct = indicators.earnings_growth * 100 if abs(indicators.earnings_growth) < 5 else indicators.earnings_growth
            if eg_pct > 30:
                score += 20
                insights.append(f"盈利增长 {eg_pct:.1f}% 势头强劲")
            elif eg_pct > 15:
                score += 10
                insights.append(f"盈利增长 {eg_pct:.1f}% 表现良好")
            elif eg_pct > 0:
                score += 5
            elif eg_pct > -20:
                score -= 5
                insights.append(f"盈利下滑 {eg_pct:.1f}%")
            else:
                score -= 15
                insights.append(f"盈利大幅下滑 {eg_pct:.1f}%，需警惕")
        
        return min(max(score, 0), 100), insights
    
    def analyze_safety(self, indicators: KeyIndicators) -> Tuple[float, List[str]]:
        """
        分析财务安全性
        
        Args:
            indicators: 关键指标数据
            
        Returns:
            (评分, 分析要点列表)
        """
        score = 60.0
        insights = []
        
        # 负债率分析
        if indicators.debt_to_equity is not None:
            de_ratio = indicators.debt_to_equity
            if de_ratio < 0.5:
                score += 20
                insights.append(f"负债权益比 {de_ratio:.2f} 很低，财务稳健")
            elif de_ratio < 1.0:
                score += 10
                insights.append(f"负债权益比 {de_ratio:.2f} 处于合理水平")
            elif de_ratio < 2.0:
                insights.append(f"负债权益比 {de_ratio:.2f} 中等")
            else:
                score -= 20
                insights.append(f"负债权益比 {de_ratio:.2f} 较高，存在财务风险")
        
        # 流动比率
        if indicators.current_ratio is not None:
            cr = indicators.current_ratio
            if cr > 2.0:
                score += 15
                insights.append(f"流动比率 {cr:.2f} 健康，短期偿债能力强")
            elif cr > 1.5:
                score += 10
                insights.append(f"流动比率 {cr:.2f} 良好")
            elif cr > 1.0:
                score += 5
                insights.append(f"流动比率 {cr:.2f} 尚可")
            else:
                score -= 15
                insights.append(f"流动比率 {cr:.2f} 偏低，短期偿债压力大")
        
        # Beta 风险
        if indicators.beta is not None:
            beta = indicators.beta
            if beta < 0.8:
                score += 5
                insights.append(f"Beta {beta:.2f} 低波动，防御性强")
            elif beta > 1.5:
                score -= 10
                insights.append(f"Beta {beta:.2f} 高波动，风险较大")
        
        return min(max(score, 0), 100), insights
    
    def analyze_valuation(self, indicators: KeyIndicators, quote: Optional[StockQuote] = None) -> Tuple[str, List[str]]:
        """
        分析估值水平
        
        Args:
            indicators: 关键指标数据
            quote: 实时报价数据
            
        Returns:
            (估值评级, 分析要点列表)
        """
        insights = []
        scores = []  # 用于综合判断
        
        # PE 分析
        if indicators.pe_ratio is not None:
            pe = indicators.pe_ratio
            if pe < 0:
                insights.append(f"市盈率 {pe:.1f} (亏损状态)")
            elif pe < 15:
                scores.append(-1)  # 低估
                insights.append(f"市盈率 {pe:.1f} 较低")
            elif pe < 25:
                scores.append(0)  # 合理
                insights.append(f"市盈率 {pe:.1f} 处于合理区间")
            elif pe < 40:
                scores.append(1)  # 偏高
                insights.append(f"市盈率 {pe:.1f} 偏高")
            else:
                scores.append(2)  # 高估
                insights.append(f"市盈率 {pe:.1f} 较高，估值承压")
        
        # PB 分析
        if indicators.pb_ratio is not None:
            pb = indicators.pb_ratio
            if pb < 1:
                scores.append(-1)
                insights.append(f"市净率 {pb:.2f} 破净，可能被低估")
            elif pb < 3:
                scores.append(0)
                insights.append(f"市净率 {pb:.2f} 合理")
            elif pb < 5:
                scores.append(1)
                insights.append(f"市净率 {pb:.2f} 偏高")
            else:
                scores.append(2)
                insights.append(f"市净率 {pb:.2f} 较高")
        
        # PS 分析
        if indicators.ps_ratio is not None:
            ps = indicators.ps_ratio
            if ps < 2:
                scores.append(-1)
                insights.append(f"市销率 {ps:.2f} 较低")
            elif ps < 5:
                scores.append(0)
            elif ps < 10:
                scores.append(1)
                insights.append(f"市销率 {ps:.2f} 偏高")
            else:
                scores.append(2)
                insights.append(f"市销率 {ps:.2f} 很高")
        
        # 综合判断
        if not scores:
            return "数据不足", insights
        
        avg_score = sum(scores) / len(scores)
        if avg_score < -0.5:
            return "可能低估", insights
        elif avg_score < 0.5:
            return "估值合理", insights
        elif avg_score < 1.5:
            return "估值偏高", insights
        else:
            return "明显高估", insights
    
    def extract_financial_trends(self, financials: FinancialData) -> List[FinancialTrend]:
        """
        从财务报表中提取趋势数据
        
        Args:
            financials: 财务数据
            
        Returns:
            FinancialTrend 列表
        """
        trends = []
        
        # 分析利润表趋势
        if financials.income_statement is not None and not financials.income_statement.empty:
            income = financials.income_statement
            
            # 营收趋势
            if 'Total Revenue' in income.index:
                revenue_row = income.loc['Total Revenue']
                trend = self._analyze_trend('总营收', revenue_row)
                if trend:
                    trends.append(trend)
            
            # 净利润趋势
            if 'Net Income' in income.index:
                net_income_row = income.loc['Net Income']
                trend = self._analyze_trend('净利润', net_income_row)
                if trend:
                    trends.append(trend)
            
            # 毛利趋势
            if 'Gross Profit' in income.index:
                gross_profit_row = income.loc['Gross Profit']
                trend = self._analyze_trend('毛利润', gross_profit_row)
                if trend:
                    trends.append(trend)
        
        # 分析现金流趋势
        if financials.cash_flow is not None and not financials.cash_flow.empty:
            cf = financials.cash_flow
            
            if 'Operating Cash Flow' in cf.index:
                ocf_row = cf.loc['Operating Cash Flow']
                trend = self._analyze_trend('经营现金流', ocf_row)
                if trend:
                    trends.append(trend)
            
            if 'Free Cash Flow' in cf.index:
                fcf_row = cf.loc['Free Cash Flow']
                trend = self._analyze_trend('自由现金流', fcf_row)
                if trend:
                    trends.append(trend)
        
        return trends
    
    def _analyze_trend(self, metric_name: str, data: pd.Series) -> Optional[FinancialTrend]:
        """
        分析单个指标的趋势
        
        Args:
            metric_name: 指标名称
            data: 数据序列
            
        Returns:
            FinancialTrend 或 None
        """
        try:
            # 清理数据
            values = data.dropna().values[:4]  # 最近4个季度
            if len(values) < 2:
                return None
            
            # 转换为浮点数
            values = [float(v) for v in values]
            
            # 获取时期标签
            periods = [str(col)[:10] for col in data.dropna().index[:4]]
            
            # 计算变化率
            if values[-1] != 0:
                change_rate = ((values[0] - values[-1]) / abs(values[-1])) * 100
            else:
                change_rate = 0
            
            # 判断趋势
            if len(values) >= 3:
                # 简单线性趋势判断
                increasing = sum(1 for i in range(len(values)-1) if values[i] > values[i+1])
                if increasing >= len(values) - 1:
                    trend = "上升"
                elif increasing <= 1:
                    trend = "下降"
                else:
                    trend = "波动"
            else:
                trend = "上升" if values[0] > values[-1] else "下降"
            
            return FinancialTrend(
                metric_name=metric_name,
                values=values,
                periods=periods,
                trend=trend,
                change_rate=change_rate
            )
        except Exception as e:
            logger.warning(f"分析 {metric_name} 趋势时出错: {e}")
            return None
    
    async def generate_full_analysis(
        self,
        quote: StockQuote,
        indicators: KeyIndicators,
        financials: Optional[FinancialData] = None
    ) -> AnalysisResult:
        """
        生成完整的财务分析结果
        
        Args:
            quote: 实时报价
            indicators: 关键指标
            financials: 财务数据（可选）
            
        Returns:
            AnalysisResult 综合分析结果
        """
        logger.info(f"正在为 {quote.symbol} 生成完整财务分析...")
        
        # 各维度分析
        profit_score, profit_insights = self.analyze_profitability(indicators)
        growth_score, growth_insights = self.analyze_growth(indicators)
        safety_score, safety_insights = self.analyze_safety(indicators)
        valuation, valuation_insights = self.analyze_valuation(indicators, quote)
        
        # 提取趋势
        trends = []
        if financials:
            trends = self.extract_financial_trends(financials)
        
        # 整合优势和风险
        all_insights = profit_insights + growth_insights + safety_insights + valuation_insights
        strengths = [i for i in all_insights if any(word in i for word in ['优', '良好', '健康', '强', '高速', '稳健'])]
        risks = [i for i in all_insights if any(word in i for word in ['低', '下滑', '风险', '亏损', '压力', '警惕', '偏高'])]
        
        result = AnalysisResult(
            symbol=quote.symbol,
            profitability_score=profit_score,
            growth_score=growth_score,
            safety_score=safety_score,
            valuation_level=valuation,
            key_strengths=strengths[:5],  # 最多5条
            key_risks=risks[:5],
            trends=trends
        )
        
        logger.info(f"{quote.symbol} 分析完成: 盈利{profit_score:.0f} 成长{growth_score:.0f} 安全{safety_score:.0f} 估值:{valuation}")
        
        return result
