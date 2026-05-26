import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.cards import draw_cards, get_zodiac
from database.db import (
    get_saved_daily_horoscope,
    get_daily_horoscope_users,
    mark_daily_horoscope_sent,
    save_daily_horoscope,
)
from services.ai import get_daily_horoscope

logger = logging.getLogger(__name__)
MOSCOW_TZ = timezone(timedelta(hours=3))
HOROSCOPE_HOUR_MSK = 8


def horoscope_kb(auto: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="🃏 Сделать расклад", callback_data="start_reading")
    kb.button(text="⚡ Быстрый ответ", callback_data="quick_reading")
    if auto:
        kb.button(text="🔕 Выключить утренний гороскоп", callback_data="toggle_daily_horoscope")
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def get_horoscope_period(now: datetime | None = None) -> str:
    now = now or datetime.now(MOSCOW_TZ)
    if now.hour < HOROSCOPE_HOUR_MSK:
        now = now - timedelta(days=1)
    return now.date().isoformat()


async def get_or_create_daily_horoscope(user):
    period_date = get_horoscope_period()
    saved = get_saved_daily_horoscope(user["user_id"], period_date)
    if saved:
        return saved, False

    zodiac = get_zodiac(user["birthdate"])
    card = draw_cards(1)[0]
    analysis = await get_daily_horoscope(
        name=user["name"],
        zodiac=zodiac,
        card_name=card["name"],
        card_meaning=card["meaning"],
    )
    save_daily_horoscope(user["user_id"], period_date, zodiac, card, analysis)
    return get_saved_daily_horoscope(user["user_id"], period_date), True


async def send_daily_horoscope(bot: Bot, user, auto: bool = False):
    horoscope, created = await get_or_create_daily_horoscope(user)

    reversed_label = f"🔄 {horoscope['card_position']}" if "перев" in horoscope["card_position"].lower() else f"⬆️ {horoscope['card_position']}"
    reused_note = "" if created else "\n\nЭто твой уже открытый гороскоп дня. Новый появится после 08:00 МСК."
    caption = (
        "🌅 Гороскоп дня от Бабушки AIda\n\n"
        f"Знак: {horoscope['zodiac']}\n"
        f"🃏 Карта дня: {horoscope['card_name']}\n"
        f"{reversed_label}"
    )
    try:
        await bot.send_photo(user["user_id"], photo=horoscope["card_image_url"], caption=caption)
    except Exception as exc:
        logger.warning("Failed to send horoscope card to %s: %s", user["user_id"], exc)
        await bot.send_message(user["user_id"], f"{caption}\n\nКарта: {horoscope['card_image_url']}")

    await bot.send_message(
        user["user_id"],
        f"🔮 Бабушка AIda говорит:\n\n{horoscope['text']}{reused_note}",
        reply_markup=horoscope_kb(auto=auto),
    )


async def daily_horoscope_loop(bot: Bot):
    while True:
        try:
            now = datetime.now(MOSCOW_TZ)
            if now.hour == HOROSCOPE_HOUR_MSK:
                today = get_horoscope_period(now)
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
