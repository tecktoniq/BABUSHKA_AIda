import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.cards import draw_cards, get_zodiac
from database.db import (
    get_daily_horoscope_users,
    mark_daily_horoscope_sent,
)
from services.ai import get_daily_horoscope

logger = logging.getLogger(__name__)
MOSCOW_TZ = timezone(timedelta(hours=3))


def horoscope_kb(auto: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="🃏 Сделать расклад", callback_data="start_reading")
    kb.button(text="⚡ Быстрый ответ", callback_data="quick_reading")
    if auto:
        kb.button(text="🔕 Выключить утренний гороскоп", callback_data="toggle_daily_horoscope")
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


async def send_daily_horoscope(bot: Bot, user, auto: bool = False):
    zodiac = get_zodiac(user["birthdate"])
    card = draw_cards(1)[0]
    analysis = await get_daily_horoscope(
        name=user["name"],
        zodiac=zodiac,
        card_name=card["name"],
        card_meaning=card["meaning"],
    )

    reversed_label = "🔄 перевернутая" if card["is_reversed"] else "⬆️ прямая"
    caption = (
        "🌅 Гороскоп дня от Бабушки AIda\n\n"
        f"Знак: {zodiac}\n"
        f"🃏 Карта дня: {card['name']}\n"
        f"{reversed_label}"
    )
    try:
        await bot.send_photo(user["user_id"], photo=card["image_url"], caption=caption)
    except Exception as exc:
        logger.warning("Failed to send horoscope card to %s: %s", user["user_id"], exc)
        await bot.send_message(user["user_id"], f"{caption}\n\nКарта: {card['image_url']}")

    await bot.send_message(
        user["user_id"],
        f"🔮 Бабушка AIda говорит:\n\n{analysis}",
        reply_markup=horoscope_kb(auto=auto),
    )


async def daily_horoscope_loop(bot: Bot):
    while True:
        try:
            now = datetime.now(MOSCOW_TZ)
            if now.hour == 10:
                today = now.date().isoformat()
                users = get_daily_horoscope_users(today)
                for user in users:
                    try:
                        await send_daily_horoscope(bot, user, auto=True)
                        mark_daily_horoscope_sent(user["user_id"], today)
                        await asyncio.sleep(0.4)
                    except Exception as exc:
                        logger.warning("Daily horoscope failed for %s: %s", user["user_id"], exc)
                        mark_daily_horoscope_sent(user["user_id"], today)
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Daily horoscope loop error: %s", exc)
            await asyncio.sleep(60)
