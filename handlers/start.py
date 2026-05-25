from aiogram import Router, F
from aiogram.types import FSInputFile, Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

from database.db import get_user, create_user, update_user, is_subscribed, has_trial
from data.phrases import get, WELCOME
from data.cards import get_zodiac, get_soul_card, get_soul_card_calculation, normalize_birthdate
from services.ai import get_soul_card_analysis

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WELCOME_IMAGE_PATH = "assets/AIDA.jpg"


class Onboarding(StatesGroup):
    waiting_name = State()
    waiting_birthdate = State()


def main_menu_kb(user_id: int | None = None):
    kb = InlineKeyboardBuilder()
    kb.button(text="🃏 Сделать расклад", callback_data="start_reading")
    kb.button(text="🔢 Анализ карты судьбы", callback_data="soul_card_analysis")
    kb.button(text="⭐ Открыть подписку", callback_data="subscription")
    kb.button(text="📖 Что умеет бабушка?", callback_data="about")
    kb.button(text="⚙️ Мои данные", callback_data="my_data")
    if user_id == ADMIN_ID:
        kb.button(text="🔧 Админ-панель", callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    # Проверяем реферала
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id != user_id:
            await state.update_data(referrer_id=referrer_id)

    create_user(user_id, username)
    user = get_user(user_id)

    # Если уже зарегистрирован — показываем меню
    if user and user["name"]:
        if user["birthdate"]:
            zodiac = get_zodiac(user["birthdate"])
            if zodiac != user["zodiac"]:
                update_user(user_id, zodiac=zodiac)
        await message.answer(
            f"🔮 С возвращением, {user['name']}!\n\nБабушка AIda рада тебя видеть снова...",
            reply_markup=main_menu_kb(user_id)
        )
        return

    # Новый пользователь — онбординг
    await message.answer_photo(
        photo=FSInputFile(WELCOME_IMAGE_PATH),
        caption=f"{get(WELCOME)}\n\n"
                f"Я гадаю на картах уже сорок лет.\n"
                f"Теперь и здесь, дитя моё.\n\n"
                f"Скажи мне своё имя..."
    )
    await state.set_state(Onboarding.waiting_name)


@router.message(Onboarding.waiting_name)
async def got_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 30:
        await message.answer("Напиши своё настоящее имя, дитя моё... 🕯")
        return

    await state.update_data(name=name)
    await message.answer(
        f"{name}... хорошее имя 🕯\n\n"
        f"Скажи мне свою дату рождения, дитя моё.\n"
        f"(например: 15.03.1990)"
    )
    await state.set_state(Onboarding.waiting_birthdate)


@router.message(Onboarding.waiting_birthdate)
async def got_birthdate(message: Message, state: FSMContext):
    birthdate = message.text.strip()

    try:
        birthdate = normalize_birthdate(birthdate)
    except ValueError:
        await message.answer("Напиши дату в формате ДД.ММ.ГГГГ, дитя моё. Например: 15.03.1990")
        return

    data = await state.get_data()
    name = data["name"]
    zodiac = get_zodiac(birthdate)
    soul_card = get_soul_card(birthdate)

    update_user(
        message.from_user.id,
        name=name,
        birthdate=birthdate,
        zodiac=zodiac,
        soul_card=soul_card["id"]
    )

    # Обработка реферала
    referrer_id = data.get("referrer_id")
    if referrer_id:
        from database.db import add_referral
        add_referral(referrer_id, message.from_user.id)

    await state.clear()

    await message.answer(
        f"✨ Бабушка всё запомнила, {name}!\n\n"
        f"Твой знак: {zodiac}\n"
        f"Карта судьбы: {soul_card['name']} 🔮\n\n"
        f"У тебя есть 3 бесплатных расклада.\n"
        f"Потом бабушка попросит немного звёздочек ⭐",
        reply_markup=main_menu_kb(message.from_user.id)
    )


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="main_menu")
    await callback.message.edit_text(
        "🔮 Что умеет Бабушка AIda:\n\n"
        "🃏 Расклад Таро — прошлое, настоящее, будущее\n"
        "💕 На любовь и отношения\n"
        "💰 На деньги и карьеру\n"
        "🌙 На ситуацию в жизни\n"
        "✍️ Твой личный вопрос\n\n"
        "Только для подписчиков:\n"
        "🌅 Персональный гороскоп каждое утро\n"
        "🔢 Карта судьбы по дате рождения\n"
        "📚 История твоих раскладов\n"
        "🎯 Расклад Да/Нет",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔮 Главное меню Бабушки AIda",
        reply_markup=main_menu_kb(callback.from_user.id)
    )


@router.callback_query(F.data == "my_data")
async def my_data(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not user["name"]:
        await callback.answer("Сначала пройди регистрацию!")
        return
    if user["birthdate"]:
        zodiac = get_zodiac(user["birthdate"])
        if zodiac != user["zodiac"]:
            update_user(callback.from_user.id, zodiac=zodiac)
            user = get_user(callback.from_user.id)

    soul_card_name = "не определена"
    if user["soul_card"] is not None:
        from data.cards import MAJOR_ARCANA
        for card in MAJOR_ARCANA:
            if card["id"] == user["soul_card"]:
                soul_card_name = card["name"]
                break

    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить имя", callback_data="edit_name")
    kb.button(text="📅 Изменить дату рождения", callback_data="edit_birthdate")
    kb.button(text="🔢 Анализ карты судьбы", callback_data="soul_card_analysis")
    kb.button(text="🎁 Моя реферальная ссылка", callback_data="referral")
    kb.button(text="◀️ Назад", callback_data="main_menu")
    kb.adjust(1)

    sub_status = "✅ Активна" if is_subscribed(callback.from_user.id) else f"❌ Нет (осталось пробных: {user['trial_left']})"

    await callback.message.edit_text(
        f"⚙️ Твои данные:\n\n"
        f"Имя: {user['name']}\n"
        f"Дата рождения: {user['birthdate']}\n"
        f"Знак зодиака: {user['zodiac']}\n"
        f"Карта судьбы: {soul_card_name} 🔮\n"
        f"Подписка: {sub_status}",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "referral")
async def referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="my_data")

    await callback.message.edit_text(
        f"🎁 Твоя реферальная ссылка:\n\n"
        f"`{ref_link}`\n\n"
        f"Поделись с подругой — она получит первый месяц за 199 Stars ⭐\n"
        f"А ты получишь +7 дней к подписке 🔮\n\n"
        f"Бонусы накапливаются без ограничений!",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "soul_card_analysis")
async def soul_card_analysis(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not user["name"] or not user["birthdate"]:
        await callback.answer("Сначала пройди регистрацию!")
        return

    calculation = get_soul_card_calculation(user["birthdate"])
    soul_card = get_soul_card(user["birthdate"])
    digits_text = " + ".join(str(digit) for digit in calculation["digits"])
    steps_text = " → ".join(str(step) for step in calculation["steps"])

    await callback.message.edit_text(
        "🔢 Считаю карту судьбы...\n\n"
        f"Дата: {calculation['birthdate']}\n"
        f"Цифры: {digits_text}\n"
        f"Расчёт: {steps_text}\n"
        f"Карта: {soul_card['name']} 🔮\n\n"
        "Сейчас Бабушка AIda даст развёрнутый AI-анализ."
    )

    analysis = await get_soul_card_analysis(
        name=user["name"],
        birthdate=calculation["birthdate"],
        calculation=calculation,
        soul_card=soul_card,
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Главное меню", callback_data="main_menu")

    await callback.message.answer(
        f"🔢 Карта судьбы: {soul_card['name']}\n\n"
        f"Логика расчёта:\n"
        f"{digits_text} = {calculation['first_sum']}\n"
        f"Приведение к старшему аркану: {steps_text}\n\n"
        f"🔮 AI-анализ:\n\n{analysis}",
        reply_markup=kb.as_markup()
    )
