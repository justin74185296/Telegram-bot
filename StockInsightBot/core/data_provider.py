"""
统一数据提供层
封装 yfinance 和 akshare，提供股票数据获取的统一接口
支持美股、港股、A股等多市场数据
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from cachetools import TTLCache
import yfinance as yf
import pandas as pd

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class StockQuote:
    """股票实时报价数据结构"""
    symbol: str
    name: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    day_high: float
    day_low: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    currency: str
    exchange: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FinancialData:
    """财务数据结构"""
    symbol: str
    income_statement: Optional[pd.DataFrame] = None
    balance_sheet: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class KeyIndicators:
    """关键财务指标"""
    symbol: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    beta: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    summary: str
    url: str
    publisher: str
    published_time: Optional[datetime] = None


class StockDataProvider:
    """
    股票数据提供者
    整合多个数据源，提供统一的数据获取接口
    内置缓存机制避免频繁API调用
    """
    
    def __init__(self):
        """初始化数据提供者，设置缓存"""
        # 设置不同类型数据的缓存
        self._quote_cache = TTLCache(maxsize=100, ttl=settings.cache_ttl_quote)
        self._financials_cache = TTLCache(maxsize=50, ttl=settings.cache_ttl_financials)
        self._news_cache = TTLCache(maxsize=50, ttl=settings.cache_ttl_news)
        self._indicators_cache = TTLCache(maxsize=100, ttl=settings.cache_ttl_quote)
        
        logger.info("StockDataProvider 初始化完成")
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码
        美股: AAPL, TSLA
        港股: 0700.HK, 9988.HK
        A股: 600519.SS (上海), 000858.SZ (深圳)
        """
        symbol = symbol.upper().strip()
        
        # 如果是纯数字且6位，判断A股市场
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith('6'):
                return f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                return f"{symbol}.SZ"
        
        # 港股处理
        if symbol.isdigit() and len(symbol) <= 5:
            return f"{symbol.zfill(4)}.HK"
        
        return symbol
    
    async def fetch_realtime_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        获取股票实时报价
        
        Args:
            symbol: 股票代码
            
        Returns:
            StockQuote 对象，包含实时价格等信息
        """
        normalized_symbol = self._normalize_symbol(symbol)
        
        # 检查缓存
        if normalized_symbol in self._quote_cache:
            logger.debug(f"从缓存获取 {normalized_symbol} 报价")
            return self._quote_cache[normalized_symbol]
        
        try:
            logger.info(f"正在获取 {normalized_symbol} 的实时报价...")
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"无法获取 {normalized_symbol} 的数据")
                return None
            
            quote = StockQuote(
                symbol=normalized_symbol,
                name=info.get('longName') or info.get('shortName', normalized_symbol),
                current_price=info.get('regularMarketPrice', 0) or info.get('currentPrice', 0),
                previous_close=info.get('previousClose', 0) or info.get('regularMarketPreviousClose', 0),
                change=info.get('regularMarketChange', 0),
                change_percent=info.get('regularMarketChangePercent', 0),
                volume=info.get('regularMarketVolume', 0) or info.get('volume', 0),
                market_cap=info.get('marketCap', 0),
                day_high=info.get('dayHigh', 0) or info.get('regularMarketDayHigh', 0),
                day_low=info.get('dayLow', 0) or info.get('regularMarketDayLow', 0),
                fifty_two_week_high=info.get('fiftyTwoWeekHigh', 0),
                fifty_two_week_low=info.get('fiftyTwoWeekLow', 0),
                currency=info.get('currency', 'USD'),
                exchange=info.get('exchange', 'Unknown')
            )
            
            # 如果涨跌幅为0但有前收盘价，手动计算
            if quote.change_percent == 0 and quote.previous_close > 0:
                quote.change = quote.current_price - quote.previous_close
                quote.change_percent = (quote.change / quote.previous_close) * 100
            
            # 存入缓存
            self._quote_cache[normalized_symbol] = quote
            logger.info(f"成功获取 {normalized_symbol} 报价: {quote.current_price} {quote.currency}")
            
            return quote
            
        except Exception as e:
            logger.error(f"获取 {normalized_symbol} 报价失败: {e}")
            return None
    
    async def fetch_financials(self, symbol: str) -> Optional[FinancialData]:
        """
        获取财务报表数据（最近4个季度）
        
        Args:
            symbol: 股票代码
            
        Returns:
            FinancialData 对象，包含三大财务报表
        """
        normalized_symbol = self._normalize_symbol(symbol)
        
        # 检查缓存
        if normalized_symbol in self._financials_cache:
            logger.debug(f"从缓存获取 {normalized_symbol} 财务数据")
            return self._financials_cache[normalized_symbol]
        
        try:
            logger.info(f"正在获取 {normalized_symbol} 的财务数据...")
            ticker = yf.Ticker(normalized_symbol)
            
            financial_data = FinancialData(
                symbol=normalized_symbol,
                income_statement=ticker.quarterly_income_stmt,
                balance_sheet=ticker.quarterly_balance_sheet,
                cash_flow=ticker.quarterly_cash_flow
            )
            
            # 存入缓存
            self._financials_cache[normalized_symbol] = financial_data
            logger.info(f"成功获取 {normalized_symbol} 财务数据")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"获取 {normalized_symbol} 财务数据失败: {e}")
            return None
    
    async def fetch_key_indicators(self, symbol: str) -> Optional[KeyIndicators]:
        """
        获取关键财务指标
        
        Args:
            symbol: 股票代码
            
        Returns:
            KeyIndicators 对象
        """
        normalized_symbol = self._normalize_symbol(symbol)
        
        # 检查缓存
        if normalized_symbol in self._indicators_cache:
            logger.debug(f"从缓存获取 {normalized_symbol} 关键指标")
            return self._indicators_cache[normalized_symbol]
        
        try:
            logger.info(f"正在获取 {normalized_symbol} 的关键指标...")
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            indicators = KeyIndicators(
                symbol=normalized_symbol,
                pe_ratio=info.get('trailingPE') or info.get('forwardPE'),
                pb_ratio=info.get('priceToBook'),
                ps_ratio=info.get('priceToSalesTrailing12Months'),
                roe=info.get('returnOnEquity'),
                roa=info.get('returnOnAssets'),
                debt_to_equity=info.get('debtToEquity'),
                current_ratio=info.get('currentRatio'),
                dividend_yield=info.get('dividendYield'),
                profit_margin=info.get('profitMargins'),
                operating_margin=info.get('operatingMargins'),
                revenue_growth=info.get('revenueGrowth'),
                earnings_growth=info.get('earningsGrowth'),
                beta=info.get('beta')
            )
            
            # 存入缓存
            self._indicators_cache[normalized_symbol] = indicators
            logger.info(f"成功获取 {normalized_symbol} 关键指标")
            
            return indicators
            
        except Exception as e:
            logger.error(f"获取 {normalized_symbol} 关键指标失败: {e}")
            return None
    
    async def fetch_company_news(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        """
        获取公司相关新闻
        
        Args:
            symbol: 股票代码
            limit: 返回新闻条数限制
            
        Returns:
            NewsItem 列表
        """
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"{normalized_symbol}_{limit}"
        
        # 检查缓存
        if cache_key in self._news_cache:
            logger.debug(f"从缓存获取 {normalized_symbol} 新闻")
            return self._news_cache[cache_key]
        
        try:
            logger.info(f"正在获取 {normalized_symbol} 的相关新闻...")
            ticker = yf.Ticker(normalized_symbol)
            news_data = ticker.news
            
            news_items = []
            for item in news_data[:limit]:
                published_time = None
                if 'providerPublishTime' in item:
                    published_time = datetime.fromtimestamp(item['providerPublishTime'])
                
                news_items.append(NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('summary', item.get('title', '')),
                    url=item.get('link', ''),
                    publisher=item.get('publisher', 'Unknown'),
                    published_time=published_time
                ))
            
            # 存入缓存
            self._news_cache[cache_key] = news_items
            logger.info(f"成功获取 {normalized_symbol} 新闻 {len(news_items)} 条")
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取 {normalized_symbol} 新闻失败: {e}")
            return []
    
    async def fetch_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取历史价格数据
        
        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        normalized_symbol = self._normalize_symbol(symbol)
        
        try:
            logger.info(f"正在获取 {normalized_symbol} 的历史数据 (周期: {period})...")
            ticker = yf.Ticker(normalized_symbol)
            history = ticker.history(period=period)
            
            if history.empty:
                logger.warning(f"无法获取 {normalized_symbol} 的历史数据")
                return None
            
            logger.info(f"成功获取 {normalized_symbol} 历史数据 {len(history)} 条")
            return history
            
        except Exception as e:
            logger.error(f"获取 {normalized_symbol} 历史数据失败: {e}")
            return None
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清除缓存
        
        Args:
            symbol: 指定股票代码，为None时清除所有缓存
        """
        if symbol:
            normalized_symbol = self._normalize_symbol(symbol)
            self._quote_cache.pop(normalized_symbol, None)
            self._financials_cache.pop(normalized_symbol, None)
            self._indicators_cache.pop(normalized_symbol, None)
            # 清除该股票的所有新闻缓存
            keys_to_remove = [k for k in self._news_cache.keys() if k.startswith(normalized_symbol)]
            for key in keys_to_remove:
                self._news_cache.pop(key, None)
            logger.info(f"已清除 {normalized_symbol} 的缓存")
        else:
            self._quote_cache.clear()
            self._financials_cache.clear()
            self._news_cache.clear()
            self._indicators_cache.clear()
            logger.info("已清除所有缓存")
