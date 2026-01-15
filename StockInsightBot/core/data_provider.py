"""
統一數據獲取層
封裝 yfinance 獲取股票數據
支援美股、港股、A股等多市場
"""
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
from utils.loggers import get_logger

logger = get_logger("DataProvider")


class StockDataProvider:
    """
    股票數據提供者
    統一接口獲取各類股票數據
    """
    
    def __init__(self, cache_ttl: int = 300, cache_maxsize: int = 100):
        """
        初始化數據提供者
        
        Args:
            cache_ttl: 快取有效期（秒）
            cache_maxsize: 快取最大條目數
        """
        self._cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        logger.info(f"數據提供者初始化完成，快取 TTL={cache_ttl}s, 最大條目={cache_maxsize}")
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        標準化股票代碼
        
        Args:
            symbol: 原始股票代碼
        
        Returns:
            標準化後的代碼
        """
        symbol = symbol.upper().strip()
        
        # 處理港股 (如 0700 -> 0700.HK)
        if symbol.isdigit() and len(symbol) == 4:
            return f"{symbol}.HK"
        
        # 處理 A 股 (如 600519 -> 600519.SS 或 000001 -> 000001.SZ)
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('6', '9')):
                return f"{symbol}.SS"  # 上海
            else:
                return f"{symbol}.SZ"  # 深圳
        
        return symbol
    
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """
        獲取股票 Ticker 對象（帶快取）
        
        Args:
            symbol: 股票代碼
        
        Returns:
            yfinance Ticker 對象
        """
        normalized = self._normalize_symbol(symbol)
        cache_key = f"ticker_{normalized}"
        
        if cache_key not in self._cache:
            self._cache[cache_key] = yf.Ticker(normalized)
            logger.debug(f"創建新的 Ticker: {normalized}")
        
        return self._cache[cache_key]
    
    def fetch_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        獲取實時報價數據
        
        Args:
            symbol: 股票代碼
        
        Returns:
            包含價格、漲跌幅、成交量等信息的字典
        """
        cache_key = f"quote_{symbol}"
        if cache_key in self._cache:
            logger.debug(f"從快取獲取報價: {symbol}")
            return self._cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            # 獲取歷史數據計算漲跌
            hist = ticker.history(period="5d")
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose', 0)
            
            # 計算漲跌幅
            if previous_close and previous_close > 0:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            else:
                change = 0
                change_percent = 0
            
            quote = {
                "symbol": self._normalize_symbol(symbol),
                "name": info.get('shortName') or info.get('longName', symbol),
                "current_price": current_price,
                "previous_close": previous_close,
                "change": change,
                "change_percent": change_percent,
                "open": info.get('open') or info.get('regularMarketOpen', 0),
                "high": info.get('dayHigh') or info.get('regularMarketDayHigh', 0),
                "low": info.get('dayLow') or info.get('regularMarketDayLow', 0),
                "volume": info.get('volume') or info.get('regularMarketVolume', 0),
                "market_cap": info.get('marketCap', 0),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange', 'Unknown'),
                "timestamp": datetime.now().isoformat(),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 0),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow', 0),
            }
            
            self._cache[cache_key] = quote
            logger.info(f"獲取報價成功: {symbol} @ {current_price}")
            return quote
            
        except Exception as e:
            logger.error(f"獲取報價失敗 {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_key_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        獲取關鍵財務指標
        
        Args:
            symbol: 股票代碼
        
        Returns:
            包含 PE、PB、ROE 等指標的字典
        """
        cache_key = f"indicators_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            indicators = {
                "symbol": self._normalize_symbol(symbol),
                "pe_ratio": info.get('trailingPE') or info.get('forwardPE'),
                "pb_ratio": info.get('priceToBook'),
                "ps_ratio": info.get('priceToSalesTrailing12Months'),
                "peg_ratio": info.get('pegRatio'),
                "dividend_yield": info.get('dividendYield'),
                "dividend_rate": info.get('dividendRate'),
                "eps": info.get('trailingEps'),
                "beta": info.get('beta'),
                "roe": info.get('returnOnEquity'),
                "roa": info.get('returnOnAssets'),
                "profit_margin": info.get('profitMargins'),
                "operating_margin": info.get('operatingMargins'),
                "revenue_growth": info.get('revenueGrowth'),
                "earnings_growth": info.get('earningsGrowth'),
                "debt_to_equity": info.get('debtToEquity'),
                "current_ratio": info.get('currentRatio'),
                "quick_ratio": info.get('quickRatio'),
                "free_cash_flow": info.get('freeCashflow'),
                "operating_cash_flow": info.get('operatingCashflow'),
                "timestamp": datetime.now().isoformat()
            }
            
            self._cache[cache_key] = indicators
            logger.info(f"獲取指標成功: {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"獲取指標失敗 {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_financials(self, symbol: str) -> Dict[str, Any]:
        """
        獲取財務報表數據
        
        Args:
            symbol: 股票代碼
        
        Returns:
            包含損益表、資產負債表、現金流量表的字典
        """
        cache_key = f"financials_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            
            # 獲取財務報表
            income_stmt = ticker.quarterly_income_stmt
            balance_sheet = ticker.quarterly_balance_sheet
            cash_flow = ticker.quarterly_cashflow
            
            financials = {
                "symbol": self._normalize_symbol(symbol),
                "income_statement": self._process_dataframe(income_stmt),
                "balance_sheet": self._process_dataframe(balance_sheet),
                "cash_flow": self._process_dataframe(cash_flow),
                "timestamp": datetime.now().isoformat()
            }
            
            self._cache[cache_key] = financials
            logger.info(f"獲取財報成功: {symbol}")
            return financials
            
        except Exception as e:
            logger.error(f"獲取財報失敗 {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_dataframe(self, df) -> Dict[str, Any]:
        """
        處理 pandas DataFrame 轉換為字典
        
        Args:
            df: pandas DataFrame
        
        Returns:
            處理後的字典
        """
        if df is None or df.empty:
            return {}
        
        try:
            # 只取最近 4 個季度
            df = df.iloc[:, :4] if df.shape[1] > 4 else df
            result = {}
            
            for col in df.columns:
                period = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                result[period] = {}
                for idx in df.index:
                    value = df.loc[idx, col]
                    # 處理 NaN 值
                    if value is not None and str(value) != 'nan':
                        result[period][str(idx)] = float(value) if isinstance(value, (int, float)) else value
            
            return result
        except Exception as e:
            logger.error(f"處理 DataFrame 失敗: {e}")
            return {}
    
    def fetch_company_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        獲取公司相關新聞
        
        Args:
            symbol: 股票代碼
            limit: 返回新聞數量限制
        
        Returns:
            新聞列表
        """
        cache_key = f"news_{symbol}_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            news_data = ticker.news
            
            news_list = []
            
            # yfinance 1.0+ 新格式處理
            if isinstance(news_data, dict) and 'news' in news_data:
                news_items = news_data.get('news', [])
            elif isinstance(news_data, list):
                news_items = news_data
            else:
                news_items = []
            
            for item in news_items[:limit]:
                # 處理不同的數據結構
                if isinstance(item, dict):
                    # 獲取標題
                    title = item.get('title', '')
                    if not title and 'content' in item:
                        content = item.get('content', {})
                        title = content.get('title', '') if isinstance(content, dict) else ''
                    
                    # 獲取發布者
                    publisher = item.get('publisher', '')
                    if not publisher and 'content' in item:
                        content = item.get('content', {})
                        if isinstance(content, dict):
                            provider = content.get('provider', {})
                            publisher = provider.get('displayName', '') if isinstance(provider, dict) else ''
                    
                    # 獲取連結
                    link = item.get('link', '') or item.get('url', '')
                    if not link and 'content' in item:
                        content = item.get('content', {})
                        if isinstance(content, dict):
                            click_through = content.get('clickThroughUrl', {})
                            link = click_through.get('url', '') if isinstance(click_through, dict) else ''
                    
                    # 獲取時間
                    pub_time = item.get('providerPublishTime', 0)
                    if not pub_time and 'content' in item:
                        content = item.get('content', {})
                        if isinstance(content, dict):
                            pub_time = content.get('pubDate', 0)
                            if isinstance(pub_time, str):
                                try:
                                    pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00')).timestamp()
                                except:
                                    pub_time = 0
                    
                    news_item = {
                        "title": title or "無標題",
                        "publisher": publisher or "未知來源",
                        "link": link,
                        "published_time": datetime.fromtimestamp(pub_time).isoformat() if pub_time else None,
                        "type": item.get('type', 'news')
                    }
                    
                    if news_item["title"] and news_item["title"] != "無標題":
                        news_list.append(news_item)
            
            self._cache[cache_key] = news_list
            logger.info(f"獲取新聞成功: {symbol}, 共 {len(news_list)} 條")
            return news_list
            
        except Exception as e:
            logger.error(f"獲取新聞失敗 {symbol}: {e}")
            return []
    
    def fetch_historical_data(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """
        獲取歷史價格數據
        
        Args:
            symbol: 股票代碼
            period: 時間範圍 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            歷史數據字典
        """
        cache_key = f"history_{symbol}_{period}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"symbol": symbol, "error": "無歷史數據"}
            
            history = {
                "symbol": self._normalize_symbol(symbol),
                "period": period,
                "data": [],
                "summary": {
                    "start_price": hist['Close'].iloc[0] if len(hist) > 0 else 0,
                    "end_price": hist['Close'].iloc[-1] if len(hist) > 0 else 0,
                    "high": hist['High'].max(),
                    "low": hist['Low'].min(),
                    "avg_volume": hist['Volume'].mean(),
                    "total_volume": hist['Volume'].sum()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 計算期間漲跌幅
            if history["summary"]["start_price"] > 0:
                history["summary"]["period_return"] = (
                    (history["summary"]["end_price"] - history["summary"]["start_price"]) 
                    / history["summary"]["start_price"] * 100
                )
            
            self._cache[cache_key] = history
            logger.info(f"獲取歷史數據成功: {symbol} ({period})")
            return history
            
        except Exception as e:
            logger.error(f"獲取歷史數據失敗 {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_full_analysis_data(self, symbol: str) -> Dict[str, Any]:
        """
        獲取完整的分析數據（整合所有數據源）
        
        Args:
            symbol: 股票代碼
        
        Returns:
            整合後的完整數據
        """
        logger.info(f"開始獲取 {symbol} 的完整分析數據...")
        
        return {
            "quote": self.fetch_realtime_quote(symbol),
            "indicators": self.fetch_key_indicators(symbol),
            "financials": self.fetch_financials(symbol),
            "news": self.fetch_company_news(symbol),
            "history": self.fetch_historical_data(symbol, "3mo"),
            "timestamp": datetime.now().isoformat()
        }
