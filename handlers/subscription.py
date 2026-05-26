from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import is_subscribed, add_subscription, get_user, reward_referrer_after_payment

router = Router()

PRICES = {
    "single": {"stars": 99, "days": 0, "label": "Один расклад с толкованием"},
    "month": {"stars": 399, "days": 30, "label": "Подписка на 1 месяц"},
    "3months": {"stars": 999, "days": 90, "label": "Подписка на 3 месяца (-20%)"},
    "ref_month": {"stars": 199, "days": 30, "label": "Подписка на 1 месяц (реферальная)"},
}


def subscription_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Один расклад — 99 Stars", callback_data="buy_single")
    kb.button(text="💫 Месяц — 399 Stars", callback_data="buy_month")
    kb.button(text="🌟 3 месяца — 999 Stars (-20%)", callback_data="buy_3months")
    kb.button(text="◀️ Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data == "subscription")
async def show_subscription(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    name = user["name"] if user and user["name"] else "дитя моё"

    sub_status = ""
    if is_subscribed(callback.from_user.id):
        sub_status = "✅ У тебя уже есть подписка!\n\n"

    await callback.message.edit_text(
        f"{sub_status}"
        f"✨ Открой всю силу Бабушки AIda, {name}!\n\n"
        f"🃏 Безлимитные расклады с живым толкованием\n"
        f"🌅 Персональный гороскоп каждое утро\n"
        f"🔢 Твоя карта судьбы\n"
        f"📚 История всех раскладов\n\n"
        f"Выбери подходящий вариант:",
        reply_markup=subscription_kb()
    )


@router.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):
    plan = callback.data.replace("buy_", "")
    price_data = PRICES.get(plan)
    if not price_data:
        await callback.answer("Неверный план!")
        return

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Бабушка AIda — {price_data['label']}",
        description="Доступ к персональным раскладам Таро с тёплым толкованием 🔮",
        payload=f"sub_{plan}_{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=price_data["label"], amount=price_data["stars"])],
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    plan = parts[1]
    user_id = message.from_user.id

    price_data = PRICES.get(plan, {})
    days = price_data.get("days", 0)

    user = get_user(user_id)
    name = user["name"] if user and user["name"] else "дитя моё"
    from handlers.start import reply_menu_kb

    if plan == "single":
        # Разовый расклад — добавляем 1 trial
        from database.db import update_user
        from database.db import get_conn
        conn = get_conn()
        conn.execute("UPDATE users SET trial_left=trial_left+1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        await message.answer(
            f"✨ Оплата получена, {name}!\n\n"
            f"Бабушка AIda открыла для тебя один расклад 🃏\n"
            f"Нажми 'Сделать расклад' в меню 🔮",
            reply_markup=reply_menu_kb(user_id)
        )
    else:
        add_subscription(user_id, days)
        await message.answer(
            f"🌟 Подписка активирована, {name}!\n\n"
            f"Бабушка AIda теперь всегда с тобой 🔮\n"
            f"Каждое утро тебя ждёт персональный гороскоп 🌅",
            reply_markup=reply_menu_kb(user_id)
        )

    reward = reward_referrer_after_payment(user_id, plan)
    if reward:
        try:
            await message.bot.send_message(
                reward["referrer_id"],
                "🎁 По твоей ссылке пришёл новый покупатель.\n\n"
                f"Бабушка AIda добавила тебе {reward['bonus_days']} дней подписки 🔮"
            )
        except Exception:
            pass
