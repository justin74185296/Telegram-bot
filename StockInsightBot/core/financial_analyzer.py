"""
財務指標計算與分析模組
處理財務數據並生成分析結論
"""
from typing import Dict, Any, Optional, List
from utils.loggers import get_logger
from utils.formatters import Formatters

logger = get_logger("FinancialAnalyzer")


class FinancialAnalyzer:
    """
    財務分析器
    計算和解讀各類財務指標
    """
    
    # 指標評級標準
    RATING_CRITERIA = {
        "pe_ratio": {
            "excellent": (0, 15),
            "good": (15, 25),
            "fair": (25, 40),
            "poor": (40, float('inf'))
        },
        "pb_ratio": {
            "excellent": (0, 1),
            "good": (1, 3),
            "fair": (3, 5),
            "poor": (5, float('inf'))
        },
        "roe": {
            "excellent": (0.20, float('inf')),
            "good": (0.15, 0.20),
            "fair": (0.10, 0.15),
            "poor": (0, 0.10)
        },
        "debt_to_equity": {
            "excellent": (0, 0.5),
            "good": (0.5, 1),
            "fair": (1, 2),
            "poor": (2, float('inf'))
        }
    }
    
    @staticmethod
    def rate_indicator(indicator_name: str, value: Optional[float]) -> str:
        """
        評估指標等級
        
        Args:
            indicator_name: 指標名稱
            value: 指標值
        
        Returns:
            評級 (excellent/good/fair/poor/unknown)
        """
        if value is None:
            return "unknown"
        
        criteria = FinancialAnalyzer.RATING_CRITERIA.get(indicator_name)
        if not criteria:
            return "unknown"
        
        for rating, (low, high) in criteria.items():
            if indicator_name == "roe":  # ROE 越高越好
                if low <= value <= high or (high == float('inf') and value >= low):
                    return rating
            else:  # 其他指標越低越好
                if low <= value < high:
                    return rating
        
        return "unknown"
    
    @staticmethod
    def get_rating_emoji(rating: str) -> str:
        """
        根據評級返回表情符號
        
        Args:
            rating: 評級
        
        Returns:
            表情符號
        """
        emoji_map = {
            "excellent": "🟢",
            "good": "🟡",
            "fair": "🟠",
            "poor": "🔴",
            "unknown": "⚪"
        }
        return emoji_map.get(rating, "⚪")
    
    @staticmethod
    def analyze_valuation(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析估值水平
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            估值分析結果
        """
        pe = indicators.get("pe_ratio")
        pb = indicators.get("pb_ratio")
        ps = indicators.get("ps_ratio")
        peg = indicators.get("peg_ratio")
        
        analysis = {
            "pe": {
                "value": pe,
                "rating": FinancialAnalyzer.rate_indicator("pe_ratio", pe),
                "interpretation": ""
            },
            "pb": {
                "value": pb,
                "rating": FinancialAnalyzer.rate_indicator("pb_ratio", pb),
                "interpretation": ""
            },
            "overall_assessment": ""
        }
        
        # PE 解讀
        if pe:
            if pe < 0:
                analysis["pe"]["interpretation"] = "公司處於虧損狀態"
            elif pe < 15:
                analysis["pe"]["interpretation"] = "估值偏低，可能被低估或成長性較差"
            elif pe < 25:
                analysis["pe"]["interpretation"] = "估值合理"
            elif pe < 40:
                analysis["pe"]["interpretation"] = "估值偏高，市場預期較高成長"
            else:
                analysis["pe"]["interpretation"] = "估值過高，需謹慎"
        
        # PB 解讀
        if pb:
            if pb < 1:
                analysis["pb"]["interpretation"] = "股價低於淨資產，可能被低估"
            elif pb < 3:
                analysis["pb"]["interpretation"] = "估值合理"
            else:
                analysis["pb"]["interpretation"] = "估值偏高"
        
        # 綜合評估
        ratings = [analysis["pe"]["rating"], analysis["pb"]["rating"]]
        excellent_count = ratings.count("excellent")
        good_count = ratings.count("good")
        poor_count = ratings.count("poor")
        
        if excellent_count >= 1:
            analysis["overall_assessment"] = "估值具有吸引力"
        elif good_count >= 1:
            analysis["overall_assessment"] = "估值處於合理水平"
        elif poor_count >= 1:
            analysis["overall_assessment"] = "估值偏高，建議謹慎"
        else:
            analysis["overall_assessment"] = "估值數據不足，難以判斷"
        
        return analysis
    
    @staticmethod
    def analyze_profitability(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析盈利能力
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            盈利能力分析結果
        """
        roe = indicators.get("roe")
        roa = indicators.get("roa")
        profit_margin = indicators.get("profit_margin")
        operating_margin = indicators.get("operating_margin")
        
        analysis = {
            "roe": {
                "value": roe,
                "rating": FinancialAnalyzer.rate_indicator("roe", roe),
                "interpretation": ""
            },
            "profit_margin": {
                "value": profit_margin,
                "interpretation": ""
            },
            "overall_assessment": ""
        }
        
        # ROE 解讀
        if roe:
            if roe >= 0.20:
                analysis["roe"]["interpretation"] = "優秀的股東權益報酬率"
            elif roe >= 0.15:
                analysis["roe"]["interpretation"] = "良好的股東權益報酬率"
            elif roe >= 0.10:
                analysis["roe"]["interpretation"] = "一般的股東權益報酬率"
            else:
                analysis["roe"]["interpretation"] = "較低的股東權益報酬率"
        
        # 利潤率解讀
        if profit_margin:
            if profit_margin >= 0.20:
                analysis["profit_margin"]["interpretation"] = "高利潤率，具有定價能力"
            elif profit_margin >= 0.10:
                analysis["profit_margin"]["interpretation"] = "利潤率適中"
            else:
                analysis["profit_margin"]["interpretation"] = "利潤率偏低"
        
        # 綜合評估
        if roe and roe >= 0.15 and profit_margin and profit_margin >= 0.10:
            analysis["overall_assessment"] = "盈利能力優秀"
        elif roe and roe >= 0.10:
            analysis["overall_assessment"] = "盈利能力一般"
        else:
            analysis["overall_assessment"] = "盈利能力需要關注"
        
        return analysis
    
    @staticmethod
    def analyze_financial_health(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析財務健康度
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            財務健康度分析結果
        """
        debt_to_equity = indicators.get("debt_to_equity")
        current_ratio = indicators.get("current_ratio")
        quick_ratio = indicators.get("quick_ratio")
        
        analysis = {
            "debt_to_equity": {
                "value": debt_to_equity,
                "rating": FinancialAnalyzer.rate_indicator("debt_to_equity", debt_to_equity),
                "interpretation": ""
            },
            "liquidity": {
                "current_ratio": current_ratio,
                "quick_ratio": quick_ratio,
                "interpretation": ""
            },
            "overall_assessment": ""
        }
        
        # 負債比解讀
        if debt_to_equity:
            if debt_to_equity < 0.5:
                analysis["debt_to_equity"]["interpretation"] = "負債水平低，財務穩健"
            elif debt_to_equity < 1:
                analysis["debt_to_equity"]["interpretation"] = "負債水平適中"
            elif debt_to_equity < 2:
                analysis["debt_to_equity"]["interpretation"] = "負債水平偏高"
            else:
                analysis["debt_to_equity"]["interpretation"] = "負債水平過高，存在風險"
        
        # 流動性解讀
        if current_ratio:
            if current_ratio >= 2:
                analysis["liquidity"]["interpretation"] = "流動性充足"
            elif current_ratio >= 1:
                analysis["liquidity"]["interpretation"] = "流動性尚可"
            else:
                analysis["liquidity"]["interpretation"] = "流動性不足，可能面臨短期償債壓力"
        
        # 綜合評估
        is_healthy = True
        if debt_to_equity and debt_to_equity > 2:
            is_healthy = False
        if current_ratio and current_ratio < 1:
            is_healthy = False
        
        analysis["overall_assessment"] = "財務狀況健康" if is_healthy else "財務狀況需要關注"
        
        return analysis
    
    @staticmethod
    def analyze_growth(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析成長性
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            成長性分析結果
        """
        revenue_growth = indicators.get("revenue_growth")
        earnings_growth = indicators.get("earnings_growth")
        
        analysis = {
            "revenue_growth": {
                "value": revenue_growth,
                "interpretation": ""
            },
            "earnings_growth": {
                "value": earnings_growth,
                "interpretation": ""
            },
            "overall_assessment": ""
        }
        
        # 營收成長解讀
        if revenue_growth:
            if revenue_growth >= 0.20:
                analysis["revenue_growth"]["interpretation"] = "高速成長"
            elif revenue_growth >= 0.10:
                analysis["revenue_growth"]["interpretation"] = "穩健成長"
            elif revenue_growth >= 0:
                analysis["revenue_growth"]["interpretation"] = "緩慢成長"
            else:
                analysis["revenue_growth"]["interpretation"] = "營收下滑"
        
        # 獲利成長解讀
        if earnings_growth:
            if earnings_growth >= 0.20:
                analysis["earnings_growth"]["interpretation"] = "獲利快速成長"
            elif earnings_growth >= 0:
                analysis["earnings_growth"]["interpretation"] = "獲利穩定成長"
            else:
                analysis["earnings_growth"]["interpretation"] = "獲利下滑"
        
        # 綜合評估
        if revenue_growth and revenue_growth >= 0.10 and earnings_growth and earnings_growth >= 0.10:
            analysis["overall_assessment"] = "成長性優秀"
        elif revenue_growth and revenue_growth >= 0:
            analysis["overall_assessment"] = "成長性一般"
        else:
            analysis["overall_assessment"] = "成長性欠佳"
        
        return analysis
    
    @staticmethod
    def generate_full_analysis(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整財務分析
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            完整分析結果
        """
        return {
            "valuation": FinancialAnalyzer.analyze_valuation(indicators),
            "profitability": FinancialAnalyzer.analyze_profitability(indicators),
            "financial_health": FinancialAnalyzer.analyze_financial_health(indicators),
            "growth": FinancialAnalyzer.analyze_growth(indicators)
        }
    
    @staticmethod
    def format_indicators_summary(indicators: Dict[str, Any]) -> str:
        """
        格式化指標摘要為文字
        
        Args:
            indicators: 財務指標字典
        
        Returns:
            格式化的文字摘要
        """
        fmt = Formatters()
        
        lines = ["📊 **關鍵財務指標**\n"]
        
        # 估值指標
        pe = indicators.get("pe_ratio")
        pb = indicators.get("pb_ratio")
        ps = indicators.get("ps_ratio")
        
        lines.append("**估值指標**")
        if pe:
            rating = FinancialAnalyzer.rate_indicator("pe_ratio", pe)
            emoji = FinancialAnalyzer.get_rating_emoji(rating)
            lines.append(f"  {emoji} P/E: {fmt.format_number(pe)}")
        if pb:
            rating = FinancialAnalyzer.rate_indicator("pb_ratio", pb)
            emoji = FinancialAnalyzer.get_rating_emoji(rating)
            lines.append(f"  {emoji} P/B: {fmt.format_number(pb)}")
        if ps:
            lines.append(f"  P/S: {fmt.format_number(ps)}")
        
        # 盈利能力
        roe = indicators.get("roe")
        roa = indicators.get("roa")
        profit_margin = indicators.get("profit_margin")
        
        lines.append("\n**盈利能力**")
        if roe:
            rating = FinancialAnalyzer.rate_indicator("roe", roe)
            emoji = FinancialAnalyzer.get_rating_emoji(rating)
            lines.append(f"  {emoji} ROE: {fmt.format_percentage(roe * 100)}")
        if roa:
            lines.append(f"  ROA: {fmt.format_percentage(roa * 100)}")
        if profit_margin:
            lines.append(f"  淨利率: {fmt.format_percentage(profit_margin * 100)}")
        
        # 財務健康
        debt_to_equity = indicators.get("debt_to_equity")
        current_ratio = indicators.get("current_ratio")
        
        lines.append("\n**財務健康**")
        if debt_to_equity:
            rating = FinancialAnalyzer.rate_indicator("debt_to_equity", debt_to_equity)
            emoji = FinancialAnalyzer.get_rating_emoji(rating)
            lines.append(f"  {emoji} 負債權益比: {fmt.format_number(debt_to_equity)}")
        if current_ratio:
            lines.append(f"  流動比率: {fmt.format_number(current_ratio)}")
        
        # 股息
        dividend_yield = indicators.get("dividend_yield")
        if dividend_yield:
            lines.append(f"\n**股息**")
            lines.append(f"  股息率: {fmt.format_percentage(dividend_yield * 100)}")
        
        return "\n".join(lines)
