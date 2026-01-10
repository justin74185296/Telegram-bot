# -*- coding: utf-8 -*-
"""
Telegram Bot 命令和消息处理器
处理用户交互并协调数据获取与报告生成
"""

import asyncio
import re
from typing import Optional
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import settings
from core import StockDataProvider, FinancialAnalyzer, StockReportEngine
from utils import get_logger
from .keyboards import (
    InlineKeyboardBuilder,
    get_similar_stocks,
    POPULAR_STOCKS
)

# 获取日志记录器
logger = get_logger(__name__)


class BotHandlers:
    """
    Bot 处理器类
    管理所有命令和回调处理逻辑
    """
    
    def __init__(self):
        """初始化处理器，创建核心服务实例"""
        self.data_provider = StockDataProvider()
        self.analyzer = FinancialAnalyzer()
        self.report_engine = StockReportEngine()
        
        # 用于跟踪正在处理的请求，避免重复
        self._processing = set()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /start 命令
        发送欢迎信息和功能介绍
        """
        welcome_message = """
👋 **欢迎使用 StockInsightBot！**

我是您的专业股票分析助手，能够为您提供：

📊 **实时行情** - 获取股票最新价格和涨跌情况
📈 **财务分析** - 深度解析公司财务数据
📰 **新闻整合** - 汇总近期相关新闻动态
🔮 **专业报告** - AI生成投资分析报告

━━━━━━━━━━━━━━━

**快速开始：**
发送 `/analyze 股票代码` 获取分析报告

**示例：**
• `/analyze TSLA` - 分析特斯拉
• `/analyze AAPL` - 分析苹果
• `/analyze 600519` - 分析贵州茅台（A股）

━━━━━━━━━━━━━━━

💡 输入 /help 查看完整命令列表
"""
        await update.message.reply_text(
            welcome_message,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardBuilder.build_help_keyboard()
        )
        logger.info(f"用户 {update.effective_user.id} 启动了机器人")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /help 命令
        显示详细的使用说明
        """
        help_message = """
📖 **StockInsightBot 使用指南**

━━━━━━━━━━━━━━━

**📌 主要命令**

`/analyze [代码]` - 生成股票深度分析报告
  • 美股：直接输入代码，如 `AAPL`, `TSLA`
  • 港股：添加 `.HK` 后缀，如 `0700.HK`
  • A股：输入6位数字代码，如 `600519`

`/quote [代码]` - 快速获取实时报价

`/news [代码]` - 获取近期新闻

`/help` - 显示此帮助信息

━━━━━━━━━━━━━━━

**🎯 使用示例**

• 分析特斯拉：`/analyze TSLA`
• 分析腾讯：`/analyze 0700.HK`
• 分析茅台：`/analyze 600519`
• 查看英伟达行情：`/quote NVDA`

━━━━━━━━━━━━━━━

**💡 小提示**

1. 报告生成需要10-30秒，请耐心等待
2. 可点击报告下方按钮进行更多操作
3. 数据有5分钟缓存，避免频繁请求

━━━━━━━━━━━━━━━

**热门股票快捷分析 👇**
"""
        await update.message.reply_text(
            help_message,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardBuilder.build_help_keyboard()
        )
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /analyze 命令
        核心功能：获取数据 -> AI分析 -> 推送报告
        """
        # 解析股票代码
        if not context.args:
            await update.message.reply_text(
                "⚠️ 请提供股票代码\n\n"
                "**使用方法：** `/analyze 股票代码`\n\n"
                "**示例：**\n"
                "• `/analyze TSLA` - 特斯拉\n"
                "• `/analyze AAPL` - 苹果\n"
                "• `/analyze 600519` - 贵州茅台",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return
        
        symbol = context.args[0].upper().strip()
        await self._process_analysis(update, symbol)
    
    async def _process_analysis(self, update: Update, symbol: str):
        """
        执行股票分析的核心流程
        
        参数:
            update: Telegram 更新对象
            symbol: 股票代码
        """
        user_id = update.effective_user.id
        request_key = f"{user_id}:{symbol}"
        
        # 检查是否正在处理相同请求
        if request_key in self._processing:
            await self._send_message(
                update,
                "⏳ 该股票正在分析中，请稍候..."
            )
            return
        
        self._processing.add(request_key)
        
        try:
            # 发送处理中提示
            status_message = await self._send_message(
                update,
                f"🔍 **正在获取 {symbol} 的数据并生成分析报告，请稍候...**\n\n"
                "📊 获取实时行情...\n"
                "📈 获取财务数据...\n"
                "📰 获取新闻动态...\n"
                "🤖 AI正在生成报告...",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            
            # 并行获取所有数据
            logger.info(f"开始分析股票 {symbol}，用户 {user_id}")
            
            quote, financials, indicators, news = await asyncio.gather(
                self.data_provider.fetch_realtime_quote(symbol),
                self.data_provider.fetch_financials(symbol),
                self.data_provider.fetch_key_indicators(symbol),
                self.data_provider.fetch_company_news(symbol),
                return_exceptions=True
            )
            
            # 处理获取异常
            if isinstance(quote, Exception):
                logger.error(f"获取 {symbol} 报价失败: {quote}")
                quote = None
            if isinstance(financials, Exception):
                logger.error(f"获取 {symbol} 财务数据失败: {financials}")
                financials = None
            if isinstance(indicators, Exception):
                logger.error(f"获取 {symbol} 指标失败: {indicators}")
                indicators = None
            if isinstance(news, Exception):
                logger.error(f"获取 {symbol} 新闻失败: {news}")
                news = []
            
            # 检查是否获取到基本数据
            if quote is None and indicators is None:
                await self._edit_message(
                    status_message,
                    f"❌ **无法获取 {symbol} 的数据**\n\n"
                    "可能的原因：\n"
                    "• 股票代码不正确\n"
                    "• 该股票暂不支持\n"
                    "• 数据源暂时不可用\n\n"
                    "请检查代码后重试。",
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                return
            
            # 更新状态
            await self._edit_message(
                status_message,
                f"🔍 **{symbol} 数据获取完成**\n\n"
                "✅ 实时行情\n"
                "✅ 财务数据\n"
                "✅ 新闻动态\n"
                "🤖 **AI正在生成深度分析报告...**",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            
            # 执行财务分析
            analysis = self.analyzer.analyze(quote, financials, indicators)
            
            # 生成AI报告
            report = await self.report_engine.generate_report(
                quote, financials, indicators, news, analysis
            )
            
            # 删除状态消息
            try:
                await status_message.delete()
            except Exception:
                pass
            
            # 分割并发送报告
            messages = self.report_engine.split_report(report)
            
            for i, msg in enumerate(messages):
                # 最后一条消息添加操作按钮
                if i == len(messages) - 1:
                    await self._send_message(
                        update,
                        msg,
                        parse_mode=constants.ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardBuilder.build_post_report_keyboard(symbol)
                    )
                else:
                    await self._send_message(
                        update,
                        msg,
                        parse_mode=constants.ParseMode.MARKDOWN
                    )
                    # 避免发送过快
                    await asyncio.sleep(0.5)
            
            logger.info(f"成功生成 {symbol} 分析报告，用户 {user_id}")
            
        except Exception as e:
            logger.error(f"分析 {symbol} 时发生错误: {e}", exc_info=True)
            await self._send_message(
                update,
                f"❌ **分析 {symbol} 时发生错误**\n\n"
                f"错误信息：{str(e)}\n\n"
                "请稍后重试或联系管理员。",
                parse_mode=constants.ParseMode.MARKDOWN
            )
        finally:
            self._processing.discard(request_key)
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /quote 命令
        快速获取股票实时报价
        """
        if not context.args:
            await update.message.reply_text(
                "⚠️ 请提供股票代码\n\n"
                "**示例：** `/quote AAPL`",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        # 发送等待提示
        status_msg = await update.message.reply_text(
            f"🔍 正在获取 {symbol} 实时行情..."
        )
        
        try:
            quote = await self.data_provider.fetch_realtime_quote(symbol)
            
            if quote is None:
                await status_msg.edit_text(
                    f"❌ 无法获取 {symbol} 的行情数据，请检查代码是否正确。"
                )
                return
            
            # 确定涨跌emoji
            if quote.change_percent > 0:
                emoji = "🟢"
                trend = "📈"
            elif quote.change_percent < 0:
                emoji = "🔴"
                trend = "📉"
            else:
                emoji = "⚪"
                trend = "➡️"
            
            message = f"""
{trend} **{quote.name}** ({quote.symbol})

{emoji} **当前价格：** {quote.currency} {quote.current_price:.2f}
📊 **涨跌幅：** {quote.change:+.2f} ({quote.change_percent:+.2f}%)

━━━━━━━━━━━━━━━

📈 **今日区间：** {quote.day_low:.2f} - {quote.day_high:.2f}
📊 **开盘价：** {quote.open_price:.2f}
📊 **昨收价：** {quote.previous_close:.2f}
📊 **成交量：** {self._format_number(quote.volume)}
"""
            
            if quote.market_cap:
                message += f"💰 **市值：** {self._format_market_cap(quote.market_cap)}\n"
            
            if quote.fifty_two_week_high and quote.fifty_two_week_low:
                message += f"📅 **52周区间：** {quote.fifty_two_week_low:.2f} - {quote.fifty_two_week_high:.2f}\n"
            
            message += f"\n_数据更新时间：{quote.timestamp.strftime('%Y-%m-%d %H:%M')}_"
            
            await status_msg.edit_text(
                message,
                parse_mode=constants.ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"获取 {symbol} 报价失败: {e}")
            await status_msg.edit_text(f"❌ 获取行情时发生错误：{str(e)}")
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str = None):
        """
        处理 /news 命令
        获取股票近期新闻，并翻译成中文
        
        参数:
            symbol: 可选，直接传入股票代码（用于回调处理）
        """
        # 获取股票代码
        if symbol is None:
            if not context.args:
                await self._send_message(
                    update,
                    "⚠️ 请提供股票代码\n\n"
                    "**示例：** `/news TSLA`",
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                return
            symbol = context.args[0].upper().strip()
        
        status_msg = await self._send_message(
            update,
            f"📰 正在获取 {symbol} 相关新闻并翻译成中文..."
        )
        
        try:
            news = await self.data_provider.fetch_company_news(symbol, limit=5)
            
            if not news:
                await self._edit_message(
                    status_msg,
                    f"📰 {symbol} 近期暂无相关新闻"
                )
                return
            
            # 构建新闻列表用于翻译
            news_text = ""
            for i, item in enumerate(news, 1):
                news_text += f"{i}. 标题: {item.title}\n"
                if item.summary:
                    news_text += f"   摘要: {item.summary[:200]}\n"
                news_text += "\n"
            
            # 更新状态
            await self._edit_message(
                status_msg,
                f"📰 正在将 {symbol} 新闻翻译成中文...",
            )
            
            # 使用 AI 翻译新闻
            translated = await self._translate_news(news_text, symbol)
            
            # 添加时间和来源信息
            message = f"📰 **{symbol} 近期新闻（中文翻译）**\n\n"
            message += translated
            message += "\n\n---\n"
            
            # 添加原始来源信息
            message += "_来源：_"
            sources = list(set([item.source for item in news if item.source]))
            message += ", ".join(sources[:3]) if sources else "Yahoo Finance"
            
            await self._edit_message(
                status_msg,
                message,
                parse_mode=constants.ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"获取 {symbol} 新闻失败: {e}")
            await self._edit_message(status_msg, f"❌ 获取新闻时发生错误：{str(e)}")
    
    async def _translate_news(self, news_text: str, symbol: str) -> str:
        """
        使用 AI 翻译新闻内容为中文
        
        参数:
            news_text: 英文新闻文本
            symbol: 股票代码
        返回:
            翻译后的中文文本
        """
        try:
            from openai import AsyncOpenAI
            from config import settings
            
            client_kwargs = {"api_key": settings.openai_api_key}
            if settings.openai_api_base:
                client_kwargs["base_url"] = settings.openai_api_base
            
            client = AsyncOpenAI(**client_kwargs)
            
            prompt = f"""请将以下关于 {symbol} 的英文新闻翻译成中文，保持新闻的专业性和准确性。

要求：
1. 保持原有的编号格式
2. 标题要简洁有力
3. 摘要翻译要通顺易懂
4. 专业术语保持准确

原文：
{news_text}

请直接输出翻译结果，格式如下：
**1. [中文标题]**
   [中文摘要]

**2. [中文标题]**
   [中文摘要]
...
"""
            
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是一位专业的财经新闻翻译，擅长将英文财经新闻准确翻译成中文。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"翻译新闻失败: {e}")
            # 如果翻译失败，返回原文
            return f"（翻译失败，显示原文）\n\n{news_text}"
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理内联键盘回调
        """
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # 解析回调数据
        if data.startswith("analyze:"):
            symbol = data.split(":")[1]
            await self._process_analysis(update, symbol)
        
        elif data.startswith("refresh:"):
            symbol = data.split(":")[1]
            await query.message.reply_text(f"🔄 正在刷新 {symbol} 的分析报告...")
            await self._process_analysis(update, symbol)
        
        elif data.startswith("financials:"):
            symbol = data.split(":")[1]
            await self._show_detailed_financials(update, symbol)
        
        elif data.startswith("news:"):
            symbol = data.split(":")[1]
            # 直接传入股票代码
            await self.news_command(update, context, symbol=symbol)
        
        elif data.startswith("compare:"):
            symbol = data.split(":")[1]
            similar = get_similar_stocks(symbol)
            await query.message.reply_text(
                f"📊 **{symbol} 的同类/相关股票**\n\n"
                "点击下方按钮快速分析：",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardBuilder.build_similar_stocks_keyboard(similar)
            )
        
        elif data == "guide":
            await query.message.reply_text(
                "📖 **详细使用指南**\n\n"
                "**股票代码格式：**\n"
                "• 美股：直接输入，如 `AAPL`, `TSLA`, `NVDA`\n"
                "• 港股：添加 `.HK`，如 `0700.HK`, `9988.HK`\n"
                "• A股：6位代码，如 `600519`, `000858`\n\n"
                "**报告内容说明：**\n"
                "• 即时快照：当前股价和市场情绪\n"
                "• 财务解析：季度财务趋势分析\n"
                "• 动态集成：近期新闻影响评估\n"
                "• 展望评估：上行驱动与下行风险\n"
                "• 核心结论：3点关键总结\n\n"
                "**注意事项：**\n"
                "• 报告仅供参考，不构成投资建议\n"
                "• 数据可能有延迟，请以官方数据为准",
                parse_mode=constants.ParseMode.MARKDOWN
            )
        
        elif data == "cancel":
            await query.message.edit_text("❌ 操作已取消")
        
        elif data == "noop":
            pass  # 无操作
    
    async def _show_detailed_financials(self, update: Update, symbol: str):
        """
        显示详细财务数据
        """
        query = update.callback_query
        
        status_msg = await query.message.reply_text(
            f"📊 正在获取 {symbol} 详细财务数据..."
        )
        
        try:
            financials = await self.data_provider.fetch_financials(symbol)
            indicators = await self.data_provider.fetch_key_indicators(symbol)
            
            if not financials and not indicators:
                await status_msg.edit_text(
                    f"❌ 无法获取 {symbol} 的财务数据"
                )
                return
            
            message = f"📊 **{symbol} 详细财务指标**\n\n"
            
            if indicators:
                message += "**估值指标：**\n"
                if indicators.pe_ratio:
                    message += f"• 市盈率(PE): {indicators.pe_ratio:.2f}\n"
                if indicators.pb_ratio:
                    message += f"• 市净率(PB): {indicators.pb_ratio:.2f}\n"
                if indicators.ps_ratio:
                    message += f"• 市销率(PS): {indicators.ps_ratio:.2f}\n"
                if indicators.peg_ratio:
                    message += f"• PEG比率: {indicators.peg_ratio:.2f}\n"
                
                message += "\n**盈利能力：**\n"
                if indicators.roe:
                    roe = indicators.roe * 100 if indicators.roe < 1 else indicators.roe
                    message += f"• ROE: {roe:.2f}%\n"
                if indicators.profit_margin:
                    margin = indicators.profit_margin * 100 if indicators.profit_margin < 1 else indicators.profit_margin
                    message += f"• 净利润率: {margin:.2f}%\n"
                if indicators.gross_margin:
                    gross = indicators.gross_margin * 100 if indicators.gross_margin < 1 else indicators.gross_margin
                    message += f"• 毛利率: {gross:.2f}%\n"
                
                message += "\n**财务健康：**\n"
                if indicators.debt_to_equity:
                    message += f"• 负债权益比: {indicators.debt_to_equity:.2f}\n"
                if indicators.current_ratio:
                    message += f"• 流动比率: {indicators.current_ratio:.2f}\n"
                
                message += "\n**成长性：**\n"
                if indicators.revenue_growth:
                    rev = indicators.revenue_growth * 100 if abs(indicators.revenue_growth) < 10 else indicators.revenue_growth
                    message += f"• 营收增长: {rev:+.2f}%\n"
                if indicators.earnings_growth:
                    earn = indicators.earnings_growth * 100 if abs(indicators.earnings_growth) < 10 else indicators.earnings_growth
                    message += f"• 盈利增长: {earn:+.2f}%\n"
            
            await status_msg.edit_text(
                message,
                parse_mode=constants.ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"获取 {symbol} 财务数据失败: {e}")
            await status_msg.edit_text(f"❌ 获取财务数据时发生错误：{str(e)}")
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理普通文本消息
        尝试识别股票代码并提供快速查询
        """
        text = update.message.text.strip().upper()
        
        # 简单的股票代码模式匹配
        # 美股：1-5个字母
        # A股：6位数字
        # 港股：1-5位数字或带.HK后缀
        
        us_pattern = r'^[A-Z]{1,5}$'
        cn_pattern = r'^[036]\d{5}$'
        hk_pattern = r'^(\d{1,5})(\.HK)?$'
        
        symbol = None
        
        if re.match(us_pattern, text):
            symbol = text
        elif re.match(cn_pattern, text):
            symbol = text
        elif re.match(hk_pattern, text):
            symbol = text if text.endswith('.HK') else f"{text}.HK"
        
        if symbol:
            await update.message.reply_text(
                f"🔍 检测到股票代码 **{symbol}**\n\n"
                f"点击下方按钮获取分析报告：",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardBuilder.build_similar_stocks_keyboard([symbol])
            )
        else:
            await update.message.reply_text(
                "👋 您好！我是股票分析助手。\n\n"
                "请使用以下命令：\n"
                "• `/analyze 代码` - 获取深度分析\n"
                "• `/quote 代码` - 获取实时行情\n"
                "• `/help` - 查看帮助\n\n"
                "或直接输入股票代码试试！",
                parse_mode=constants.ParseMode.MARKDOWN
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        全局错误处理
        """
        logger.error(f"处理更新时发生错误: {context.error}", exc_info=context.error)
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ 处理您的请求时发生错误，请稍后重试。"
            )
    
    async def _send_message(self, update: Update, text: str, **kwargs):
        """
        统一的消息发送方法
        自动处理不同来源的消息
        """
        if update.callback_query:
            return await update.callback_query.message.reply_text(text, **kwargs)
        else:
            return await update.message.reply_text(text, **kwargs)
    
    async def _edit_message(self, message, text: str, **kwargs):
        """
        编辑消息的辅助方法
        """
        try:
            await message.edit_text(text, **kwargs)
        except Exception as e:
            logger.warning(f"编辑消息失败: {e}")
    
    @staticmethod
    def _format_number(num: Optional[int]) -> str:
        """格式化数字显示"""
        if num is None:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        if num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        if num >= 1_000:
            return f"{num / 1_000:.2f}K"
        return f"{num:,}"
    
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


def setup_handlers(application: Application) -> None:
    """
    设置所有处理器到 Application
    
    参数:
        application: Telegram Bot Application 实例
    """
    handlers = BotHandlers()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("analyze", handlers.analyze_command))
    application.add_handler(CommandHandler("quote", handlers.quote_command))
    application.add_handler(CommandHandler("news", handlers.news_command))
    
    # 注册回调处理器
    application.add_handler(CallbackQueryHandler(handlers.callback_handler))
    
    # 注册文本消息处理器（最后添加，作为fallback）
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )
    
    # 注册错误处理器
    application.add_error_handler(handlers.error_handler)
    
    logger.info("所有处理器已注册")
