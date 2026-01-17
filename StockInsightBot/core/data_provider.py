"""
統一數據獲取層
封裝 yfinance 獲取股票數據
"""
import yfinance as yf
from typing import Dict, Any, Optional, List
from datetime import datetime
from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)

# 緩存配置：最多100個條目，每個條目存活300秒
_cache = TTLCache(maxsize=100, ttl=300)


class StockDataProvider:
    """股票數據提供者"""
    
    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """
        標準化股票代碼
        - 美股: AAPL, TSLA
        - 港股: 0700.HK, 9988.HK
        - A股: 600519.SS (上海), 000001.SZ (深圳)
        """
        symbol = symbol.upper().strip()
        
        # 如果是純數字，判斷市場
        if symbol.isdigit():
            if len(symbol) == 4:
                # 港股
                return f"{symbol}.HK"
            elif len(symbol) == 6:
                if symbol.startswith('6'):
                    return f"{symbol}.SS"  # 上海
                else:
                    return f"{symbol}.SZ"  # 深圳
        
        return symbol
    
    @staticmethod
    def fetch_realtime_quote(symbol: str) -> Dict[str, Any]:
        """
        獲取實時報價
        返回: 價格、漲跌幅、成交量、市值等
        """
        cache_key = f"quote_{symbol}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            normalized = StockDataProvider._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            info = ticker.info
            
            # 獲取歷史數據計算漲跌
            hist = ticker.history(period="2d")
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', 0) or info.get('regularMarketPreviousClose', 0)
            
            if len(hist) >= 2 and current_price == 0:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
            
            change = current_price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            result = {
                'symbol': normalized,
                'name': info.get('shortName') or info.get('longName', symbol),
                'current_price': current_price,
                'previous_close': prev_close,
                'change': change,
                'change_percent': change_pct,
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            _cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 報價失敗: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    @staticmethod
    def fetch_key_indicators(symbol: str) -> Dict[str, Any]:
        """
        獲取關鍵財務指標
        PE、PB、ROE、股息率等
        """
        cache_key = f"indicators_{symbol}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            normalized = StockDataProvider._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            info = ticker.info
            
            result = {
                'pe_ratio': info.get('trailingPE') or info.get('forwardPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'ps_ratio': info.get('priceToSalesTrailing12Months', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'roe': info.get('returnOnEquity', 0),
                'roa': info.get('returnOnAssets', 0),
                'profit_margin': info.get('profitMargins', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'dividend_rate': info.get('dividendRate', 0),
                'beta': info.get('beta', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'free_cash_flow': info.get('freeCashflow', 0),
                'operating_cash_flow': info.get('operatingCashflow', 0),
            }
            
            _cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 指標失敗: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def fetch_financials(symbol: str) -> Dict[str, Any]:
        """
        獲取財務報表數據
        資產負債表、利潤表、現金流量表
        """
        cache_key = f"financials_{symbol}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            normalized = StockDataProvider._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            
            result = {
                'income_statement': {},
                'balance_sheet': {},
                'cash_flow': {}
            }
            
            # 收入報表
            income = ticker.quarterly_income_stmt
            if income is not None and not income.empty:
                latest = income.iloc[:, :4]  # 最近4季
                result['income_statement'] = {
                    'total_revenue': latest.loc['Total Revenue'].tolist() if 'Total Revenue' in latest.index else [],
                    'net_income': latest.loc['Net Income'].tolist() if 'Net Income' in latest.index else [],
                    'gross_profit': latest.loc['Gross Profit'].tolist() if 'Gross Profit' in latest.index else [],
                    'operating_income': latest.loc['Operating Income'].tolist() if 'Operating Income' in latest.index else [],
                    'dates': [str(d.date()) for d in latest.columns]
                }
            
            # 資產負債表
            balance = ticker.quarterly_balance_sheet
            if balance is not None and not balance.empty:
                latest = balance.iloc[:, :4]
                result['balance_sheet'] = {
                    'total_assets': latest.loc['Total Assets'].tolist() if 'Total Assets' in latest.index else [],
                    'total_liabilities': latest.loc['Total Liabilities Net Minority Interest'].tolist() if 'Total Liabilities Net Minority Interest' in latest.index else [],
                    'total_equity': latest.loc['Stockholders Equity'].tolist() if 'Stockholders Equity' in latest.index else [],
                    'dates': [str(d.date()) for d in latest.columns]
                }
            
            # 現金流量表
            cashflow = ticker.quarterly_cashflow
            if cashflow is not None and not cashflow.empty:
                latest = cashflow.iloc[:, :4]
                result['cash_flow'] = {
                    'operating_cash_flow': latest.loc['Operating Cash Flow'].tolist() if 'Operating Cash Flow' in latest.index else [],
                    'free_cash_flow': latest.loc['Free Cash Flow'].tolist() if 'Free Cash Flow' in latest.index else [],
                    'dates': [str(d.date()) for d in latest.columns]
                }
            
            _cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 財務數據失敗: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def fetch_company_news(symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        獲取公司新聞
        """
        cache_key = f"news_{symbol}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            normalized = StockDataProvider._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            news = ticker.news
            
            result = []
            if news:
                for item in news[:limit]:
                    # yfinance 1.0+ 格式
                    if isinstance(item, dict):
                        content = item.get('content', {})
                        if content:
                            result.append({
                                'title': content.get('title', ''),
                                'publisher': content.get('provider', {}).get('displayName', ''),
                                'link': content.get('canonicalUrl', {}).get('url', ''),
                                'publish_time': content.get('pubDate', '')
                            })
                        else:
                            # 舊格式兼容
                            result.append({
                                'title': item.get('title', ''),
                                'publisher': item.get('publisher', ''),
                                'link': item.get('link', ''),
                                'publish_time': item.get('providerPublishTime', '')
                            })
            
            _cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 新聞失敗: {e}")
            return []
    
    @staticmethod
    def get_company_profile(symbol: str) -> Dict[str, Any]:
        """獲取公司簡介"""
        cache_key = f"profile_{symbol}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            normalized = StockDataProvider._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            info = ticker.info
            
            result = {
                'name': info.get('shortName') or info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'country': info.get('country', ''),
                'website': info.get('website', ''),
                'employees': info.get('fullTimeEmployees', 0),
                'description': info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else ''
            }
            
            _cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 公司簡介失敗: {e}")
            return {'error': str(e)}
