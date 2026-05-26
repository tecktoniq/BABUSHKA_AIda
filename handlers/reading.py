from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import logging

from database.db import get_user, is_subscribed, has_trial, use_trial, save_reading, get_last_readings
from data.cards import draw_cards
from data.phrases import get, SHUFFLING, FIRST_CARD, SECOND_CARD, THIRD_CARD, VERDICT_INTRO, AFTER_READING
from services.ai import interpret_card, get_verdict, get_quick_card_answer

router = Router()
logger = logging.getLogger(__name__)

TOPICS = {
    "love": "💕 На любовь и отношения",
    "money": "💰 На деньги и карьеру",
    "life": "🌙 На ситуацию в жизни",
    "custom": "✍️ Свой вопрос",
    "yesno": "🎯 Да или Нет",
}

POSITIONS = {
    0: ("🌑 ПРОШЛОЕ", "прошлое"),
    1: ("🌕 НАСТОЯЩЕЕ", "настоящее"),
    2: ("✨ БУДУЩЕЕ", "будущее"),
}

NEXT_CARD_PHRASES = {
    1: SECOND_CARD,
    2: THIRD_CARD,
}


class ReadingState(StatesGroup):
    choosing_topic = State()
    waiting_question = State()
    showing_cards = State()


class QuickReadingState(StatesGroup):
    waiting_question = State()


def topic_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💕 На любовь", callback_data="topic_love")
    kb.button(text="💰 На деньги", callback_data="topic_money")
    kb.button(text="🌙 На ситуацию", callback_data="topic_life")
    kb.button(text="✍️ Свой вопрос", callback_data="topic_custom")
    kb.button(text="◀️ Назад", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def next_card_kb(card_index: int):
    kb = InlineKeyboardBuilder()
    if card_index == 1:
        kb.button(text="🃏 Взять вторую карту", callback_data=f"next_card_{card_index}")
    elif card_index == 2:
        kb.button(text="🃏 Взять третью карту", callback_data=f"next_card_{card_index}")
    return kb.as_markup()


def verdict_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔮 Послушать итог Бабушки", callback_data="get_verdict")
    return kb.as_markup()


def after_reading_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Поделиться раскладом", callback_data="share_reading")
    kb.button(text="⚡ Быстрый ответ", callback_data="quick_reading")
    kb.button(text="🃏 Новый расклад", callback_data="start_reading")
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def subscription_prompt_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Один расклад — 99 Stars", callback_data="buy_single")
    kb.button(text="💫 Подписка месяц — 399 Stars", callback_data="buy_month")
    kb.button(text="🌟 3 месяца — 999 Stars (-20%)", callback_data="buy_3months")
    kb.button(text="◀️ Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def quick_after_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⚡ Ещё вопрос", callback_data="quick_reading")
    kb.button(text="🃏 Большой расклад", callback_data="start_reading")
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data == "start_reading")
async def start_reading(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not user["name"]:
        await callback.answer("Сначала пройди регистрацию!")
        return

    # Проверяем доступ
    if not is_subscribed(callback.from_user.id) and not has_trial(callback.from_user.id):
        await callback.message.edit_text(
            "🔒 Бабушка видит больше...\n\n"
            "Твои бесплатные расклады закончились, дитя моё.\n"
            "Открой подписку чтобы продолжить 🔮",
            reply_markup=subscription_prompt_kb()
        )
        return

    await callback.message.edit_text(
        "О чём тревожится твоё сердце? 🔮\n\n"
        "Выбери тему расклада:",
        reply_markup=topic_kb()
    )
    await state.set_state(ReadingState.choosing_topic)


async def start_reading_from_message(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user["name"]:
        await message.answer("Сначала пройди регистрацию!")
        return

    if not is_subscribed(message.from_user.id) and not has_trial(message.from_user.id):
        await message.answer(
            "🔒 Бабушка видит больше...\n\n"
            "Твои бесплатные расклады закончились, дитя моё.\n"
            "Открой подписку, чтобы продолжить 🔮",
            reply_markup=subscription_prompt_kb()
        )
        return

    await message.answer(
        "О чём тревожится твоё сердце? 🔮\n\n"
        "Выбери тему расклада:",
        reply_markup=topic_kb()
    )
    await state.set_state(ReadingState.choosing_topic)


async def start_quick_reading_from_message(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user["name"]:
        await message.answer("Сначала пройди регистрацию!")
        return

    if not is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Быстрый ответ одной картой открыт только по подписке.\n\n"
            "Это короткое гадание под конкретную ситуацию: ты задаёшь вопрос, Бабушка тянет одну карту и сразу говорит по сути.",
            reply_markup=subscription_prompt_kb()
        )
        return

    await message.answer(
        "⚡ Быстрый ответ одной картой\n\n"
        "Напиши вопрос или ситуацию одним сообщением. Можно про чувства, выбор, работу, деньги или то, что сейчас тревожит."
    )
    await state.set_state(QuickReadingState.waiting_question)


@router.callback_query(F.data == "quick_reading")
async def quick_reading(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not user["name"]:
        await callback.answer("Сначала пройди регистрацию!")
        return

    if not is_subscribed(callback.from_user.id):
        await callback.message.answer(
            "🔒 Быстрый ответ одной картой открыт только по подписке.",
            reply_markup=subscription_prompt_kb()
        )
        await callback.answer()
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "⚡ Напиши вопрос или ситуацию одним сообщением, а Бабушка вытянет одну карту."
    )
    await state.set_state(QuickReadingState.waiting_question)
    await callback.answer()


@router.message(QuickReadingState.waiting_question)
async def got_quick_question(message: Message, state: FSMContext):
    question = message.text.strip()
    if len(question) < 5:
        await message.answer("Дай Бабушке чуть больше ниточки: напиши вопрос или ситуацию подробнее.")
        return

    user = get_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Быстрый ответ одной картой открыт только по подписке.",
            reply_markup=subscription_prompt_kb()
        )
        await state.clear()
        return

    card = draw_cards(1)[0]
    wait_msg = await message.answer("⚡ Бабушка тянет одну карту...")
    await asyncio.sleep(0.7)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    reversed_label = "🔄 перевернутая" if card["is_reversed"] else "⬆️ прямая"
    card_title = f"⚡ Быстрый ответ\n\n🃏 {card['name']}\n{reversed_label}"
    try:
        await message.answer_photo(photo=card["image_url"], caption=card_title)
    except Exception as exc:
        logger.warning("Failed to send quick card image %s: %s", card.get("image_url"), exc)
        await message.answer(f"{card_title}\n\nКарта: {card['image_url']}")

    thinking_msg = await message.answer("🔮 Бабушка AIda всматривается в карту...")
    answer = await get_quick_card_answer(user["name"], question, card)
    try:
        await thinking_msg.delete()
    except Exception:
        pass

    await message.answer(
        f"🔮 Бабушка AIda говорит:\n\n{answer}",
        reply_markup=quick_after_kb()
    )
    await state.clear()


@router.callback_query(F.data.startswith("topic_"))
async def choose_topic(callback: CallbackQuery, state: FSMContext):
    topic_key = callback.data.replace("topic_", "")
    topic_label = TOPICS.get(topic_key, "На ситуацию в жизни")

    await state.update_data(topic_key=topic_key, topic_label=topic_label)

    if topic_key == "custom":
        await callback.message.edit_text(
            "🕯 Напиши свой вопрос бабушке...\n\n"
            "Спрашивай о том, что действительно волнует твоё сердце:"
        )
        await state.set_state(ReadingState.waiting_question)
    else:
        await state.update_data(question=topic_label)
        await _begin_reading(callback.message, state, callback.from_user.id)


@router.message(ReadingState.waiting_question)
async def got_question(message: Message, state: FSMContext):
    question = message.text.strip()
    if len(question) < 5:
        await message.answer("Задай вопрос подробнее, дитя моё... 🕯")
        return
    await state.update_data(question=question)
    await _begin_reading(message, state, message.from_user.id)


async def _begin_reading(msg, state: FSMContext, user_id: int):
    user = get_user(user_id)
    data = await state.get_data()

    # Списываем trial если не подписчик
    if not is_subscribed(user_id):
        use_trial(user_id)

    # Тянем карты
    cards = draw_cards(3)
    await state.update_data(cards=cards, card_index=0, interpretations=[])
    await state.set_state(ReadingState.showing_cards)

    # Тасование
    shuffle_msg = await msg.answer(get(SHUFFLING))
    await asyncio.sleep(2)
    await shuffle_msg.delete()

    # Показываем первую карту
    await _show_card(msg, state, user, cards, 0)


async def _show_card(msg, state: FSMContext, user, cards: list, index: int):
    card = cards[index]
    position_label, position_name = POSITIONS[index]
    data = await state.get_data()
    topic_label = data.get("topic_label", "")
    question = data.get("question", "")

    # Заголовок позиции
    await msg.answer(get([FIRST_CARD, SECOND_CARD, THIRD_CARD][index]))

    await asyncio.sleep(0.5)

    reversed_label = "🔄 Перевёрнутая" if card["is_reversed"] else "⬆️ Прямая"
    card_title = (
        f"{position_label}\n\n"
        f"🃏 {card['name']}\n"
        f"{reversed_label}"
    )

    try:
        await msg.answer_photo(photo=card["image_url"], caption=card_title)
    except Exception as exc:
        logger.warning("Failed to send tarot card image %s: %s", card.get("image_url"), exc)
        await msg.answer(f"{card_title}\n\nКарта: {card['image_url']}")

    thinking_msg = await msg.answer("🔮 Бабушка AIda всматривается в карту...")

    interpretation = await interpret_card(
        name=user["name"],
        card=card,
        position=position_name,
        topic=topic_label,
        question=question
    )
    await thinking_msg.delete()

    # Сохраняем интерпретацию
    interpretations = data.get("interpretations", [])
    interpretations.append(interpretation)
    await state.update_data(interpretations=interpretations, card_index=index + 1)

    # Кнопка следующего шага
    if index < 2:
        kb = next_card_kb(index + 1)
    else:
        kb = verdict_kb()

    await msg.answer(
        f"🔮 Бабушка AIda говорит:\n\n{interpretation}",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("next_card_"))
async def next_card(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("card_index", 0)
    cards = data.get("cards", [])
    user = get_user(callback.from_user.id)

    await callback.message.edit_reply_markup(reply_markup=None)
    await _show_card(callback.message, state, user, cards, index)


@router.callback_query(F.data == "get_verdict")
async def show_verdict(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = get_user(callback.from_user.id)
    cards = data.get("cards", [])
    topic_label = data.get("topic_label", "")
    question = data.get("question", "")
    interpretations = data.get("interpretations", [])

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get(VERDICT_INTRO))
    await asyncio.sleep(1)

    verdict = await get_verdict(
        name=user["name"],
        topic=topic_label,
        question=question,
        cards=cards,
        interpretations=interpretations
    )

    # Сохраняем расклад в базу
    save_reading(
        user_id=callback.from_user.id,
        topic=topic_label,
        question=question,
        card1=f"{cards[0]['name']} ({cards[0]['position_label']})",
        card2=f"{cards[1]['name']} ({cards[1]['position_label']})",
        card3=f"{cards[2]['name']} ({cards[2]['position_label']})",
        verdict=verdict
    )

    await callback.message.answer(
        f"🔮 Бабушка AIda говорит...\n\n{verdict}\n\n"
        f"_{get(AFTER_READING)}_",
        reply_markup=after_reading_kb(),
        parse_mode="Markdown"
    )

    await state.clear()


@router.callback_query(F.data == "share_reading")
async def share_reading(callback: CallbackQuery):
    readings = get_last_readings(callback.from_user.id, limit=1)
    if not readings:
        await callback.answer("Сначала сделай расклад")
        return

    reading = readings[0]
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"
    verdict = reading["verdict"] or ""
    short_verdict = verdict if len(verdict) <= 850 else verdict[:847].rstrip() + "..."

    share_text = (
        "🔮 Смотри, как мне погадала Бабушка AIda\n\n"
        f"Вопрос: {reading['question']}\n\n"
        "Карты расклада:\n"
        f"1. {reading['card1']}\n"
        f"2. {reading['card2']}\n"
        f"3. {reading['card3']}\n\n"
        "Что сказала Бабушка:\n"
        f"{short_verdict}\n\n"
        "Хочешь тоже спросить карты?\n"
        f"{ref_link}"
    )

    await callback.message.answer(
        "Вот красивый текст для пересылки:\n\n"
        f"{share_text}"
    )
    await callback.answer()
