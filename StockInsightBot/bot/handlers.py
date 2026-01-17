"""
Telegram Bot 命令和消息處理器
"""
import logging
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode

from core.data_provider import StockDataProvider
from core.report_engine import StockReportEngine
from .keyboards import get_report_keyboard, get_news_keyboard, get_start_keyboard

logger = logging.getLogger(__name__)

# 初始化數據提供者和報告引擎
data_provider = StockDataProvider()
report_engine = StockReportEngine()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start 命令處理
    發送歡迎信息和功能介紹
    """
    logger.info(f"收到 /start 命令 - 用戶: {update.effective_user.id}")
    try:
        welcome_message = """
🤖 **歡迎使用 StockInsightBot！**

我是您的專業股票分析助手，可以幫您：

📊 **即時行情** - 獲取股票最新價格和漲跌
📈 **深度分析** - AI 生成專業投資報告
📰 **新聞整合** - 獲取相關市場新聞
💹 **財務指標** - PE、PB、ROE 等關鍵數據

**使用方法：**
• 發送 `/analyze TSLA` 分析特斯拉
• 或直接發送股票代碼如 `AAPL`

**支持市場：**
🇺🇸 美股：AAPL, TSLA, GOOGL
🇭🇰 港股：0700, 9988
🇨🇳 A股：600519, 000001

點擊下方按鈕快速開始 👇
"""
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_start_keyboard()
        )
        logger.info(f"已回覆 /start - 用戶: {update.effective_user.id}")
    except Exception as e:
        logger.error(f"/start 命令錯誤: {e}", exc_info=True)
        await update.message.reply_text("❌ 發生錯誤，請稍後再試")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help 命令處理
    顯示詳細使用說明
    """
    logger.info(f"收到 /help 命令 - 用戶: {update.effective_user.id}")
    try:
        help_message = """
📖 **StockInsightBot 使用指南**

**命令列表：**
• `/start` - 開始使用，顯示歡迎信息
• `/analyze <代碼>` - 分析指定股票
• `/help` - 顯示此幫助信息

**快速分析：**
直接發送股票代碼即可，例如：
• `TSLA` - 分析特斯拉
• `AAPL` - 分析蘋果
• `0700` - 分析騰訊（港股）
• `600519` - 分析茅台（A股）

**報告內容：**
📈 即時快照 - 股價、漲跌、市場情緒
📊 財務解析 - 估值、盈利、健康度
📰 新聞整合 - 近期動態與影響分析
🔮 未來展望 - 機會與風險評估
💎 核心結論 - 投資價值判斷

**提示：**
• AI 報告生成需要 30-60 秒
• 可點擊「刷新報告」獲取最新數據
• 支持美股、港股、A股代碼
"""
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"已回覆 /help - 用戶: {update.effective_user.id}")
    except Exception as e:
        logger.error(f"/help 命令錯誤: {e}", exc_info=True)
        await update.message.reply_text("❌ 發生錯誤，請稍後再試")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /analyze 命令處理
    生成股票分析報告
    """
    if not context.args:
        await update.message.reply_text(
            "❌ 請提供股票代碼\n\n例如：`/analyze TSLA`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.args[0].upper()
    await generate_analysis(update, symbol)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理普通文字消息
    嘗試識別股票代碼
    """
    logger.info(f"收到訊息: '{update.message.text}' - 用戶: {update.effective_user.id}")
    try:
        text = update.message.text.strip().upper()
        
        # 檢查是否為有效的股票代碼格式
        # 美股: 1-5 個字母
        # 港股: 4 位數字
        # A股: 6 位數字
        if re.match(r'^[A-Z]{1,5}$', text) or re.match(r'^\d{4,6}$', text):
            await generate_analysis(update, text)
        else:
            await update.message.reply_text(
                "🤔 無法識別的股票代碼\n\n"
                "請輸入有效的股票代碼，例如：\n"
                "• 美股：AAPL, TSLA\n"
                "• 港股：0700\n"
                "• A股：600519\n\n"
                "或使用 `/help` 查看幫助",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"處理訊息錯誤: {e}", exc_info=True)
        await update.message.reply_text("❌ 發生錯誤，請稍後再試")


async def generate_analysis(update: Update, symbol: str):
    """
    生成並發送股票分析報告
    """
    # 發送等待消息
    wait_message = await update.message.reply_text(
        f"⏳ 正在獲取 **{symbol}** 的數據並生成 AI 分析報告，請稍候...\n\n"
        f"_這可能需要 30-60 秒_",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # 獲取數據
        quote = data_provider.fetch_realtime_quote(symbol)
        
        if 'error' in quote:
            await wait_message.edit_text(
                f"❌ 無法獲取 **{symbol}** 的數據\n\n"
                f"錯誤：{quote['error']}\n\n"
                f"請確認股票代碼是否正確",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        indicators = data_provider.fetch_key_indicators(symbol)
        profile = data_provider.get_company_profile(symbol)
        news = data_provider.fetch_company_news(symbol)
        
        # 生成報告
        report = report_engine.generate_report(quote, indicators, profile, news)
        
        # 刪除等待消息
        await wait_message.delete()
        
        # 發送報告（可能需要分割）
        await send_long_message(update, report, symbol)
        
    except Exception as e:
        logger.error(f"分析 {symbol} 時發生錯誤: {e}")
        await wait_message.edit_text(
            f"❌ 分析 **{symbol}** 時發生錯誤\n\n"
            f"請稍後再試或聯繫管理員",
            parse_mode=ParseMode.MARKDOWN
        )


async def send_long_message(update: Update, text: str, symbol: str):
    """
    發送長消息，自動分割
    Telegram 單條消息限制 4096 字符
    """
    max_length = 4000  # 留些餘量
    
    if len(text) <= max_length:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_report_keyboard(symbol)
        )
    else:
        # 分割消息
        parts = []
        current_part = ""
        
        for line in text.split('\n'):
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line
            else:
                current_part += '\n' + line if current_part else line
        
        if current_part:
            parts.append(current_part)
        
        # 發送所有部分
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # 最後一部分添加鍵盤
                await update.message.reply_text(
                    part,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_report_keyboard(symbol)
                )
            else:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理內聯鍵盤回調
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("analyze_"):
        # 快速分析按鈕
        symbol = data.replace("analyze_", "")
        await query.message.reply_text(
            f"⏳ 正在分析 **{symbol}**，請稍候...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 創建一個假的 update 對象來複用 generate_analysis
        class FakeUpdate:
            def __init__(self, message):
                self.message = message
        
        fake_update = FakeUpdate(query.message)
        await generate_analysis(fake_update, symbol)
        
    elif data.startswith("refresh_"):
        symbol = data.replace("refresh_", "")
        await query.message.reply_text(
            f"⏳ 正在刷新 **{symbol}** 報告...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        class FakeUpdate:
            def __init__(self, message):
                self.message = message
        
        fake_update = FakeUpdate(query.message)
        await generate_analysis(fake_update, symbol)
        
    elif data.startswith("news_"):
        symbol = data.replace("news_", "")
        await show_news(query, symbol)
        
    elif data.startswith("financials_"):
        symbol = data.replace("financials_", "")
        await show_financials(query, symbol)
        
    elif data.startswith("back_"):
        symbol = data.replace("back_", "")
        await query.message.reply_text(
            f"⏳ 正在載入 **{symbol}** 報告...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        class FakeUpdate:
            def __init__(self, message):
                self.message = message
        
        fake_update = FakeUpdate(query.message)
        await generate_analysis(fake_update, symbol)


async def show_news(query, symbol: str):
    """顯示新聞詳情"""
    news = data_provider.fetch_company_news(symbol, limit=10)
    
    if not news:
        await query.message.reply_text(
            f"📰 **{symbol}** 暫無近期新聞",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_news_keyboard(symbol)
        )
        return
    
    text = f"📰 **{symbol}** 近期新聞\n\n"
    
    for i, item in enumerate(news, 1):
        title = item.get('title', '無標題')
        publisher = item.get('publisher', '未知來源')
        link = item.get('link', '')
        
        text += f"**{i}. {title}**\n"
        text += f"   來源：{publisher}\n"
        if link:
            text += f"   [閱讀全文]({link})\n"
        text += "\n"
    
    await query.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_news_keyboard(symbol),
        disable_web_page_preview=True
    )


async def show_financials(query, symbol: str):
    """顯示詳細財務數據"""
    indicators = data_provider.fetch_key_indicators(symbol)
    financials = data_provider.fetch_financials(symbol)
    
    text = f"📊 **{symbol}** 詳細財務數據\n\n"
    
    text += "**估值指標**\n"
    text += f"• PE (本益比): {indicators.get('pe_ratio', 0) or 0:.2f}\n"
    text += f"• Forward PE: {indicators.get('forward_pe', 0) or 0:.2f}\n"
    text += f"• PB (股價淨值比): {indicators.get('pb_ratio', 0) or 0:.2f}\n"
    text += f"• PS (市銷率): {indicators.get('ps_ratio', 0) or 0:.2f}\n"
    text += f"• PEG: {indicators.get('peg_ratio', 0) or 0:.2f}\n\n"
    
    text += "**盈利能力**\n"
    text += f"• ROE: {(indicators.get('roe', 0) or 0) * 100:.2f}%\n"
    text += f"• ROA: {(indicators.get('roa', 0) or 0) * 100:.2f}%\n"
    text += f"• 利潤率: {(indicators.get('profit_margin', 0) or 0) * 100:.2f}%\n"
    text += f"• 營業利潤率: {(indicators.get('operating_margin', 0) or 0) * 100:.2f}%\n\n"
    
    text += "**財務健康**\n"
    text += f"• 負債/權益比: {indicators.get('debt_to_equity', 0) or 0:.2f}\n"
    text += f"• 流動比率: {indicators.get('current_ratio', 0) or 0:.2f}\n"
    text += f"• 速動比率: {indicators.get('quick_ratio', 0) or 0:.2f}\n\n"
    
    text += "**股息**\n"
    text += f"• 股息率: {(indicators.get('dividend_yield', 0) or 0) * 100:.2f}%\n"
    text += f"• 每股股息: ${indicators.get('dividend_rate', 0) or 0:.2f}\n\n"
    
    text += "**成長性**\n"
    text += f"• 營收成長: {(indicators.get('revenue_growth', 0) or 0) * 100:.2f}%\n"
    text += f"• 盈餘成長: {(indicators.get('earnings_growth', 0) or 0) * 100:.2f}%\n"
    
    await query.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_report_keyboard(symbol)
    )


def setup_handlers(application: Application):
    """
    設置所有處理器
    """
    # 命令處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    
    # 回調處理器
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # 消息處理器（放在最後，處理所有文字消息）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("所有處理器已設置完成")
