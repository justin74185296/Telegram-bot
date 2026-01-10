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
import html

from database import get_database

# 建立路由器 / Create router
router = Router()


def escape_html(text: str) -> str:
    """
    轉義 HTML 特殊字元
    Escape HTML special characters
    """
    if not text:
        return ""
    return html.escape(str(text))


def format_location_html(location: Dict, detailed: bool = False) -> str:
    """
    將地點資料格式化為 HTML 字串
    Format location data as HTML string
    """
    lines = []
    
    # 標題：暱稱或區域名稱
    nickname = location.get("nickname", "")
    area = location.get("area", "")
    title = nickname if nickname else area
    lines.append(f"🏷️ <b>{escape_html(title)}</b>")
    lines.append("")
    
    # 地理位置
    country = location.get("country", "")
    city = location.get("city", "")
    sub_area = location.get("sub_area", "")
    
    lines.append(f"🌍 <b>國家/Country:</b> {escape_html(country)}")
    lines.append(f"🏙️ <b>城市/City:</b> {escape_html(city)}")
    lines.append(f"📍 <b>區域/Area:</b> {escape_html(area)}")
    
    if sub_area:
        lines.append(f"🔹 <b>子區域/Sub-area:</b> {escape_html(sub_area)}")
    
    # 類型
    types = location.get("types", [])
    if types:
        types_str = ", ".join(types)
        lines.append(f"🏛️ <b>類型/Types:</b> {escape_html(types_str)}")
    
    # 價格範圍
    price_range = location.get("price_range", "")
    if price_range:
        lines.append(f"💰 <b>費用/Price:</b> {escape_html(price_range)}")
    
    # 詳細資訊
    if detailed:
        address = location.get("address_detail", "")
        if address:
            lines.append(f"📬 <b>地址/Address:</b> {escape_html(address)}")
        
        # Telegram 聯絡方式
        tg_contacts = location.get("tg_contacts", [])
        if tg_contacts:
            lines.append("")
            lines.append("📱 <b>Telegram 資訊/Contacts:</b>")
            for contact in tg_contacts:
                lines.append(f"  • {escape_html(contact)}")
        
        # 備註
        notes = location.get("notes", "")
        if notes:
            lines.append("")
            lines.append(f"📝 <b>備註/Notes:</b> {escape_html(notes)}")
        
        # 最後更新
        last_update = location.get("last_update", "")
        if last_update:
            lines.append(f"🕐 <b>更新/Updated:</b> {escape_html(last_update)}")
    
    return "\n".join(lines)


def create_results_keyboard(results: List[Dict], show_regions: bool = True) -> InlineKeyboardMarkup:
    """
    建立搜尋結果的內聯鍵盤
    Create inline keyboard for search results
    """
    buttons = []
    
    for i, loc in enumerate(results):
        nickname = loc.get("nickname", loc.get("area", "Location"))
        if len(nickname) > 25:
            nickname = nickname[:22] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=f"📍 {nickname}",
                callback_data=f"detail_{i}"
            )
        ])
    
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
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 返回/Back", callback_data="back")]
    ])


# 儲存最近搜尋結果
_recent_results: Dict[int, List[Dict]] = {}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    處理 /start 指令
    """
    welcome_text = """
🌍 <b>歡迎使用全球城市指南 Bot!</b>
<b>Welcome to Global City Guide Bot!</b>

這是一個用於學習程式設計的示範 Bot，展示：

• 🔍 模糊字串匹配 (Fuzzy String Matching)
• 📊 JSON 資料處理 (JSON Data Processing)
• 🤖 aiogram 3.x 框架 (aiogram 3.x Framework)
• ⌨️ Inline Keyboards 互動

<b>使用方式/How to use:</b>
直接輸入地點名稱即可搜尋!
Just type a location name to search!

<b>範例輸入/Examples:</b>
• 東京 或 Tokyo
• 巴黎 或 Paris
• 台北101
• 香港

輸入 /help 查看更多資訊
Type /help for more information

⚠️ <i>此 Bot 純粹用於程式學習與實驗</i>
"""
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    處理 /help 指令
    """
    help_text = """
📖 <b>城市指南 Bot 使用說明</b>

<b>指令列表/Commands:</b>
• /start - 開始使用
• /help - 顯示此說明

<b>搜尋功能/Search:</b>
直接輸入任何地點關鍵字：
• 城市名稱 (如: 東京、巴黎、紐約)
• 景點名稱 (如: 淺草寺、艾菲爾鐵塔)
• 區域名稱 (如: 士林夜市、明洞)

<b>搜尋範例/Search Examples:</b>
• 東京 → 東京相關景點
• 台北101 → 台北101大樓
• 香港 → 香港景點
• Paris → 巴黎景點

<b>匹配邏輯/Matching Logic:</b>
• 支援中英文搜尋
• 使用模糊匹配，相似度 ≥70% 即顯示
• 優先級：子區域 &gt; 區域 &gt; 城市 &gt; 國家

<b>資料來源/Data Source:</b>
基於公開旅遊資訊與 Wikipedia 景點列表

⚠️ <i>資料僅供學習參考，可能不完全準確</i>
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(F.text)
async def handle_search(message: Message) -> None:
    """
    處理一般文字訊息（搜尋查詢）
    """
    query = message.text.strip()
    
    if not query or len(query) < 1:
        await message.answer(
            "⚠️ 請輸入地點關鍵字\n"
            "⚠️ Please enter a location keyword\n\n"
            "範例/Example: 東京、巴黎、Bangkok",
            parse_mode=ParseMode.HTML
        )
        return
    
    db = get_database()
    results = db.search(query, threshold=70, max_results=6)
    
    if not results:
        samples = db.get_sample_locations(5)
        samples_text = "\n".join([f"• {s}" for s in samples])
        
        no_result_text = f"""
❌ <b>無匹配記錄</b>

找不到與「{escape_html(query)}」相關的地點。

資料可能已過期，或請嘗試更精確的關鍵字。

<b>建議嘗試/Try these:</b>
{samples_text}

💡 也可以試試：東京、巴黎、香港、台北
"""
        await message.answer(no_result_text, parse_mode=ParseMode.HTML)
        return
    
    user_id = message.from_user.id
    _recent_results[user_id] = results
    
    if len(results) == 1:
        response = format_location_html(results[0], detailed=True)
        await message.answer(response, parse_mode=ParseMode.HTML)
    else:
        header = f"🔍 <b>找到 {len(results)} 個結果</b>\n\n"
        
        summaries = []
        for i, loc in enumerate(results, 1):
            nickname = loc.get("nickname", loc.get("area", ""))
            city = loc.get("city", "")
            country = loc.get("country", "")
            has_tg = "📱" if loc.get("tg_contacts") else ""
            summaries.append(
                f"{i}. <b>{escape_html(nickname)}</b> {has_tg}\n"
                f"   {escape_html(city)}, {escape_html(country)}"
            )
        
        response = header + "\n\n".join(summaries)
        response += "\n\n<i>點擊下方按鈕查看詳細</i>"
        
        keyboard = create_results_keyboard(results)
        await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)


@router.callback_query(F.data.startswith("detail_"))
async def handle_detail_callback(callback: CallbackQuery) -> None:
    """
    處理詳細查看回調
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    results = _recent_results.get(user_id, [])
    
    try:
        index = int(callback.data.split("_")[1])
        if 0 <= index < len(results):
            location = results[index]
            response = format_location_html(location, detailed=True)
            await callback.message.edit_text(
                response,
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_keyboard()
            )
    except (ValueError, IndexError):
        await callback.message.answer("⚠️ 無法載入詳細資訊")


@router.callback_query(F.data.startswith("region_"))
async def handle_region_callback(callback: CallbackQuery) -> None:
    """
    處理地區篩選回調
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
        await callback.message.answer("該地區暫無資料")
        return
    
    user_id = callback.from_user.id
    _recent_results[user_id] = results
    
    header = f"📍 <b>{region_names.get(region, region)} 熱門景點</b>\n\n"
    
    summaries = []
    for i, loc in enumerate(results, 1):
        nickname = loc.get("nickname", loc.get("area", ""))
        city = loc.get("city", "")
        has_tg = "📱" if loc.get("tg_contacts") else ""
        summaries.append(
            f"{i}. <b>{escape_html(nickname)}</b> {has_tg}\n"
            f"   {escape_html(city)}"
        )
    
    response = header + "\n\n".join(summaries)
    keyboard = create_results_keyboard(results, show_regions=False)
    
    await callback.message.edit_text(
        response,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back")
async def handle_back_callback(callback: CallbackQuery) -> None:
    """
    處理返回按鈕回調
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
    
    header = f"🔍 <b>找到 {len(results)} 個結果</b>\n\n"
    
    summaries = []
    for i, loc in enumerate(results, 1):
        nickname = loc.get("nickname", loc.get("area", ""))
        city = loc.get("city", "")
        country = loc.get("country", "")
        has_tg = "📱" if loc.get("tg_contacts") else ""
        summaries.append(
            f"{i}. <b>{escape_html(nickname)}</b> {has_tg}\n"
            f"   {escape_html(city)}, {escape_html(country)}"
        )
    
    response = header + "\n\n".join(summaries)
    response += "\n\n<i>點擊下方按鈕查看詳細</i>"
    
    keyboard = create_results_keyboard(results)
    await callback.message.edit_text(
        response,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
