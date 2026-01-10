# -*- coding: utf-8 -*-
"""
财务分析模块
对获取的财务数据进行深度计算和分析处理
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from .data_provider import StockQuote, FinancialData, KeyIndicators


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    symbol: str
    
    # 估值分析
    valuation_score: Optional[float] = None    # 估值评分 (1-10)
    valuation_summary: str = ""                 # 估值总结
    
    # 盈利能力分析
    profitability_score: Optional[float] = None  # 盈利能力评分
    profitability_summary: str = ""
    
    # 成长性分析
    growth_score: Optional[float] = None       # 成长性评分
    growth_summary: str = ""
    
    # 财务健康度分析
    health_score: Optional[float] = None       # 财务健康评分
    health_summary: str = ""
    
    # 综合评分
    overall_score: Optional[float] = None
    
    # 趋势数据（用于图表/表格展示）
    revenue_trend: List[Dict[str, Any]] = field(default_factory=list)
    profit_trend: List[Dict[str, Any]] = field(default_factory=list)
    margin_trend: List[Dict[str, Any]] = field(default_factory=list)


class FinancialAnalyzer:
    """
    财务分析器
    对股票的财务数据进行多维度分析和评分
    """
    
    def __init__(self):
        """初始化分析器"""
        # 估值基准参数（可根据行业调整）
        self.pe_benchmark = 25.0      # PE基准值
        self.pb_benchmark = 3.0       # PB基准值
        self.ps_benchmark = 5.0       # PS基准值
    
    def analyze(
        self,
        quote: Optional[StockQuote],
        financials: Optional[FinancialData],
        indicators: Optional[KeyIndicators]
    ) -> AnalysisResult:
        """
        执行综合财务分析
        
        参数:
            quote: 实时报价数据
            financials: 财务报表数据
            indicators: 关键财务指标
        返回:
            AnalysisResult 分析结果
        """
        symbol = quote.symbol if quote else (financials.symbol if financials else "UNKNOWN")
        result = AnalysisResult(symbol=symbol)
        
        # 执行各维度分析
        if indicators:
            self._analyze_valuation(result, indicators)
            self._analyze_profitability(result, indicators)
            self._analyze_health(result, indicators)
        
        if financials:
            self._analyze_growth(result, financials, indicators)
            self._calculate_trends(result, financials)
        
        # 计算综合评分
        self._calculate_overall_score(result)
        
        return result
    
    def _analyze_valuation(self, result: AnalysisResult, indicators: KeyIndicators):
        """
        估值分析
        
        通过PE、PB、PS、PEG等指标评估股票估值水平
        评分越高表示估值越合理/便宜
        """
        scores = []
        factors = []
        
        # PE分析（市盈率）
        if indicators.pe_ratio is not None and indicators.pe_ratio > 0:
            pe_score = max(0, min(10, (self.pe_benchmark / indicators.pe_ratio) * 5))
            scores.append(pe_score)
            if indicators.pe_ratio < 15:
                factors.append(f"PE={indicators.pe_ratio:.1f}，估值较低")
            elif indicators.pe_ratio > 40:
                factors.append(f"PE={indicators.pe_ratio:.1f}，估值偏高")
            else:
                factors.append(f"PE={indicators.pe_ratio:.1f}，估值适中")
        
        # PB分析（市净率）
        if indicators.pb_ratio is not None and indicators.pb_ratio > 0:
            pb_score = max(0, min(10, (self.pb_benchmark / indicators.pb_ratio) * 5))
            scores.append(pb_score)
            if indicators.pb_ratio < 1:
                factors.append(f"PB={indicators.pb_ratio:.2f}，低于净资产")
            elif indicators.pb_ratio > 5:
                factors.append(f"PB={indicators.pb_ratio:.2f}，溢价较高")
        
        # PEG分析
        if indicators.peg_ratio is not None and indicators.peg_ratio > 0:
            peg_score = max(0, min(10, (1 / indicators.peg_ratio) * 5))
            scores.append(peg_score * 1.2)  # PEG权重略高
            if indicators.peg_ratio < 1:
                factors.append(f"PEG={indicators.peg_ratio:.2f}，成长性价比高")
            elif indicators.peg_ratio > 2:
                factors.append(f"PEG={indicators.peg_ratio:.2f}，相对成长偏贵")
        
        # Forward PE 对比
        if indicators.forward_pe and indicators.pe_ratio:
            if indicators.forward_pe < indicators.pe_ratio * 0.85:
                factors.append("预期PE显著低于当前，市场预期盈利增长")
        
        if scores:
            result.valuation_score = sum(scores) / len(scores)
            result.valuation_summary = "；".join(factors) if factors else "估值数据不足"
        else:
            result.valuation_summary = "估值指标数据不可用"
    
    def _analyze_profitability(self, result: AnalysisResult, indicators: KeyIndicators):
        """
        盈利能力分析
        
        通过ROE、ROA、利润率等指标评估公司盈利质量
        """
        scores = []
        factors = []
        
        # ROE分析（净资产收益率）
        if indicators.roe is not None:
            roe_pct = indicators.roe * 100 if indicators.roe < 1 else indicators.roe
            roe_score = min(10, roe_pct / 2)  # 20%ROE得满分
            scores.append(roe_score)
            if roe_pct > 20:
                factors.append(f"ROE={roe_pct:.1f}%，盈利能力优秀")
            elif roe_pct > 10:
                factors.append(f"ROE={roe_pct:.1f}%，盈利能力良好")
            elif roe_pct > 0:
                factors.append(f"ROE={roe_pct:.1f}%，盈利能力一般")
            else:
                factors.append(f"ROE={roe_pct:.1f}%，处于亏损状态")
        
        # ROA分析（总资产收益率）
        if indicators.roa is not None:
            roa_pct = indicators.roa * 100 if indicators.roa < 1 else indicators.roa
            roa_score = min(10, roa_pct / 1)  # 10%ROA得满分
            scores.append(roa_score)
        
        # 净利润率分析
        if indicators.profit_margin is not None:
            margin_pct = indicators.profit_margin * 100 if indicators.profit_margin < 1 else indicators.profit_margin
            margin_score = min(10, margin_pct / 1.5)  # 15%净利率得满分
            scores.append(margin_score)
            if margin_pct > 15:
                factors.append(f"净利润率{margin_pct:.1f}%，利润空间大")
            elif margin_pct < 5:
                factors.append(f"净利润率{margin_pct:.1f}%，利润空间有限")
        
        # 毛利率分析
        if indicators.gross_margin is not None:
            gross_pct = indicators.gross_margin * 100 if indicators.gross_margin < 1 else indicators.gross_margin
            if gross_pct > 40:
                factors.append(f"毛利率{gross_pct:.1f}%，具有定价权")
        
        # 营业利润率
        if indicators.operating_margin is not None:
            op_margin = indicators.operating_margin * 100 if indicators.operating_margin < 1 else indicators.operating_margin
            op_score = min(10, op_margin / 1.5)
            scores.append(op_score)
        
        if scores:
            result.profitability_score = sum(scores) / len(scores)
            result.profitability_summary = "；".join(factors) if factors else "盈利能力数据有限"
        else:
            result.profitability_summary = "盈利能力指标不可用"
    
    def _analyze_growth(
        self,
        result: AnalysisResult,
        financials: FinancialData,
        indicators: Optional[KeyIndicators]
    ):
        """
        成长性分析
        
        通过营收增长、盈利增长、季度趋势等评估成长潜力
        """
        scores = []
        factors = []
        
        # 基于指标的增长率
        if indicators:
            if indicators.revenue_growth is not None:
                rev_growth = indicators.revenue_growth * 100 if abs(indicators.revenue_growth) < 10 else indicators.revenue_growth
                growth_score = min(10, max(0, (rev_growth + 10) / 4))  # -10%得0分，30%得满分
                scores.append(growth_score)
                if rev_growth > 20:
                    factors.append(f"营收增长{rev_growth:.1f}%，高速成长")
                elif rev_growth > 0:
                    factors.append(f"营收增长{rev_growth:.1f}%，稳健增长")
                else:
                    factors.append(f"营收下降{abs(rev_growth):.1f}%，需关注")
            
            if indicators.earnings_growth is not None:
                earn_growth = indicators.earnings_growth * 100 if abs(indicators.earnings_growth) < 10 else indicators.earnings_growth
                earn_score = min(10, max(0, (earn_growth + 10) / 4))
                scores.append(earn_score)
                if earn_growth > 25:
                    factors.append(f"盈利增长{earn_growth:.1f}%，业绩高增")
                elif earn_growth < -10:
                    factors.append(f"盈利下降{abs(earn_growth):.1f}%，业绩承压")
        
        # 基于财务报表的季度趋势分析
        if financials.revenue and len(financials.revenue) >= 2:
            # 计算最近季度环比
            latest = financials.revenue[0].get('value', 0)
            previous = financials.revenue[1].get('value', 0)
            if previous and previous != 0:
                qoq_growth = (latest - previous) / abs(previous) * 100
                if qoq_growth > 10:
                    factors.append(f"最新季度营收环比增长{qoq_growth:.1f}%")
                elif qoq_growth < -10:
                    factors.append(f"最新季度营收环比下降{abs(qoq_growth):.1f}%")
        
        if financials.net_income and len(financials.net_income) >= 2:
            latest = financials.net_income[0].get('value', 0)
            previous = financials.net_income[1].get('value', 0)
            if previous and previous != 0 and latest:
                qoq_profit = (latest - previous) / abs(previous) * 100
                if abs(qoq_profit) > 15:
                    direction = "增长" if qoq_profit > 0 else "下降"
                    factors.append(f"净利润环比{direction}{abs(qoq_profit):.1f}%")
        
        if scores:
            result.growth_score = sum(scores) / len(scores)
            result.growth_summary = "；".join(factors) if factors else "成长数据有限"
        else:
            result.growth_summary = "成长性指标不可用" if not factors else "；".join(factors)
    
    def _analyze_health(self, result: AnalysisResult, indicators: KeyIndicators):
        """
        财务健康度分析
        
        通过资产负债率、流动比率、现金流等评估财务风险
        """
        scores = []
        factors = []
        
        # 资产负债率分析
        if indicators.debt_to_equity is not None:
            de_ratio = indicators.debt_to_equity
            if de_ratio < 50:
                scores.append(9)
                factors.append(f"负债率{de_ratio:.1f}%，财务稳健")
            elif de_ratio < 100:
                scores.append(7)
                factors.append(f"负债率{de_ratio:.1f}%，负债适中")
            elif de_ratio < 200:
                scores.append(4)
                factors.append(f"负债率{de_ratio:.1f}%，杠杆较高")
            else:
                scores.append(2)
                factors.append(f"负债率{de_ratio:.1f}%，高杠杆风险")
        
        # 流动比率分析
        if indicators.current_ratio is not None:
            cr = indicators.current_ratio
            if cr > 2:
                scores.append(9)
                factors.append(f"流动比率{cr:.2f}，短期偿债能力强")
            elif cr > 1.5:
                scores.append(7)
                factors.append(f"流动比率{cr:.2f}，流动性良好")
            elif cr > 1:
                scores.append(5)
                factors.append(f"流动比率{cr:.2f}，流动性一般")
            else:
                scores.append(2)
                factors.append(f"流动比率{cr:.2f}，存在流动性风险")
        
        # 速动比率分析
        if indicators.quick_ratio is not None:
            qr = indicators.quick_ratio
            if qr > 1:
                scores.append(8)
            elif qr > 0.5:
                scores.append(5)
            else:
                scores.append(3)
                factors.append(f"速动比率{qr:.2f}，需关注变现能力")
        
        if scores:
            result.health_score = sum(scores) / len(scores)
            result.health_summary = "；".join(factors) if factors else "财务健康数据有限"
        else:
            result.health_summary = "财务健康指标不可用"
    
    def _calculate_trends(self, result: AnalysisResult, financials: FinancialData):
        """
        计算趋势数据，用于报告中的表格展示
        """
        # 营收趋势
        if financials.revenue:
            result.revenue_trend = [
                {"period": item["date"], "value": item["value"]}
                for item in financials.revenue
                if item.get("value") is not None
            ]
        
        # 利润趋势
        if financials.net_income:
            result.profit_trend = [
                {"period": item["date"], "value": item["value"]}
                for item in financials.net_income
                if item.get("value") is not None
            ]
        
        # 利润率趋势（如果有营收和净利润数据）
        if financials.revenue and financials.net_income:
            for i, rev in enumerate(financials.revenue):
                if i < len(financials.net_income):
                    net = financials.net_income[i]
                    if rev.get("value") and net.get("value") and rev["value"] != 0:
                        margin = (net["value"] / rev["value"]) * 100
                        result.margin_trend.append({
                            "period": rev["date"],
                            "value": margin
                        })
    
    def _calculate_overall_score(self, result: AnalysisResult):
        """
        计算综合评分
        
        根据各维度评分加权计算
        权重：估值25%，盈利30%，成长25%，健康20%
        """
        scores = []
        weights = []
        
        if result.valuation_score is not None:
            scores.append(result.valuation_score)
            weights.append(0.25)
        
        if result.profitability_score is not None:
            scores.append(result.profitability_score)
            weights.append(0.30)
        
        if result.growth_score is not None:
            scores.append(result.growth_score)
            weights.append(0.25)
        
        if result.health_score is not None:
            scores.append(result.health_score)
            weights.append(0.20)
        
        if scores:
            # 归一化权重
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            result.overall_score = sum(s * w for s, w in zip(scores, normalized_weights))
    
    def get_rating(self, score: Optional[float]) -> str:
        """
        将评分转换为等级评定
        
        参数:
            score: 数值评分 (0-10)
        返回:
            等级字符串
        """
        if score is None:
            return "N/A"
        if score >= 8:
            return "优秀 ⭐⭐⭐⭐⭐"
        if score >= 6.5:
            return "良好 ⭐⭐⭐⭐"
        if score >= 5:
            return "中等 ⭐⭐⭐"
        if score >= 3:
            return "较弱 ⭐⭐"
        return "风险 ⭐"
