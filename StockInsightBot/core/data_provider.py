# -*- coding: utf-8 -*-
"""
数据提供模块
统一封装 yfinance 和 akshare 的数据获取接口
支持美股、港股、A股等多市场数据
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from cachetools import TTLCache
import pandas as pd
import numpy as np

# 数据源导入
import yfinance as yf

# 尝试导入 akshare（A股/港股数据备选）
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

from config import settings


@dataclass
class StockQuote:
    """股票实时报价数据结构"""
    symbol: str                          # 股票代码
    name: str                            # 公司名称
    current_price: float                 # 当前价格
    previous_close: float                # 前收盘价
    open_price: float                    # 开盘价
    day_high: float                      # 日最高价
    day_low: float                       # 日最低价
    volume: int                          # 成交量
    market_cap: Optional[float] = None   # 市值
    change: float = 0.0                  # 涨跌额
    change_percent: float = 0.0          # 涨跌幅(%)
    fifty_two_week_high: Optional[float] = None  # 52周最高
    fifty_two_week_low: Optional[float] = None   # 52周最低
    avg_volume: Optional[int] = None     # 平均成交量
    currency: str = "USD"                # 货币单位
    exchange: str = ""                   # 交易所
    timestamp: datetime = field(default_factory=datetime.now)  # 数据时间戳


@dataclass 
class FinancialData:
    """财务数据结构"""
    symbol: str
    # 利润表关键数据
    revenue: List[Dict[str, Any]] = field(default_factory=list)           # 营收
    net_income: List[Dict[str, Any]] = field(default_factory=list)        # 净利润
    gross_profit: List[Dict[str, Any]] = field(default_factory=list)      # 毛利润
    operating_income: List[Dict[str, Any]] = field(default_factory=list)  # 营业利润
    
    # 资产负债表关键数据
    total_assets: List[Dict[str, Any]] = field(default_factory=list)      # 总资产
    total_liabilities: List[Dict[str, Any]] = field(default_factory=list) # 总负债
    total_equity: List[Dict[str, Any]] = field(default_factory=list)      # 股东权益
    cash_and_equivalents: List[Dict[str, Any]] = field(default_factory=list)  # 现金及等价物
    
    # 现金流量表关键数据
    operating_cash_flow: List[Dict[str, Any]] = field(default_factory=list)   # 经营活动现金流
    investing_cash_flow: List[Dict[str, Any]] = field(default_factory=list)   # 投资活动现金流
    financing_cash_flow: List[Dict[str, Any]] = field(default_factory=list)   # 筹资活动现金流
    free_cash_flow: List[Dict[str, Any]] = field(default_factory=list)        # 自由现金流


@dataclass
class KeyIndicators:
    """关键财务指标"""
    symbol: str
    pe_ratio: Optional[float] = None          # 市盈率
    forward_pe: Optional[float] = None        # 预测市盈率
    pb_ratio: Optional[float] = None          # 市净率
    ps_ratio: Optional[float] = None          # 市销率
    peg_ratio: Optional[float] = None         # PEG比率
    roe: Optional[float] = None               # 净资产收益率
    roa: Optional[float] = None               # 总资产收益率
    profit_margin: Optional[float] = None     # 净利润率
    operating_margin: Optional[float] = None  # 营业利润率
    gross_margin: Optional[float] = None      # 毛利率
    debt_to_equity: Optional[float] = None    # 资产负债率
    current_ratio: Optional[float] = None     # 流动比率
    quick_ratio: Optional[float] = None       # 速动比率
    dividend_yield: Optional[float] = None    # 股息率
    dividend_rate: Optional[float] = None     # 每股股息
    beta: Optional[float] = None              # Beta系数
    eps: Optional[float] = None               # 每股收益
    revenue_growth: Optional[float] = None    # 营收增长率
    earnings_growth: Optional[float] = None   # 盈利增长率


@dataclass
class NewsItem:
    """新闻条目"""
    title: str                     # 标题
    summary: str = ""              # 摘要
    link: str = ""                 # 链接
    published: Optional[datetime] = None  # 发布时间
    source: str = ""               # 来源


class StockDataProvider:
    """
    股票数据提供类
    统一封装多数据源的股票数据获取
    
    特性:
    - 内置TTL缓存，避免频繁API调用
    - 支持美股(yfinance)和A股/港股(akshare)
    - 自动数据源降级处理
    """
    
    def __init__(self):
        """初始化数据提供器，设置缓存"""
        # 创建TTL缓存，设置过期时间和最大容量
        self._cache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl
        )
        
    def _get_cache_key(self, operation: str, symbol: str) -> str:
        """
        生成缓存键
        
        参数:
            operation: 操作类型（如 quote, financials）
            symbol: 股票代码
        返回:
            缓存键字符串
        """
        return f"{operation}:{symbol.upper()}"
    
    def _normalize_symbol(self, symbol: str) -> tuple[str, str]:
        """
        标准化股票代码并判断市场
        
        参数:
            symbol: 原始股票代码
        返回:
            tuple: (标准化代码, 市场类型)
            市场类型: 'us' (美股), 'hk' (港股), 'cn' (A股)
        """
        symbol = symbol.upper().strip()
        
        # A股判断：纯数字6位或带后缀
        if symbol.isdigit() and len(symbol) == 6:
            # 根据代码判断沪深
            if symbol.startswith(('6', '9')):
                return f"{symbol}.SS", "cn"  # 上海
            else:
                return f"{symbol}.SZ", "cn"  # 深圳
        
        # 港股判断：数字开头或.HK后缀
        if symbol.endswith('.HK'):
            return symbol, "hk"
        if symbol.isdigit() and len(symbol) <= 5:
            return f"{symbol.zfill(4)}.HK", "hk"
        
        # 默认作为美股处理
        return symbol, "us"
    
    async def fetch_realtime_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        获取股票实时报价
        
        参数:
            symbol: 股票代码（如 TSLA, AAPL, 600519）
        返回:
            StockQuote 对象，失败返回 None
        """
        cache_key = self._get_cache_key("quote", symbol)
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        normalized_symbol, market = self._normalize_symbol(symbol)
        
        try:
            # 使用 yfinance 获取数据（在线程池中运行同步代码）
            quote = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_quote_yfinance, normalized_symbol
            )
            
            if quote:
                self._cache[cache_key] = quote
                return quote
            
            # yfinance 失败时尝试 akshare（仅限A股/港股）
            if AKSHARE_AVAILABLE and market in ("cn", "hk"):
                quote = await asyncio.get_event_loop().run_in_executor(
                    None, self._fetch_quote_akshare, symbol, market
                )
                if quote:
                    self._cache[cache_key] = quote
                    return quote
                    
        except Exception as e:
            print(f"[DataProvider] 获取报价失败 {symbol}: {e}")
        
        return None
    
    def _fetch_quote_yfinance(self, symbol: str) -> Optional[StockQuote]:
        """
        使用 yfinance 获取报价（同步方法）
        
        参数:
            symbol: 标准化后的股票代码
        返回:
            StockQuote 对象
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 检查是否获取到有效数据
            if not info or info.get("regularMarketPrice") is None:
                # 尝试获取历史数据作为备选
                hist = ticker.history(period="1d")
                if hist.empty:
                    return None
                
                current_price = float(hist['Close'].iloc[-1])
                previous_close = float(hist['Open'].iloc[0]) if len(hist) > 0 else current_price
                open_price = float(hist['Open'].iloc[-1]) if 'Open' in hist else current_price
                day_high = float(hist['High'].iloc[-1]) if 'High' in hist else current_price
                day_low = float(hist['Low'].iloc[-1]) if 'Low' in hist else current_price
                volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
                
                return StockQuote(
                    symbol=symbol,
                    name=info.get("shortName", symbol),
                    current_price=current_price,
                    previous_close=previous_close,
                    open_price=open_price,
                    day_high=day_high,
                    day_low=day_low,
                    volume=volume,
                    change=current_price - previous_close,
                    change_percent=((current_price - previous_close) / previous_close * 100) if previous_close else 0,
                    currency=info.get("currency", "USD"),
                    exchange=info.get("exchange", "")
                )
            
            # 从 info 中提取数据
            current_price = info.get("regularMarketPrice", 0) or info.get("currentPrice", 0)
            previous_close = info.get("regularMarketPreviousClose", 0) or info.get("previousClose", 0)
            
            return StockQuote(
                symbol=symbol,
                name=info.get("shortName") or info.get("longName", symbol),
                current_price=float(current_price) if current_price else 0,
                previous_close=float(previous_close) if previous_close else 0,
                open_price=float(info.get("regularMarketOpen", 0) or info.get("open", 0)),
                day_high=float(info.get("regularMarketDayHigh", 0) or info.get("dayHigh", 0)),
                day_low=float(info.get("regularMarketDayLow", 0) or info.get("dayLow", 0)),
                volume=int(info.get("regularMarketVolume", 0) or info.get("volume", 0)),
                market_cap=float(info.get("marketCap", 0)) if info.get("marketCap") else None,
                change=float(info.get("regularMarketChange", 0)) if info.get("regularMarketChange") else (current_price - previous_close if current_price and previous_close else 0),
                change_percent=float(info.get("regularMarketChangePercent", 0) * 100) if info.get("regularMarketChangePercent") else ((current_price - previous_close) / previous_close * 100 if previous_close else 0),
                fifty_two_week_high=float(info.get("fiftyTwoWeekHigh", 0)) if info.get("fiftyTwoWeekHigh") else None,
                fifty_two_week_low=float(info.get("fiftyTwoWeekLow", 0)) if info.get("fiftyTwoWeekLow") else None,
                avg_volume=int(info.get("averageVolume", 0)) if info.get("averageVolume") else None,
                currency=info.get("currency", "USD"),
                exchange=info.get("exchange", "")
            )
            
        except Exception as e:
            print(f"[yfinance] 获取 {symbol} 报价失败: {e}")
            return None
    
    def _fetch_quote_akshare(self, symbol: str, market: str) -> Optional[StockQuote]:
        """
        使用 akshare 获取A股/港股报价（同步方法）
        
        参数:
            symbol: 原始股票代码
            market: 市场类型 ('cn' 或 'hk')
        返回:
            StockQuote 对象
        """
        if not AKSHARE_AVAILABLE:
            return None
            
        try:
            if market == "cn":
                # A股实时行情
                df = ak.stock_zh_a_spot_em()
                # 根据代码过滤
                code = symbol.replace('.SS', '').replace('.SZ', '').strip()
                row = df[df['代码'] == code]
                
                if row.empty:
                    return None
                
                row = row.iloc[0]
                return StockQuote(
                    symbol=symbol,
                    name=row.get('名称', symbol),
                    current_price=float(row.get('最新价', 0)),
                    previous_close=float(row.get('昨收', 0)),
                    open_price=float(row.get('今开', 0)),
                    day_high=float(row.get('最高', 0)),
                    day_low=float(row.get('最低', 0)),
                    volume=int(float(row.get('成交量', 0))),
                    market_cap=float(row.get('总市值', 0)) if row.get('总市值') else None,
                    change=float(row.get('涨跌额', 0)),
                    change_percent=float(row.get('涨跌幅', 0)),
                    currency="CNY",
                    exchange="SSE" if symbol.endswith('.SS') else "SZSE"
                )
                
            elif market == "hk":
                # 港股实时行情
                df = ak.stock_hk_spot_em()
                code = symbol.replace('.HK', '').strip()
                row = df[df['代码'] == code]
                
                if row.empty:
                    return None
                
                row = row.iloc[0]
                return StockQuote(
                    symbol=symbol,
                    name=row.get('名称', symbol),
                    current_price=float(row.get('最新价', 0)),
                    previous_close=float(row.get('昨收', 0)),
                    open_price=float(row.get('今开', 0)),
                    day_high=float(row.get('最高', 0)),
                    day_low=float(row.get('最低', 0)),
                    volume=int(float(row.get('成交量', 0))),
                    market_cap=float(row.get('总市值', 0)) if row.get('总市值') else None,
                    change=float(row.get('涨跌额', 0)),
                    change_percent=float(row.get('涨跌幅', 0)),
                    currency="HKD",
                    exchange="HKEX"
                )
                
        except Exception as e:
            print(f"[akshare] 获取 {symbol} 报价失败: {e}")
        
        return None
    
    async def fetch_financials(self, symbol: str) -> Optional[FinancialData]:
        """
        获取财务报表数据（近4个季度）
        
        参数:
            symbol: 股票代码
        返回:
            FinancialData 对象
        """
        cache_key = self._get_cache_key("financials", symbol)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        normalized_symbol, _ = self._normalize_symbol(symbol)
        
        try:
            financials = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_financials_yfinance, normalized_symbol
            )
            
            if financials:
                self._cache[cache_key] = financials
                return financials
                
        except Exception as e:
            print(f"[DataProvider] 获取财务数据失败 {symbol}: {e}")
        
        return None
    
    def _fetch_financials_yfinance(self, symbol: str) -> Optional[FinancialData]:
        """
        使用 yfinance 获取财务数据（同步方法）
        
        参数:
            symbol: 标准化后的股票代码
        返回:
            FinancialData 对象
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # 获取季度财务报表
            income_stmt = ticker.quarterly_income_stmt
            balance_sheet = ticker.quarterly_balance_sheet
            cash_flow = ticker.quarterly_cashflow
            
            financial_data = FinancialData(symbol=symbol)
            
            # 处理利润表数据
            if income_stmt is not None and not income_stmt.empty:
                for col in income_stmt.columns[:4]:  # 最近4个季度
                    date_str = col.strftime("%Y-Q%q") if hasattr(col, 'strftime') else str(col)[:10]
                    
                    if 'Total Revenue' in income_stmt.index:
                        financial_data.revenue.append({
                            "date": date_str,
                            "value": self._safe_float(income_stmt.loc['Total Revenue', col])
                        })
                    
                    if 'Net Income' in income_stmt.index:
                        financial_data.net_income.append({
                            "date": date_str,
                            "value": self._safe_float(income_stmt.loc['Net Income', col])
                        })
                    
                    if 'Gross Profit' in income_stmt.index:
                        financial_data.gross_profit.append({
                            "date": date_str,
                            "value": self._safe_float(income_stmt.loc['Gross Profit', col])
                        })
                    
                    if 'Operating Income' in income_stmt.index:
                        financial_data.operating_income.append({
                            "date": date_str,
                            "value": self._safe_float(income_stmt.loc['Operating Income', col])
                        })
            
            # 处理资产负债表数据
            if balance_sheet is not None and not balance_sheet.empty:
                for col in balance_sheet.columns[:4]:
                    date_str = col.strftime("%Y-Q%q") if hasattr(col, 'strftime') else str(col)[:10]
                    
                    if 'Total Assets' in balance_sheet.index:
                        financial_data.total_assets.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Total Assets', col])
                        })
                    
                    if 'Total Liabilities Net Minority Interest' in balance_sheet.index:
                        financial_data.total_liabilities.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Total Liabilities Net Minority Interest', col])
                        })
                    elif 'Total Liab' in balance_sheet.index:
                        financial_data.total_liabilities.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Total Liab', col])
                        })
                    
                    if 'Stockholders Equity' in balance_sheet.index:
                        financial_data.total_equity.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Stockholders Equity', col])
                        })
                    elif 'Total Stockholder Equity' in balance_sheet.index:
                        financial_data.total_equity.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Total Stockholder Equity', col])
                        })
                    
                    if 'Cash And Cash Equivalents' in balance_sheet.index:
                        financial_data.cash_and_equivalents.append({
                            "date": date_str,
                            "value": self._safe_float(balance_sheet.loc['Cash And Cash Equivalents', col])
                        })
            
            # 处理现金流量表数据
            if cash_flow is not None and not cash_flow.empty:
                for col in cash_flow.columns[:4]:
                    date_str = col.strftime("%Y-Q%q") if hasattr(col, 'strftime') else str(col)[:10]
                    
                    if 'Operating Cash Flow' in cash_flow.index:
                        financial_data.operating_cash_flow.append({
                            "date": date_str,
                            "value": self._safe_float(cash_flow.loc['Operating Cash Flow', col])
                        })
                    
                    if 'Investing Cash Flow' in cash_flow.index:
                        financial_data.investing_cash_flow.append({
                            "date": date_str,
                            "value": self._safe_float(cash_flow.loc['Investing Cash Flow', col])
                        })
                    
                    if 'Financing Cash Flow' in cash_flow.index:
                        financial_data.financing_cash_flow.append({
                            "date": date_str,
                            "value": self._safe_float(cash_flow.loc['Financing Cash Flow', col])
                        })
                    
                    if 'Free Cash Flow' in cash_flow.index:
                        financial_data.free_cash_flow.append({
                            "date": date_str,
                            "value": self._safe_float(cash_flow.loc['Free Cash Flow', col])
                        })
            
            return financial_data
            
        except Exception as e:
            print(f"[yfinance] 获取 {symbol} 财务数据失败: {e}")
            return None
    
    async def fetch_key_indicators(self, symbol: str) -> Optional[KeyIndicators]:
        """
        获取关键财务指标
        
        参数:
            symbol: 股票代码
        返回:
            KeyIndicators 对象
        """
        cache_key = self._get_cache_key("indicators", symbol)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        normalized_symbol, _ = self._normalize_symbol(symbol)
        
        try:
            indicators = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_indicators_yfinance, normalized_symbol
            )
            
            if indicators:
                self._cache[cache_key] = indicators
                return indicators
                
        except Exception as e:
            print(f"[DataProvider] 获取指标失败 {symbol}: {e}")
        
        return None
    
    def _fetch_indicators_yfinance(self, symbol: str) -> Optional[KeyIndicators]:
        """
        使用 yfinance 获取关键指标（同步方法）
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return KeyIndicators(
                symbol=symbol,
                pe_ratio=self._safe_float(info.get('trailingPE')),
                forward_pe=self._safe_float(info.get('forwardPE')),
                pb_ratio=self._safe_float(info.get('priceToBook')),
                ps_ratio=self._safe_float(info.get('priceToSalesTrailing12Months')),
                peg_ratio=self._safe_float(info.get('pegRatio')),
                roe=self._safe_float(info.get('returnOnEquity')),
                roa=self._safe_float(info.get('returnOnAssets')),
                profit_margin=self._safe_float(info.get('profitMargins')),
                operating_margin=self._safe_float(info.get('operatingMargins')),
                gross_margin=self._safe_float(info.get('grossMargins')),
                debt_to_equity=self._safe_float(info.get('debtToEquity')),
                current_ratio=self._safe_float(info.get('currentRatio')),
                quick_ratio=self._safe_float(info.get('quickRatio')),
                dividend_yield=self._safe_float(info.get('dividendYield')),
                dividend_rate=self._safe_float(info.get('dividendRate')),
                beta=self._safe_float(info.get('beta')),
                eps=self._safe_float(info.get('trailingEps')),
                revenue_growth=self._safe_float(info.get('revenueGrowth')),
                earnings_growth=self._safe_float(info.get('earningsGrowth'))
            )
            
        except Exception as e:
            print(f"[yfinance] 获取 {symbol} 指标失败: {e}")
            return None
    
    async def fetch_company_news(self, symbol: str, limit: int = None) -> List[NewsItem]:
        """
        获取公司相关新闻
        
        参数:
            symbol: 股票代码
            limit: 新闻条数限制，默认使用配置值
        返回:
            新闻列表
        """
        if limit is None:
            limit = settings.news_limit
            
        cache_key = self._get_cache_key(f"news:{limit}", symbol)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        normalized_symbol, _ = self._normalize_symbol(symbol)
        
        try:
            news = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_news_yfinance, normalized_symbol, limit
            )
            
            self._cache[cache_key] = news
            return news
            
        except Exception as e:
            print(f"[DataProvider] 获取新闻失败 {symbol}: {e}")
            return []
    
    def _fetch_news_yfinance(self, symbol: str, limit: int) -> List[NewsItem]:
        """
        使用 yfinance 获取新闻（同步方法）
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            result = []
            for item in news[:limit]:
                published_time = None
                if item.get('providerPublishTime'):
                    published_time = datetime.fromtimestamp(item['providerPublishTime'])
                
                result.append(NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('summary', '') if item.get('summary') else '',
                    link=item.get('link', ''),
                    published=published_time,
                    source=item.get('publisher', '')
                ))
            
            return result
            
        except Exception as e:
            print(f"[yfinance] 获取 {symbol} 新闻失败: {e}")
            return []
    
    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """
        安全转换为浮点数
        
        参数:
            value: 待转换的值
        返回:
            浮点数或 None
        """
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    return None
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        返回:
            包含缓存大小和配置的字典
        """
        return {
            "current_size": len(self._cache),
            "max_size": self._cache.maxsize,
            "ttl": self._cache.ttl
        }
