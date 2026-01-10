"""
Handlers Module - 訊息處理模組
================================
此模組負責處理所有 Telegram Bot 訊息和回調。
This module handles all Telegram Bot messages and callbacks.

⚠️ 此 Bot 純粹用於程式學習、資料結構研究與全球地點匹配實驗，嚴禁公開部署或用於任何商業用途。
⚠️ This Bot is purely for programming learning and experiments. Do not deploy publicly.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from typing import List, Dict

from database import get_database

# 建立路由器 / Create router
router = Router()


def format_location_markdown(location: Dict, detailed: bool = False) -> str:
    """
    將地點資料格式化為 Markdown 字串
    Format location data as Markdown string
    
    Args:
        location: 地點資料字典 / Location data dictionary
        detailed: 是否顯示詳細資訊 / Whether to show detailed info
        
    Returns:
        格式化的 Markdown 字串 / Formatted Markdown string
    """
    lines = []
    
    # 標題：暱稱或區域名稱
    # Title: nickname or area name
    nickname = location.get("nickname", "")
    area = location.get("area", "")
    title = nickname if nickname else area
    lines.append(f"🏷️ *{escape_markdown(title)}*")
    lines.append("")
    
    # 地理位置
    # Geographic location
    country = location.get("country", "")
    city = location.get("city", "")
    sub_area = location.get("sub_area", "")
    
    lines.append(f"🌍 *國家/Country:* {escape_markdown(country)}")
    lines.append(f"🏙️ *城市/City:* {escape_markdown(city)}")
    lines.append(f"📍 *區域/Area:* {escape_markdown(area)}")
    
    if sub_area:
        lines.append(f"🔹 *子區域/Sub-area:* {escape_markdown(sub_area)}")
    
    # 類型
    # Types
    types = location.get("types", [])
    if types:
        types_str = ", ".join(types)
        lines.append(f"🏛️ *類型/Types:* {escape_markdown(types_str)}")
    
    # 價格範圍
    # Price range
    price_range = location.get("price_range", "")
    if price_range:
        lines.append(f"💰 *費用/Price:* {escape_markdown(price_range)}")
    
    # 詳細資訊（僅在 detailed=True 時顯示）
    # Detailed info (only shown when detailed=True)
    if detailed:
        address = location.get("address_detail", "")
        if address:
            lines.append(f"📬 *地址/Address:* {escape_markdown(address)}")
        
        # Telegram 聯絡方式
        # Telegram contacts
        tg_contacts = location.get("tg_contacts", [])
        if tg_contacts:
            lines.append("")
            lines.append("📱 *Telegram 資訊/Contacts:*")
            for contact in tg_contacts:
                lines.append(f"  • {escape_markdown(contact)}")
        
        # 備註
        # Notes
        notes = location.get("notes", "")
        if notes:
            lines.append("")
            lines.append(f"📝 *備註/Notes:* {escape_markdown(notes)}")
        
        # 最後更新
        # Last update
        last_update = location.get("last_update", "")
        if last_update:
            lines.append(f"🕐 *更新/Updated:* {escape_markdown(last_update)}")
    
    return "\n".join(lines)


def escape_markdown(text: str) -> str:
    """
    轉義 Markdown 特殊字元
    Escape Markdown special characters
    
    Args:
        text: 原始字串 / Original string
        
    Returns:
        轉義後的字串 / Escaped string
    """
    if not text:
        return ""
    # MarkdownV2 需要轉義的字元
    # Characters that need escaping in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def create_results_keyboard(results: List[Dict], show_regions: bool = True) -> InlineKeyboardMarkup:
    """
    建立搜尋結果的內聯鍵盤
    Create inline keyboard for search results
    
    Args:
        results: 搜尋結果列表 / List of search results
        show_regions: 是否顯示地區按鈕 / Whether to show region buttons
        
    Returns:
        InlineKeyboardMarkup 物件 / InlineKeyboardMarkup object
    """
    buttons = []
    
    # 為每個結果建立詳細查看按鈕
    # Create detail view button for each result
    for i, loc in enumerate(results):
        nickname = loc.get("nickname", loc.get("area", "Location"))
        # 限制按鈕文字長度
        # Limit button text length
        if len(nickname) > 25:
            nickname = nickname[:22] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=f"📍 {nickname}",
                callback_data=f"detail_{i}"
            )
        ])
    
    # 地區快捷按鈕
    # Region shortcut buttons
    if show_regions:
        buttons.append([
            InlineKeyboardButton(text="🌏 亞洲/Asia", callback_data="region_asia"),
            InlineKeyboardButton(text="🌍 歐洲/Europe", callback_data="region_europe")
        ])
        buttons.append([
            InlineKeyboardButton(text="🌎 美洲/Americas", callback_data="region_americas"),
            InlineKeyboardButton(text="🌐 其他/Other", callback_data="region_other")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_back_keyboard() -> InlineKeyboardMarkup:
    """
    建立返回按鈕鍵盤
    Create back button keyboard
    
    Returns:
        InlineKeyboardMarkup 物件 / InlineKeyboardMarkup object
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 返回/Back", callback_data="back")]
    ])


# 儲存最近搜尋結果（簡單的記憶體快取）
# Store recent search results (simple in-memory cache)
_recent_results: Dict[int, List[Dict]] = {}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    處理 /start 指令
    Handle /start command
    """
    welcome_text = """
🌍 *歡迎使用全球城市指南 Bot\\!*
*Welcome to Global City Guide Bot\\!*

這是一個用於學習程式設計的示範 Bot，展示：
This is a demo bot for learning programming, demonstrating:

• 🔍 模糊字串匹配 \\(Fuzzy String Matching\\)
• 📊 JSON 資料處理 \\(JSON Data Processing\\)
• 🤖 aiogram 3\\.x 框架 \\(aiogram 3\\.x Framework\\)
• ⌨️ Inline Keyboards 互動

*使用方式/How to use:*
直接輸入地點名稱即可搜尋\\!
Just type a location name to search\\!

*範例輸入/Examples:*
• `Tokyo Shibuya`
• `Paris Eiffel`
• `台北 101`
• `Amsterdam Museum`

輸入 /help 查看更多資訊
Type /help for more information

⚠️ _此 Bot 純粹用於程式學習與實驗_
⚠️ _This bot is for learning purposes only_
"""
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    處理 /help 指令
    Handle /help command
    """
    help_text = """
📖 *城市指南 Bot 使用說明*
*City Guide Bot Help*

*指令列表/Commands:*
• /start \\- 開始使用/Start
• /help \\- 顯示此說明/Show this help

*搜尋功能/Search:*
直接輸入任何地點關鍵字：
Just type any location keyword:
• 城市名稱 \\(City name\\)
• 景點名稱 \\(Landmark name\\)
• 區域名稱 \\(Area name\\)

*搜尋範例/Search Examples:*
• `Tokyo Senso-ji` → 東京淺草寺
• `Paris Louvre` → 巴黎羅浮宮
• `New York Times Square` → 紐約時代廣場
• `香港維多利亞港` → Victoria Harbour

*匹配邏輯/Matching Logic:*
• 使用模糊匹配，相似度 ≥70% 即顯示
• 優先級：子區域 > 區域 > 城市 > 國家
• 有 Telegram 資訊的記錄優先顯示

*資料來源/Data Source:*
基於公開旅遊資訊與 Wikipedia 景點列表
Based on public travel info and Wikipedia landmarks

*關於 TG 欄位/About TG Field:*
部分景點包含官方或社群 Telegram 連結
Some locations include official/community TG links

⚠️ _資料僅供學習參考，可能不完全準確_
⚠️ _Data is for learning reference only_
"""
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(F.text)
async def handle_search(message: Message) -> None:
    """
    處理一般文字訊息（搜尋查詢）
    Handle general text messages (search queries)
    """
    query = message.text.strip()
    
    # 驗證輸入
    # Validate input
    if not query or len(query) < 2:
        await message.answer(
            "⚠️ 請輸入至少 2 個字元的地點關鍵字\n"
            "⚠️ Please enter at least 2 characters\n\n"
            "範例/Example: `Bangkok Temple` 或 `東京 淺草`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # 取得資料庫實例並搜尋
    # Get database instance and search
    db = get_database()
    results = db.search(query, threshold=70, max_results=6)
    
    if not results:
        # 無結果時的回覆
        # Response when no results found
        samples = db.get_sample_locations(5)
        samples_text = "\n".join([f"• `{s}`" for s in samples])
        
        no_result_text = f"""
❌ *無匹配記錄*
*No matching records found*

找不到與「{escape_markdown(query)}」相關的地點。
No locations found for "{escape_markdown(query)}"\\. 

資料可能已過期，或請嘗試更精確的關鍵字。
Data may be outdated, or try more specific keywords\\.

*建議嘗試/Try these:*
{samples_text}
"""
        await message.answer(no_result_text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    # 儲存結果供後續查詢
    # Store results for later queries
    user_id = message.from_user.id
    _recent_results[user_id] = results
    
    # 格式化結果
    # Format results
    if len(results) == 1:
        # 單一結果直接顯示詳細
        # Single result shows detailed view
        response = format_location_markdown(results[0], detailed=True)
        await message.answer(response, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # 多個結果顯示摘要
        # Multiple results show summary
        header = f"🔍 *找到 {len(results)} 個結果*\n*Found {len(results)} results*\n\n"
        
        summaries = []
        for i, loc in enumerate(results, 1):
            nickname = loc.get("nickname", loc.get("area", ""))
            city = loc.get("city", "")
            country = loc.get("country", "")
            has_tg = "📱" if loc.get("tg_contacts") else ""
            summaries.append(
                f"{i}\\. *{escape_markdown(nickname)}* {has_tg}\n"
                f"   {escape_markdown(city)}, {escape_markdown(country)}"
            )
        
        response = header + "\n\n".join(summaries)
        response += "\n\n_點擊下方按鈕查看詳細/Click buttons for details_"
        
        keyboard = create_results_keyboard(results)
        await message.answer(response, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)


@router.callback_query(F.data.startswith("detail_"))
async def handle_detail_callback(callback: CallbackQuery) -> None:
    """
    處理詳細查看回調
    Handle detail view callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    results = _recent_results.get(user_id, [])
    
    try:
        index = int(callback.data.split("_")[1])
        if 0 <= index < len(results):
            location = results[index]
            response = format_location_markdown(location, detailed=True)
            await callback.message.edit_text(
                response,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=create_back_keyboard()
            )
    except (ValueError, IndexError):
        await callback.message.answer("⚠️ 無法載入詳細資訊/Cannot load details")


@router.callback_query(F.data.startswith("region_"))
async def handle_region_callback(callback: CallbackQuery) -> None:
    """
    處理地區篩選回調
    Handle region filter callback
    """
    await callback.answer()
    
    region = callback.data.split("_")[1]
    region_names = {
        "asia": "🌏 亞洲/Asia",
        "europe": "🌍 歐洲/Europe",
        "americas": "🌎 美洲/Americas",
        "other": "🌐 其他/Other"
    }
    
    db = get_database()
    results = db.get_locations_by_region(region)
    
    if not results:
        await callback.message.answer(f"該地區暫無資料/No data for this region")
        return
    
    # 儲存結果
    # Store results
    user_id = callback.from_user.id
    _recent_results[user_id] = results
    
    # 格式化結果
    # Format results
    header = f"📍 *{region_names.get(region, region)} 熱門景點*\n\n"
    
    summaries = []
    for i, loc in enumerate(results, 1):
        nickname = loc.get("nickname", loc.get("area", ""))
        city = loc.get("city", "")
        has_tg = "📱" if loc.get("tg_contacts") else ""
        summaries.append(
            f"{i}\\. *{escape_markdown(nickname)}* {has_tg}\n"
            f"   {escape_markdown(city)}"
        )
    
    response = header + "\n\n".join(summaries)
    keyboard = create_results_keyboard(results, show_regions=False)
    
    await callback.message.edit_text(
        response,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back")
async def handle_back_callback(callback: CallbackQuery) -> None:
    """
    處理返回按鈕回調
    Handle back button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    results = _recent_results.get(user_id, [])
    
    if not results:
        await callback.message.edit_text(
            "請重新搜尋/Please search again",
            reply_markup=None
        )
        return
    
    # 重新顯示結果列表
    # Re-display results list
    header = f"🔍 *找到 {len(results)} 個結果*\n*Found {len(results)} results*\n\n"
    
    summaries = []
    for i, loc in enumerate(results, 1):
        nickname = loc.get("nickname", loc.get("area", ""))
        city = loc.get("city", "")
        country = loc.get("country", "")
        has_tg = "📱" if loc.get("tg_contacts") else ""
        summaries.append(
            f"{i}\\. *{escape_markdown(nickname)}* {has_tg}\n"
            f"   {escape_markdown(city)}, {escape_markdown(country)}"
        )
    
    response = header + "\n\n".join(summaries)
    response += "\n\n_點擊下方按鈕查看詳細/Click buttons for details_"
    
    keyboard = create_results_keyboard(results)
    await callback.message.edit_text(
        response,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
    )
