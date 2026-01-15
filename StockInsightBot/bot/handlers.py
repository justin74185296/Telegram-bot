"""
Telegram Bot 命令和消息處理器
處理用戶交互和指令
"""
import re
import asyncio
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode, ChatAction

from config.settings import settings
from core.data_provider import StockDataProvider
from core.report_engine import StockReportEngine
from core.financial_analyzer import FinancialAnalyzer
from utils.loggers import get_logger
from utils.formatters import Formatters
from .keyboards import InlineKeyboards

logger = get_logger("Handlers")

# 全局實例
data_provider = StockDataProvider(
    cache_ttl=settings.cache_ttl,
    cache_maxsize=settings.cache_maxsize
)
report_engine = StockReportEngine()
formatter = Formatters()


# ==================== 命令處理器 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    處理 /start 命令
    發送歡迎訊息和使用說明
    """
    user = update.effective_user
    logger.info(f"用戶 {user.id} ({user.username}) 啟動了機器人")
    
    welcome_message = f"""👋 歡迎使用 **StockInsightBot**！

您好，{user.first_name}！我是您的專業股票分析助手。

🎯 **核心功能**
• 實時股票報價查詢
• AI 深度分析報告
• 財務指標解讀
• 市場新聞整合

📝 **使用方法**
• 發送 `/analyze AAPL` 分析蘋果公司
• 直接發送股票代碼如 `TSLA`
• 點擊下方按鈕快速查詢

🌍 **支援市場**
• 美股：直接輸入代碼（如 AAPL, TSLA）
• 港股：輸入4位數字（如 0700）
• A股：輸入6位數字（如 600519）

📌 輸入 /help 查看完整指南"""

    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboards.get_quick_symbols()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    處理 /help 命令
    顯示詳細使用說明
    """
    help_message = """📖 **StockInsightBot 使用指南**

━━━━━━━━━━━━━━━━━━━━━━
📌 **基本命令**
━━━━━━━━━━━━━━━━━━━━━━

🔹 `/start` - 啟動機器人
🔹 `/help` - 查看此幫助
🔹 `/analyze <代碼>` - 分析指定股票

━━━━━━━━━━━━━━━━━━━━━━
📊 **分析報告內容**
━━━━━━━━━━━━━━━━━━━━━━

📈 **即時快照**
• 當前股價與漲跌幅
• 成交量與市值

📊 **財務分析**
• 估值指標 (PE/PB/PS)
• 盈利能力 (ROE/ROA)
• 財務健康度

📰 **新聞動態**
• 近期相關新聞
• 市場情緒分析

🔮 **投資展望**
• 上行驅動因素
• 下行風險提示

━━━━━━━━━━━━━━━━━━━━━━
🌍 **股票代碼格式**
━━━━━━━━━━━━━━━━━━━━━━

• **美股**: AAPL, TSLA, GOOGL
• **港股**: 0700, 9988, 0005
• **A股**: 600519, 000001

━━━━━━━━━━━━━━━━━━━━━━
💡 **小提示**
━━━━━━━━━━━━━━━━━━━━━━

• 直接發送股票代碼即可快速查詢
• 報告生成需要 10-30 秒
• 數據每 5 分鐘自動更新"""

    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboards.get_help_menu()
    )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    處理 /analyze 命令
    生成股票分析報告
    """
    # 檢查是否提供了股票代碼
    if not context.args:
        await update.message.reply_text(
            "⚠️ 請提供股票代碼\n\n"
            "用法: `/analyze AAPL`\n"
            "或直接發送股票代碼",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.args[0].upper()
    await perform_analysis(update, symbol)


async def perform_analysis(update: Update, symbol: str, message_to_edit=None) -> None:
    """
    執行股票分析流程
    
    Args:
        update: Telegram Update 對象
        symbol: 股票代碼
        message_to_edit: 要編輯的消息（用於刷新）
    """
    user = update.effective_user
    logger.info(f"用戶 {user.id} 請求分析: {symbol}")
    
    # 發送「正在分析」提示
    if message_to_edit:
        status_message = message_to_edit
        await status_message.edit_text(
            f"🔄 正在刷新 **{symbol}** 的分析報告...\n\n"
            "⏳ 請稍候，這可能需要 10-30 秒",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        status_message = await update.message.reply_text(
            f"🔍 正在獲取 **{symbol}** 的數據並生成分析報告...\n\n"
            "⏳ 請稍候，這可能需要 10-30 秒",
            parse_mode=ParseMode.MARKDOWN
        )
    
    try:
        # 顯示「正在輸入」狀態
        await update.effective_chat.send_action(ChatAction.TYPING)
        
        # 獲取完整數據
        data = data_provider.get_full_analysis_data(symbol)
        
        # 檢查是否有錯誤
        if "error" in data.get("quote", {}):
            await status_message.edit_text(
                f"❌ 無法獲取 **{symbol}** 的數據\n\n"
                f"錯誤: {data['quote'].get('error', '未知錯誤')}\n\n"
                "請檢查股票代碼是否正確",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # 生成 AI 報告
        report = await report_engine.generate_report(data)
        
        # 分割長報告
        await send_long_message(
            update.effective_chat,
            report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboards.get_analysis_actions(symbol)
        )
        
        # 刪除狀態消息
        await status_message.delete()
        
        logger.info(f"分析完成: {symbol}")
        
    except Exception as e:
        logger.error(f"分析失敗 {symbol}: {e}")
        await status_message.edit_text(
            f"❌ 分析 **{symbol}** 時發生錯誤\n\n"
            f"錯誤詳情: {str(e)}\n\n"
            "請稍後再試",
            parse_mode=ParseMode.MARKDOWN
        )


async def send_long_message(chat, text: str, parse_mode=None, reply_markup=None) -> None:
    """
    發送長消息（自動分割）
    
    Args:
        chat: Telegram Chat 對象
        text: 要發送的文本
        parse_mode: 解析模式
        reply_markup: 回覆鍵盤
    """
    MAX_LENGTH = 4096
    
    if len(text) <= MAX_LENGTH:
        await chat.send_message(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return
    
    # 分割消息
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > MAX_LENGTH:
            parts.append(current_part)
            current_part = line
        else:
            current_part += '\n' + line if current_part else line
    
    if current_part:
        parts.append(current_part)
    
    # 發送所有部分
    for i, part in enumerate(parts):
        # 只在最後一部分添加按鈕
        markup = reply_markup if i == len(parts) - 1 else None
        await chat.send_message(
            part,
            parse_mode=parse_mode,
            reply_markup=markup
        )
        await asyncio.sleep(0.5)  # 避免發送過快


# ==================== 消息處理器 ====================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    處理普通文字消息
    嘗試識別股票代碼
    """
    text = update.message.text.strip().upper()
    
    # 股票代碼正則匹配
    # 美股: 1-5 個字母
    # 港股: 4 位數字
    # A股: 6 位數字
    
    if re.match(r'^[A-Z]{1,5}$', text):
        # 可能是美股代碼
        await perform_analysis(update, text)
    elif re.match(r'^\d{4}$', text):
        # 可能是港股代碼
        await perform_analysis(update, text)
    elif re.match(r'^\d{6}$', text):
        # 可能是 A 股代碼
        await perform_analysis(update, text)
    else:
        # 不是股票代碼，給出提示
        await update.message.reply_text(
            "🤔 我不太理解您的意思\n\n"
            "您可以：\n"
            "• 發送股票代碼（如 AAPL, 0700, 600519）\n"
            "• 使用 /analyze <代碼> 命令\n"
            "• 輸入 /help 查看使用說明",
            reply_markup=InlineKeyboards.get_quick_symbols()
        )


# ==================== 回調處理器 ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    處理內聯按鈕回調
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"收到回調: {data}")
    
    # 解析回調數據
    if data.startswith("analyze_"):
        # 快速分析
        symbol = data.replace("analyze_", "")
        # 創建一個假的 update 對象用於發送消息
        await query.message.reply_text(
            f"🔍 正在獲取 **{symbol}** 的數據...",
            parse_mode=ParseMode.MARKDOWN
        )
        # 刪除原消息並執行分析
        await perform_analysis_from_callback(query, symbol)
    
    elif data.startswith("refresh_"):
        # 刷新報告
        symbol = data.replace("refresh_", "")
        await perform_analysis_from_callback(query, symbol, refresh=True)
    
    elif data.startswith("news_"):
        # 查看更多新聞
        symbol = data.replace("news_", "")
        await show_news(query, symbol)
    
    elif data.startswith("indicators_"):
        # 查看詳細指標
        symbol = data.replace("indicators_", "")
        await show_indicators(query, symbol)
    
    elif data.startswith("history_"):
        # 查看歷史走勢
        symbol = data.replace("history_", "")
        await show_history_options(query, symbol)
    
    elif data.startswith("period_"):
        # 選擇時間週期
        parts = data.split("_")
        symbol = parts[1]
        period = parts[2]
        await show_history(query, symbol, period)
    
    elif data.startswith("back_"):
        # 返回
        symbol = data.replace("back_", "")
        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboards.get_analysis_actions(symbol)
        )
    
    elif data.startswith("help_"):
        # 幫助選項
        await handle_help_callback(query, data)
    
    elif data == "cancel":
        await query.message.delete()


async def perform_analysis_from_callback(query, symbol: str, refresh: bool = False) -> None:
    """
    從回調執行分析
    """
    user = query.from_user
    chat = query.message.chat
    
    logger.info(f"用戶 {user.id} 從按鈕請求分析: {symbol}")
    
    # 發送狀態消息
    status_message = await chat.send_message(
        f"🔍 正在獲取 **{symbol}** 的數據並生成分析報告...\n\n"
        "⏳ 請稍候，這可能需要 10-30 秒",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        await chat.send_action(ChatAction.TYPING)
        
        # 獲取數據
        data = data_provider.get_full_analysis_data(symbol)
        
        if "error" in data.get("quote", {}):
            await status_message.edit_text(
                f"❌ 無法獲取 **{symbol}** 的數據\n\n"
                f"錯誤: {data['quote'].get('error', '未知錯誤')}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # 生成報告
        report = await report_engine.generate_report(data)
        
        # 發送報告
        await send_long_message(
            chat,
            report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboards.get_analysis_actions(symbol)
        )
        
        await status_message.delete()
        
    except Exception as e:
        logger.error(f"分析失敗 {symbol}: {e}")
        await status_message.edit_text(
            f"❌ 分析 **{symbol}** 時發生錯誤: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def show_news(query, symbol: str) -> None:
    """顯示更多新聞"""
    await query.message.reply_text(
        f"📰 正在獲取 **{symbol}** 的最新新聞...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        news = data_provider.fetch_company_news(symbol, limit=10)
        
        if not news:
            await query.message.reply_text(
                f"📰 **{symbol}** 暫無相關新聞",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        news_text = f"📰 **{symbol} 最新新聞**\n\n"
        
        for i, item in enumerate(news, 1):
            title = item.get('title', '無標題')
            publisher = item.get('publisher', '未知來源')
            pub_time = item.get('published_time', '')
            link = item.get('link', '')
            
            news_text += f"**{i}. {title}**\n"
            news_text += f"📍 {publisher}"
            if pub_time:
                news_text += f" | {pub_time[:10]}"
            if link:
                news_text += f"\n🔗 [閱讀全文]({link})"
            news_text += "\n\n"
        
        await query.message.reply_text(
            news_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"獲取新聞失敗: {e}")
        await query.message.reply_text(
            f"❌ 獲取新聞失敗: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def show_indicators(query, symbol: str) -> None:
    """顯示詳細指標"""
    try:
        indicators = data_provider.fetch_key_indicators(symbol)
        
        if "error" in indicators:
            await query.message.reply_text(
                f"❌ 獲取指標失敗: {indicators['error']}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # 使用財務分析器格式化
        summary = FinancialAnalyzer.format_indicators_summary(indicators)
        
        await query.message.reply_text(
            f"**{symbol}** 詳細財務指標\n\n{summary}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        await query.message.reply_text(
            f"❌ 獲取指標失敗: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def show_history_options(query, symbol: str) -> None:
    """顯示歷史數據選項"""
    await query.message.edit_reply_markup(
        reply_markup=InlineKeyboards.get_period_selector(symbol)
    )


async def show_history(query, symbol: str, period: str) -> None:
    """顯示歷史數據"""
    try:
        history = data_provider.fetch_historical_data(symbol, period)
        
        if "error" in history:
            await query.message.reply_text(
                f"❌ 獲取歷史數據失敗: {history['error']}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        summary = history.get('summary', {})
        
        period_names = {
            "1wk": "1週",
            "1mo": "1月",
            "3mo": "3月",
            "6mo": "6月",
            "1y": "1年",
            "max": "全部"
        }
        
        history_text = f"""📈 **{symbol}** 歷史走勢 ({period_names.get(period, period)})

💰 **價格變化**
• 期初: {formatter.format_price(summary.get('start_price'))}
• 期末: {formatter.format_price(summary.get('end_price'))}
• 漲跌: {formatter.format_percentage(summary.get('period_return'))} {formatter.get_trend_emoji(summary.get('period_return'))}

📊 **區間統計**
• 最高: {formatter.format_price(summary.get('high'))}
• 最低: {formatter.format_price(summary.get('low'))}
• 均量: {formatter.format_volume(summary.get('avg_volume'))}"""

        await query.message.reply_text(
            history_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboards.get_analysis_actions(symbol)
        )
        
    except Exception as e:
        logger.error(f"獲取歷史數據失敗: {e}")
        await query.message.reply_text(
            f"❌ 獲取歷史數據失敗: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_help_callback(query, data: str) -> None:
    """處理幫助相關回調"""
    if data == "help_guide":
        text = """📖 **使用指南**

1️⃣ **快速查詢**
直接發送股票代碼即可

2️⃣ **完整分析**
使用 `/analyze 代碼` 獲取 AI 報告

3️⃣ **支援的代碼格式**
• 美股: AAPL, TSLA (1-5字母)
• 港股: 0700, 9988 (4位數字)
• A股: 600519, 000001 (6位數字)"""
    
    elif data == "help_search":
        text = """🔍 **搜索股票**

直接輸入您想查詢的股票代碼：

**美股範例**
• AAPL - 蘋果
• TSLA - 特斯拉
• GOOGL - Google

**港股範例**
• 0700 - 騰訊
• 9988 - 阿里巴巴

**A股範例**
• 600519 - 貴州茅台
• 000001 - 平安銀行"""
    
    elif data == "help_faq":
        text = """❓ **常見問題**

**Q: 數據多久更新一次？**
A: 報價數據每5分鐘更新

**Q: 報告生成需要多久？**
A: 通常需要 10-30 秒

**Q: 支援哪些市場？**
A: 美股、港股、A股

**Q: 為什麼有些指標顯示 N/A？**
A: 部分公司可能缺少某些數據"""
    
    elif data == "help_contact":
        text = """📞 **聯繫方式**

如有問題或建議，請聯繫管理員

🤖 Bot: @Stock_analysis_8520_bot"""
    
    else:
        text = "未知選項"
    
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ==================== 錯誤處理 ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    全局錯誤處理器
    """
    logger.error(f"發生錯誤: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ 發生了一個錯誤，請稍後再試\n\n"
            "如果問題持續，請聯繫管理員",
            parse_mode=ParseMode.MARKDOWN
        )


# ==================== 主動發送訊息功能 ====================

async def send_message_to_user(bot: Bot, chat_id: int, message: str, parse_mode=ParseMode.MARKDOWN) -> bool:
    """
    主動向用戶發送訊息
    
    Args:
        bot: Telegram Bot 實例
        chat_id: 用戶或群組的 chat_id
        message: 要發送的訊息
        parse_mode: 解析模式
    
    Returns:
        是否發送成功
    """
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode
        )
        logger.info(f"成功發送訊息到 {chat_id}")
        return True
    except Exception as e:
        logger.error(f"發送訊息失敗 {chat_id}: {e}")
        return False


# ==================== 設置處理器 ====================

def setup_handlers(application: Application) -> None:
    """
    設置所有處理器
    
    Args:
        application: Telegram Application 對象
    """
    # 命令處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    
    # 回調處理器
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # 文字消息處理器
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    
    # 錯誤處理器
    application.add_error_handler(error_handler)
    
    logger.info("所有處理器設置完成")
