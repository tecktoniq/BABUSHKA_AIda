from aiogram import Router, F
from aiogram.types import FSInputFile, Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import os

from database.db import get_user, create_user, update_user, is_subscribed, has_trial
from data.phrases import get, WELCOME
from data.cards import get_zodiac, get_soul_card, get_soul_card_calculation, normalize_birthdate
from services.ai import get_soul_card_analysis

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WELCOME_IMAGE_PATH = "assets/AIDA.jpg"

BTN_READING = "🃏 Сделать расклад"
BTN_SOUL = "🔢 Анализ карты судьбы"
BTN_SUBSCRIBE = "⭐ Открыть подписку"
BTN_MY_SUBSCRIPTION = "💎 Моя подписка"
BTN_ABOUT = "📖 Что умеет Бабушка?"
BTN_MY_DATA = "⚙️ Мои данные"
BTN_ADMIN = "🛠 Админ-панель"


class Onboarding(StatesGroup):
    waiting_name = State()
    waiting_birthdate = State()


def reply_menu_kb(user_id: int | None = None):
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_READING)
    kb.button(text=BTN_SOUL)
    if user_id and is_subscribed(user_id):
        kb.button(text=BTN_MY_SUBSCRIPTION)
    else:
        kb.button(text=BTN_SUBSCRIBE)
    kb.button(text=BTN_ABOUT)
    kb.button(text=BTN_MY_DATA)
    if user_id == ADMIN_ID:
        kb.button(text=BTN_ADMIN)
        kb.adjust(2, 2, 2)
    else:
        kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    user_before_start = get_user(user_id)

    # Проверяем реферала
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id != user_id and not user_before_start:
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
            reply_markup=reply_menu_kb(user_id)
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
        reply_markup=reply_menu_kb(message.from_user.id)
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
        "🔮 Главное меню Бабушки AIda\n\nВыбери действие на клавиатуре ниже."
    )
    await callback.message.answer(
        "Кнопки меню уже под рукой, дитя моё.",
        reply_markup=reply_menu_kb(callback.from_user.id)
    )


async def send_my_data(target, user_id: int, edit: bool = False):
    user = get_user(user_id)
    if not user or not user["name"]:
        if edit:
            await target.answer("Сначала пройди регистрацию!")
        else:
            await target.answer("Сначала пройди регистрацию!")
        return
    if user["birthdate"]:
        zodiac = get_zodiac(user["birthdate"])
        if zodiac != user["zodiac"]:
            update_user(user_id, zodiac=zodiac)
            user = get_user(user_id)

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

    sub_status = "✅ Активна" if is_subscribed(user_id) else f"❌ Нет (осталось пробных: {user['trial_left']})"

    text = (
        f"⚙️ Твои данные:\n\n"
        f"Имя: {user['name']}\n"
        f"Дата рождения: {user['birthdate']}\n"
        f"Знак зодиака: {user['zodiac']}\n"
        f"Карта судьбы: {soul_card_name} 🔮\n"
        f"Подписка: {sub_status}"
    )
    if edit:
        await target.edit_text(text, reply_markup=kb.as_markup())
    else:
        await target.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "my_data")
async def my_data(callback: CallbackQuery):
    await send_my_data(callback.message, callback.from_user.id, edit=True)


@router.message(F.text == BTN_READING)
async def menu_reading(message: Message, state: FSMContext):
    from handlers.reading import start_reading_from_message
    await start_reading_from_message(message, state)


@router.message(F.text == BTN_SUBSCRIBE)
async def menu_subscription(message: Message):
    from handlers.subscription import subscription_kb
    user = get_user(message.from_user.id)
    name = user["name"] if user and user["name"] else "дитя моё"
    await message.answer(
        f"✨ Открой всю силу Бабушки AIda, {name}!\n\n"
        f"🃏 Больше раскладов с живым толкованием\n"
        f"🔢 Карта судьбы и личные подсказки\n"
        f"📚 История твоих раскладов\n\n"
        f"Выбери подходящий вариант:",
        reply_markup=subscription_kb()
    )


@router.message(F.text == BTN_MY_SUBSCRIPTION)
async def menu_my_subscription(message: Message):
    from handlers.subscription import subscription_kb
    await message.answer(
        "💎 Твоя подписка активна.\n\n"
        "Если хочешь продлить её заранее или докупить отдельный расклад, выбери вариант ниже:",
        reply_markup=subscription_kb()
    )


@router.message(F.text == BTN_ABOUT)
async def menu_about(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    await message.answer(
        "🔮 Что умеет Бабушка AIda:\n\n"
        "🃏 Расклад Таро — прошлое, настоящее, будущее\n"
        "💕 На любовь и отношения\n"
        "💰 На деньги и карьеру\n"
        "🌙 На ситуацию в жизни\n"
        "✍️ На твой личный вопрос\n\n"
        "Для подписчиков:\n"
        "🌅 Персональный гороскоп\n"
        "🔢 Анализ карты судьбы\n"
        "📚 История раскладов",
        reply_markup=kb.as_markup()
    )


@router.message(F.text == BTN_MY_DATA)
async def menu_my_data(message: Message):
    await send_my_data(message, message.from_user.id)


@router.message(F.text == BTN_ADMIN)
async def menu_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    from handlers.admin import admin_panel_kb
    await message.answer(
        "🛠 Админ-панель Бабушки AIda\n\n"
        "Быстрые действия доступны кнопками. Команды с ID можно отправлять текстом.",
        reply_markup=admin_panel_kb()
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
        f"Поделись ссылкой — приглашённый человек сможет открыть Бабушку AIda по твоему приглашению.\n"
        f"Когда он впервые оплатит Stars, ты получишь +7 дней к подписке 🔮\n\n"
        f"Бонус начисляется только после первой оплаты, не просто за переход по ссылке.",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )


async def send_soul_card_analysis(target, user_id: int, edit: bool = False):
    user = get_user(user_id)
    if not user or not user["name"] or not user["birthdate"]:
        if edit:
            await target.answer("Сначала пройди регистрацию!")
        else:
            await target.answer("Сначала пройди регистрацию!")
        return

    calculation = get_soul_card_calculation(user["birthdate"])
    soul_card = get_soul_card(user["birthdate"])
    digits_text = " + ".join(str(digit) for digit in calculation["digits"])
    steps_text = " → ".join(str(step) for step in calculation["steps"])

    intro_text = (
        "🔢 Считаю карту судьбы...\n\n"
        f"Дата: {calculation['birthdate']}\n"
        f"Цифры: {digits_text}\n"
        f"Расчёт: {steps_text}\n"
        f"Карта: {soul_card['name']} 🔮\n\n"
        "Сейчас Бабушка AIda раскроет её смысл."
    )
    if edit:
        await target.edit_text(intro_text)
    else:
        await target.answer(intro_text)

    analysis = await get_soul_card_analysis(
        name=user["name"],
        birthdate=calculation["birthdate"],
        calculation=calculation,
        soul_card=soul_card,
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Главное меню", callback_data="main_menu")

    await target.answer(
        f"🔢 Карта судьбы: {soul_card['name']}\n\n"
        f"Логика расчёта:\n"
        f"{digits_text} = {calculation['first_sum']}\n"
        f"Приведение к старшему аркану: {steps_text}\n\n"
        f"🔮 Бабушка AIda говорит:\n\n{analysis}",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "soul_card_analysis")
async def soul_card_analysis(callback: CallbackQuery):
    await send_soul_card_analysis(callback.message, callback.from_user.id, edit=True)


@router.message(F.text == BTN_SOUL)
async def menu_soul_card_analysis(message: Message):
    await send_soul_card_analysis(message, message.from_user.id)
