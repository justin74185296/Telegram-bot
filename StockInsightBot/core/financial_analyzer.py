"""
財務分析模組
計算和分析關鍵財務指標
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """財務分析器"""
    
    @staticmethod
    def analyze_valuation(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        估值分析
        判斷股票估值水平
        """
        pe = indicators.get('pe_ratio', 0) or 0
        pb = indicators.get('pb_ratio', 0) or 0
        ps = indicators.get('ps_ratio', 0) or 0
        
        analysis = {
            'pe_assessment': '',
            'pb_assessment': '',
            'overall': ''
        }
        
        # PE 評估
        if pe > 0:
            if pe < 15:
                analysis['pe_assessment'] = '低估值'
            elif pe < 25:
                analysis['pe_assessment'] = '合理估值'
            elif pe < 40:
                analysis['pe_assessment'] = '偏高估值'
            else:
                analysis['pe_assessment'] = '高估值'
        
        # PB 評估
        if pb > 0:
            if pb < 1:
                analysis['pb_assessment'] = '低於淨資產'
            elif pb < 3:
                analysis['pb_assessment'] = '合理'
            else:
                analysis['pb_assessment'] = '偏高'
        
        return analysis
    
    @staticmethod
    def analyze_profitability(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        盈利能力分析
        """
        roe = (indicators.get('roe', 0) or 0) * 100
        roa = (indicators.get('roa', 0) or 0) * 100
        profit_margin = (indicators.get('profit_margin', 0) or 0) * 100
        
        analysis = {
            'roe_level': '',
            'profitability': ''
        }
        
        if roe > 20:
            analysis['roe_level'] = '優秀'
        elif roe > 15:
            analysis['roe_level'] = '良好'
        elif roe > 10:
            analysis['roe_level'] = '一般'
        elif roe > 0:
            analysis['roe_level'] = '偏低'
        else:
            analysis['roe_level'] = '虧損'
        
        if profit_margin > 20:
            analysis['profitability'] = '高利潤率'
        elif profit_margin > 10:
            analysis['profitability'] = '中等利潤率'
        elif profit_margin > 0:
            analysis['profitability'] = '低利潤率'
        else:
            analysis['profitability'] = '虧損'
        
        return analysis
    
    @staticmethod
    def analyze_financial_health(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        財務健康度分析
        """
        debt_to_equity = indicators.get('debt_to_equity', 0) or 0
        current_ratio = indicators.get('current_ratio', 0) or 0
        
        analysis = {
            'debt_level': '',
            'liquidity': ''
        }
        
        if debt_to_equity < 50:
            analysis['debt_level'] = '低負債'
        elif debt_to_equity < 100:
            analysis['debt_level'] = '適度負債'
        elif debt_to_equity < 200:
            analysis['debt_level'] = '高負債'
        else:
            analysis['debt_level'] = '極高負債'
        
        if current_ratio > 2:
            analysis['liquidity'] = '流動性充裕'
        elif current_ratio > 1:
            analysis['liquidity'] = '流動性正常'
        else:
            analysis['liquidity'] = '流動性緊張'
        
        return analysis
    
    @staticmethod
    def generate_summary(quote: Dict, indicators: Dict, financials: Dict) -> str:
        """
        生成財務摘要
        """
        name = quote.get('name', quote.get('symbol', ''))
        price = quote.get('current_price', 0)
        change_pct = quote.get('change_percent', 0)
        
        pe = indicators.get('pe_ratio', 0) or 0
        pb = indicators.get('pb_ratio', 0) or 0
        roe = (indicators.get('roe', 0) or 0) * 100
        
        summary = f"""
**{name}** 財務摘要

📊 當前股價: {price:.2f} ({change_pct:+.2f}%)

📈 關鍵指標:
- PE: {pe:.2f}
- PB: {pb:.2f}
- ROE: {roe:.2f}%
"""
        return summary
