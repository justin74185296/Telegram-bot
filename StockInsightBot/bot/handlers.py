"""
Telegram Bot 命令和消息处理器
处理用户交互，协调数据获取和报告生成
"""

import logging
from typing import Optional
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from core.data_provider import StockDataProvider
from core.financial_analyzer import FinancialAnalyzer
from core.report_engine import StockReportEngine
from .keyboards import (
    create_main_menu_keyboard,
    create_report_keyboard,
    create_popular_stocks_keyboard
)

logger = logging.getLogger(__name__)

# 全局服务实例
data_provider: Optional[StockDataProvider] = None
analyzer: Optional[FinancialAnalyzer] = None
report_engine: Optional[StockReportEngine] = None


def init_services():
    """初始化所有服务"""
    global data_provider, analyzer, report_engine
    data_provider = StockDataProvider()
    analyzer = FinancialAnalyzer()
    report_engine = StockReportEngine()
    logger.info("所有服务初始化完成")


# ==================== 命令处理器 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /start 命令
    发送欢迎信息和功能介绍
    """
    user = update.effective_user
    welcome_message = f"""
👋 **欢迎使用 StockInsightBot！**

你好，{user.first_name}！我是你的专业股票分析助手。

🎯 **我能做什么：**
• 获取全球股票实时行情
• 分析公司财务数据
• 生成AI驱动的投资分析报告
• 整合最新市场新闻

📝 **快速开始：**
发送 `/analyze TSLA` 分析特斯拉
发送 `/analyze AAPL` 分析苹果
发送 `/analyze 0700.HK` 分析腾讯

💡 **支持市场：**
• 美股：直接输入代码 (AAPL, TSLA)
• 港股：代码.HK (0700.HK, 9988.HK)
• A股：代码.SS/.SZ (600519.SS, 000858.SZ)

输入 /help 查看完整帮助
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=create_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /help 命令
    显示详细使用说明
    """
    help_text = """
📖 **StockInsightBot 使用指南**

━━━━━━━━━━━━━━━━━━━━━━

**📊 分析命令**

`/analyze <股票代码>`
生成完整的AI分析报告

示例：
• `/analyze TSLA` - 分析特斯拉
• `/analyze NVDA` - 分析英伟达
• `/analyze 0700.HK` - 分析腾讯
• `/analyze 600519.SS` - 分析贵州茅台

━━━━━━━━━━━━━━━━━━━━━━

**🔍 股票代码格式**

| 市场 | 格式 | 示例 |
|------|------|------|
| 美股 | 代码 | AAPL, TSLA |
| 港股 | 代码.HK | 0700.HK |
| 上证 | 代码.SS | 600519.SS |
| 深证 | 代码.SZ | 000858.SZ |

━━━━━━━━━━━━━━━━━━━━━━

**📈 报告内容**

每份报告包含：
✅ 即时行情快照
✅ 财务深度解析
✅ 近期新闻整合
✅ 未来展望与风险
✅ 核心投资结论

━━━━━━━━━━━━━━━━━━━━━━

**⚡ 其他命令**

`/start` - 重新开始
`/help` - 显示此帮助

━━━━━━━━━━━━━━━━━━━━━━

💬 直接发送股票代码也可以快速分析！
"""
    await update.message.reply_text(
        help_text,
        parse_mode=constants.ParseMode.MARKDOWN
    )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /analyze 命令
    核心命令：获取数据 -> AI分析 -> 推送报告
    """
    # 检查是否提供了股票代码
    if not context.args:
        await update.message.reply_text(
            "⚠️ 请提供股票代码\n\n"
            "用法: `/analyze <股票代码>`\n"
            "示例: `/analyze TSLA`",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        return
    
    symbol = context.args[0].upper()
    await process_stock_analysis(update, context, symbol)


async def process_stock_analysis(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    symbol: str,
    edit_message: bool = False
) -> None:
    """
    处理股票分析的核心流程
    
    Args:
        update: Telegram Update
        context: 上下文
        symbol: 股票代码
        edit_message: 是否编辑现有消息（用于回调）
    """
    # 发送等待消息
    if edit_message and update.callback_query:
        wait_message = await update.callback_query.message.edit_text(
            f"🔄 正在获取 **{symbol}** 的数据并生成分析报告，请稍候...\n\n"
            "⏳ 这可能需要15-30秒",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    else:
        wait_message = await update.message.reply_text(
            f"🔄 正在获取 **{symbol}** 的数据并生成分析报告，请稍候...\n\n"
            "⏳ 这可能需要15-30秒",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    
    try:
        # 1. 获取实时报价
        quote = await data_provider.fetch_realtime_quote(symbol)
        if not quote:
            await wait_message.edit_text(
                f"❌ 无法获取 **{symbol}** 的数据\n\n"
                "可能原因：\n"
                "• 股票代码不正确\n"
                "• 该市场暂不支持\n"
                "• 网络连接问题\n\n"
                "请检查代码后重试，或使用 /help 查看支持的格式",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return
        
        # 更新进度
        await wait_message.edit_text(
            f"🔄 正在分析 **{quote.name}** ({symbol})...\n\n"
            f"✅ 实时报价已获取\n"
            f"⏳ 正在获取财务数据...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        # 2. 获取财务数据
        financials = await data_provider.fetch_financials(symbol)
        indicators = await data_provider.fetch_key_indicators(symbol)
        news = await data_provider.fetch_company_news(symbol, limit=5)
        
        if not indicators:
            await wait_message.edit_text(
                f"⚠️ **{symbol}** 的财务数据不完整\n\n"
                "仅能提供基础报价信息",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return
        
        # 更新进度
        await wait_message.edit_text(
            f"🔄 正在生成 **{quote.name}** 的AI分析报告...\n\n"
            f"✅ 实时报价已获取\n"
            f"✅ 财务数据已获取\n"
            f"✅ 新闻数据已获取\n"
            f"⏳ AI正在撰写报告...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        # 3. 生成量化分析
        analysis = await analyzer.generate_full_analysis(quote, indicators, financials)
        
        # 4. 生成AI报告
        report = await report_engine.generate_report(
            quote=quote,
            indicators=indicators,
            analysis=analysis,
            news=news,
            trends=analysis.trends
        )
        
        # 5. 发送报告（处理长消息）
        await send_long_message(
            wait_message,
            report,
            reply_markup=create_report_keyboard(symbol)
        )
        
        logger.info(f"成功为用户 {update.effective_user.id} 生成 {symbol} 分析报告")
        
    except Exception as e:
        logger.error(f"分析 {symbol} 时发生错误: {e}", exc_info=True)
        await wait_message.edit_text(
            f"❌ 分析过程中发生错误\n\n"
            f"错误信息: {str(e)[:200]}\n\n"
            "请稍后重试或联系管理员",
            parse_mode=constants.ParseMode.MARKDOWN
        )


async def send_long_message(
    message,
    text: str,
    reply_markup=None,
    max_length: int = 4000
) -> None:
    """
    发送长消息（自动分割）
    
    Args:
        message: 要编辑的消息对象
        text: 要发送的文本
        reply_markup: 键盘标记
        max_length: 单条消息最大长度
    """
    # Telegram消息限制约4096字符，留一些余量
    if len(text) <= max_length:
        await message.edit_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return
    
    # 分割长消息
    parts = []
    current_part = ""
    
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        if len(current_part) + len(para) + 2 > max_length:
            if current_part:
                parts.append(current_part.strip())
            current_part = para
        else:
            current_part += "\n\n" + para if current_part else para
    
    if current_part:
        parts.append(current_part.strip())
    
    # 发送第一部分（编辑原消息）
    if parts:
        await message.edit_text(
            parts[0] + "\n\n⬇️ *续下文*",
            parse_mode=constants.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        # 发送剩余部分
        chat = message.chat
        for i, part in enumerate(parts[1:], 2):
            is_last = i == len(parts)
            suffix = "" if is_last else "\n\n⬇️ *续下文*"
            markup = reply_markup if is_last else None
            
            await chat.send_message(
                f"*（第{i}部分）*\n\n{part}{suffix}",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=markup,
                disable_web_page_preview=True
            )


# ==================== 回调处理器 ====================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理内联键盘回调
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.debug(f"收到回调: {data}")
    
    # 主菜单操作
    if data == "menu_main":
        await query.message.edit_text(
            "📊 **StockInsightBot 主菜单**\n\n"
            "请选择操作或直接发送股票代码进行分析：",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=create_main_menu_keyboard()
        )
    
    elif data == "menu_analyze":
        await query.message.edit_text(
            "📊 **分析股票**\n\n"
            "请发送股票代码，例如：\n"
            "• `TSLA` - 特斯拉\n"
            "• `AAPL` - 苹果\n"
            "• `0700.HK` - 腾讯\n\n"
            "或点击下方热门股票快速分析：",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=create_popular_stocks_keyboard()
        )
    
    elif data == "menu_help":
        await help_command(update, context)
    
    elif data == "menu_popular":
        await query.message.edit_text(
            "🔥 **热门股票**\n\n"
            "点击下方按钮快速分析：",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=create_popular_stocks_keyboard()
        )
    
    elif data == "menu_market":
        await query.message.edit_text(
            "📈 **市场概览**\n\n"
            "🚧 此功能正在开发中...\n\n"
            "敬请期待！",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=create_main_menu_keyboard()
        )
    
    # 分析特定股票
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await process_stock_analysis(update, context, symbol, edit_message=True)
    
    # 刷新报告
    elif data.startswith("refresh_"):
        symbol = data.replace("refresh_", "")
        # 清除缓存后重新分析
        data_provider.clear_cache(symbol)
        await process_stock_analysis(update, context, symbol, edit_message=True)
    
    # 查看更多新闻
    elif data.startswith("news_"):
        symbol = data.replace("news_", "")
        await show_news(query, symbol)
    
    # 同行对比
    elif data.startswith("peers_"):
        symbol = data.replace("peers_", "")
        await query.message.reply_text(
            f"🏢 **{symbol} 同行对比**\n\n"
            "🚧 此功能正在开发中...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    
    # K线图
    elif data.startswith("chart_"):
        symbol = data.replace("chart_", "")
        await query.message.reply_text(
            f"📈 **{symbol} K线图**\n\n"
            "🚧 此功能正在开发中...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    
    # 返回
    elif data.startswith("back_"):
        symbol = data.replace("back_", "")
        await query.message.edit_reply_markup(
            reply_markup=create_report_keyboard(symbol)
        )
    
    # 无操作
    elif data == "noop":
        pass
    
    elif data == "cancel":
        await query.message.edit_text("❌ 操作已取消")


async def show_news(query, symbol: str) -> None:
    """显示更多新闻"""
    news = await data_provider.fetch_company_news(symbol, limit=10)
    
    if not news:
        await query.message.reply_text(
            f"📰 **{symbol} 相关新闻**\n\n"
            "暂无相关新闻",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        return
    
    news_text = f"📰 **{symbol} 最新新闻**\n\n"
    
    for i, item in enumerate(news, 1):
        time_str = item.published_time.strftime('%m-%d %H:%M') if item.published_time else ""
        news_text += f"**{i}. {item.title}**\n"
        if time_str:
            news_text += f"🕐 {time_str} | "
        news_text += f"📰 {item.publisher}\n"
        if item.url:
            news_text += f"[阅读全文]({item.url})\n"
        news_text += "\n"
    
    await query.message.reply_text(
        news_text,
        parse_mode=constants.ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


# ==================== 消息处理器 ====================

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理普通文本消息
    尝试将其作为股票代码处理
    """
    text = update.message.text.strip().upper()
    
    # 检查是否可能是股票代码
    # 美股: 1-5个字母
    # 港股: 数字 或 数字.HK
    # A股: 6位数字 或 数字.SS/SZ
    
    is_valid_symbol = (
        (text.isalpha() and 1 <= len(text) <= 5) or  # 美股
        (text.replace('.', '').replace('HK', '').replace('SS', '').replace('SZ', '').isdigit()) or  # 港股/A股
        ('.' in text and any(suffix in text for suffix in ['.HK', '.SS', '.SZ']))  # 明确后缀
    )
    
    if is_valid_symbol:
        # 作为股票代码处理
        await process_stock_analysis(update, context, text)
    else:
        # 提供帮助
        await update.message.reply_text(
            "🤔 我不太理解你的意思\n\n"
            "你可以：\n"
            "• 直接发送股票代码，如 `TSLA`\n"
            "• 使用 `/analyze TSLA` 命令\n"
            "• 发送 /help 查看帮助",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=create_main_menu_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    全局错误处理器
    """
    logger.error(f"发生错误: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ 抱歉，处理您的请求时发生了错误。\n"
            "请稍后重试。"
        )


def setup_handlers(application: Application) -> None:
    """
    设置所有处理器
    
    Args:
        application: Telegram Application 实例
    """
    # 初始化服务
    init_services()
    
    # 命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    
    # 回调处理器
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # 文本消息处理器
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_message_handler
    ))
    
    # 错误处理器
    application.add_error_handler(error_handler)
    
    logger.info("所有处理器设置完成")
