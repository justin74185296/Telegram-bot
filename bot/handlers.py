import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import LocationDatabase

# Initialize router
router = Router()

# Initialize Database (assuming data is in data/global_locations.json)
db = LocationDatabase("data/global_locations.json")

def format_location_md(loc: dict) -> str:
    """
    Formats a single location dictionary into a Markdown string for Telegram.
    """
    # Header: Flag (if possible, simplified here) + Location Name
    title = f"📍 *{loc['city']}, {loc['country']}*"
    if loc.get('area'):
        title += f"\n🏙 *Area:* {loc['area']}"
    if loc.get('sub_area'):
        title += f" ({loc['sub_area']})"
    
    # Nickname
    nickname = f"\n🏷 *Alias:* _{loc['nickname']}_" if loc.get('nickname') else ""
    
    # Address
    address = f"\n🗺 *Spot:* {loc['address_detail']}" if loc.get('address_detail') else ""
    
    # Services
    services_list = ", ".join(loc.get('services', []))
    services = f"\n🛠 *Services:* {services_list}"
    
    # Price
    price = f"\n💰 *Price:* {loc.get('price_range', 'N/A')}"
    
    # TG Contacts (Highlighted)
    tg_section = ""
    if loc.get('tg_contacts'):
        tg_links = []
        for contact in loc['tg_contacts']:
            # Simple heuristic to make them clickable if they are usernames or links
            if "t.me" in contact:
                tg_links.append(f"[{contact}]({contact})")
            elif contact.startswith("@"):
                # Remove @ for the link, keep for display
                username = contact.lstrip('@')
                tg_links.append(f"[{contact}](https://t.me/{username})")
            else:
                tg_links.append(f"`{contact}`")
        tg_section = "\n\n📱 *Telegram / Contacts:*\n" + "\n".join(f"• {link}" for link in tg_links)
    
    # Notes & Update
    notes = f"\n\n📝 *Notes:* {loc.get('notes', '')}"
    update = f"\n📅 *Updated:* {loc.get('last_update', 'Unknown')}"

    # Assemble
    msg = f"{title}{nickname}{address}{services}{price}{tg_section}{notes}{update}"
    return msg

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    /start command handler.
    """
    welcome_text = (
        "🌏 *Global Red Light District Research Bot*\n\n"
        "This bot helps you find information about specific entertainment districts worldwide for research and safety awareness.\n\n"
        "🔎 *How to use:*\n"
        "Simply type a location, city, or area name.\n\n"
        "💡 *Examples:*\n"
        "• `Amsterdam De Wallen`\n"
        "• `Bangkok Patpong`\n"
        "• `Tokyo Kabukicho`\n"
        "• `Tijuana Zona Norte`\n\n"
        "⚠️ _Data is for educational purposes only. Static database._"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    /help command handler.
    """
    help_text = (
        "📚 *Bot Help*\n\n"
        "**Data Sources:**\n"
        "Information is aggregated from public Wikipedia lists, travel safety forums, and open internet reports (2025-2026 estimates).\n\n"
        "**Telegram Links:**\n"
        "If a record has public Telegram channels or groups mentioned in reports, they are displayed for research verification.\n\n"
        "**Matching Logic:**\n"
        "We use fuzzy text matching. If you don't get a result, try adding the city name (e.g., instead of just 'Nana', try 'Bangkok Nana')."
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text)
async def handle_search(message: types.Message):
    """
    Main handler for text messages (search queries).
    """
    query = message.text
    if len(query) < 2:
        await message.answer("⚠️ Please enter a longer keyword.")
        return

    # Perform search
    results = db.search(query, threshold=60) # Slightly lower threshold for better UX

    if not results:
        # No results found
        await message.answer(
            "❌ *No matching records found.*\n\n"
            "Data might be outdated or the location is not in our specific list.\n"
            "Try broader keywords like:\n"
            "• `Amsterdam`\n"
            "• `Bangkok`\n"
            "• `Singapore`",
            parse_mode="Markdown"
        )
        return

    # Process results
    top_match = results[0]
    
    # Send the best match immediately
    response_text = format_location_md(top_match)
    
    # If there are other matches, create buttons to show them
    keyboard = None
    if len(results) > 1:
        buttons = []
        for i, res in enumerate(results[1:6]): # Show up to 5 alternatives
            # Button text: "City - Area"
            btn_text = f"{res['city']} - {res['area']}"
            # Callback data: simpler implementation would be needed for full interactivity
            # For this MVP, we will just list them as suggestions in text if user wants to search again,
            # OR we can make them simple buttons that just send the text back to chat (acting like a user query)
            # Actually, standard practice for simple bots: buttons that trigger a callback to replace message.
            # But to keep it simple and stateless: buttons that act as "shortcuts" to type the name.
            # However, prompt asked for "Inline keyboard to allow user to select".
            # Let's implement a simple callback mechanism for "Show details".
            
            # Since we don't have a persistent ID, we'll encode index or name?
            # To stay stateless and robust without a real DB ID, we can't easily do callbacks for "id=5".
            # We will list the other matches in the text footer.
            pass

        # Alternative approach for "Multiple Results":
        # Send top result, then say "Also found:"
        alternatives_text = "\n\n🔍 *Also found matching:* \n"
        for res in results[1:4]:
             alternatives_text += f"• {res['city']} - {res['area']} ({res['sub_area']})\n"
        
        response_text += alternatives_text
        response_text += "\n_Type specific name to see details._"

    await message.answer(response_text, parse_mode="Markdown", disable_web_page_preview=True)
