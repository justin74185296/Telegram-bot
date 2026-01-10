"""
This bot is provided strictly for private programming study, data-structure research,
and offline fuzzy-matching experiments. Do NOT deploy publicly or use it to facilitate
any real-world transactions or services.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from dotenv import load_dotenv

from .database import load_locations
from .handlers import router


async def main() -> None:
    """
    Bot entrypoint.

    Technical constraints:
    - Token is provided via environment variable BOT_TOKEN.
    - Static JSON database is loaded from data/global_locations.json (no network calls).
    """

    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing BOT_TOKEN. Set it in environment or a .env file.")

    data_path = Path(__file__).resolve().parent / "data" / "global_locations.json"
    locations = load_locations(data_path)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    dp.include_router(router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="開始使用"),
            BotCommand(command="help", description="顯示說明"),
        ]
    )

    # Provide loaded locations to handlers via dependency injection.
    await dp.start_polling(bot, locations=locations)


if __name__ == "__main__":
    asyncio.run(main())

