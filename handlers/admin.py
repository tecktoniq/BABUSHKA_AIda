from aiogram import Router, F
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import csv
import io
import os
from datetime import datetime

from database.db import (
    get_user, get_all_users, get_paying_users,
    add_subscription, add_bonus_days, get_stats,
    update_user, get_conn
)

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def admin_panel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data="admin_stats")
    kb.button(text="👥 Пользователи", callback_data="admin_users")
    kb.button(text="📤 Выгрузить пользователей", callback_data="admin_users_export")
    kb.button(text="💳 Платные", callback_data="admin_paying")
    kb.button(text="🔧 Команды", callback_data="admin_help")
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(2, 1, 2, 1)
    return kb.as_markup()


def get_user_subscription_label(user_id: int) -> str:
    if user_id == ADMIN_ID:
        return "админ"
    conn = get_conn()
    now = datetime.now().isoformat()
    sub = conn.execute(
        "SELECT type, expires_at FROM subscriptions WHERE user_id=? AND expires_at>? ORDER BY expires_at DESC LIMIT 1",
        (user_id, now)
    ).fetchone()
    conn.close()
    if not sub:
        return "нет"
    return f"{sub['type']} до {sub['expires_at'][:10]}"


def short_user_row(user) -> str:
    username = f"@{user['username']}" if user["username"] else "без username"
    name = user["name"] or "без имени"
    sub = get_user_subscription_label(user["user_id"])
    return f"• {name} | {username} | ID {user['user_id']} | {sub}"


def build_users_csv() -> bytes:
    users = get_all_users()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "telegram_id",
        "name",
        "username",
        "subscription",
        "birthdate",
        "zodiac",
        "trial_left",
        "registered_at",
    ])
    for user in users:
        writer.writerow([
            user["user_id"],
            user["name"] or "",
            user["username"] or "",
            get_user_subscription_label(user["user_id"]),
            user["birthdate"] or "",
            user["zodiac"] or "",
            user["trial_left"],
            user["registered_at"] or "",
        ])
    return output.getvalue().encode("utf-8-sig")


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🔧 Админ-панель Бабушки AIda\n\n"
        "Быстрые действия доступны кнопками. Команды с ID пользователя можно отправлять текстом.",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    stats = get_stats()
    await callback.message.edit_text(
        f"📊 Статистика Бабушки AIda:\n\n"
        f"👥 Всего пользователей: {stats['total']}\n"
        f"💳 Платных подписчиков: {stats['paying']}\n"
        f"🃏 Всего раскладов: {stats['readings']}\n\n"
        f"💰 Примерный доход: ${stats['paying'] * 6:.0f}/мес",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    stats = get_stats()
    users = get_all_users()
    rows = "\n".join(short_user_row(user) for user in users[:15])
    if not rows:
        rows = "Пользователей пока нет."
    await callback.message.edit_text(
        f"👥 Пользователей: {stats['total']}\n"
        f"💳 Платных: {stats['paying']}\n\n"
        f"{rows}\n\n"
        "Для карточки пользователя отправь:\n"
        "/user 123456\n\n"
        "Для CSV-файла:\n"
        "/users_export",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data == "admin_users_export")
async def admin_users_export(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    csv_bytes = build_users_csv()
    await callback.message.answer_document(
        BufferedInputFile(csv_bytes, filename="babushka_users.csv"),
        caption="📤 Выгрузка пользователей Бабушки AIda"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_paying")
async def admin_paying(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    users = get_paying_users()
    if not users:
        text = "Платных подписчиков пока нет"
    else:
        text = "💳 Платные подписчики:\n\n"
        for u in users[:20]:
            text += f"• {u['name']} (@{u['username']}) — ID: {u['user_id']}\n"
    await callback.message.edit_text(text, reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_help")
async def admin_help(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🔧 Админ-команды:\n\n"
        "/stats — статистика\n"
        "/users — список пользователей\n"
        "/users_export — CSV выгрузка пользователей\n"
        "/paying — список платных\n"
        "/user 123456 — инфо о пользователе\n"
        "/give_sub 123456 30 — дать подписку\n"
        "/give_trials 123456 3 — добавить расклады\n"
        "/ban 123456 — забанить\n"
        "/unban 123456 — разбанить\n"
        "/broadcast текст — всем\n"
        "/broadcast_paid текст — только платным",
        reply_markup=admin_panel_kb()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = get_stats()
    await message.answer(
        f"📊 Статистика Бабушки AIda:\n\n"
        f"👥 Всего пользователей: {stats['total']}\n"
        f"💳 Платных подписчиков: {stats['paying']}\n"
        f"🃏 Всего раскладов: {stats['readings']}\n\n"
        f"💰 Примерный доход: ${stats['paying'] * 6:.0f}/мес"
    )


@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = get_stats()
    users = get_all_users()
    rows = "\n".join(short_user_row(user) for user in users[:20])
    if not rows:
        rows = "Пользователей пока нет."
    await message.answer(
        f"👥 Пользователей: {stats['total']}\n"
        f"💳 Платных: {stats['paying']}\n\n"
        f"{rows}\n\n"
        "Полная выгрузка: /users_export"
    )


@router.message(Command("users_export"))
async def cmd_users_export(message: Message):
    if not is_admin(message.from_user.id):
        return
    csv_bytes = build_users_csv()
    await message.answer_document(
        BufferedInputFile(csv_bytes, filename="babushka_users.csv"),
        caption="📤 Выгрузка пользователей Бабушки AIda"
    )


@router.message(Command("paying"))
async def cmd_paying(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = get_paying_users()
    if not users:
        await message.answer("Платных подписчиков пока нет")
        return
    text = "💳 Платные подписчики:\n\n"
    for u in users[:20]:
        text += f"• {u['name']} (@{u['username']}) — ID: {u['user_id']}\n"
    await message.answer(text)


@router.message(Command("user"))
async def cmd_user(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /user 123456")
        return
    try:
        user_id = int(parts[1])
        user = get_user(user_id)
        if not user:
            await message.answer("Пользователь не найден")
            return
        from database.db import is_subscribed
        sub = "✅ Активна" if is_subscribed(user_id) else "❌ Нет"
        await message.answer(
            f"👤 Пользователь:\n\n"
            f"ID: {user['user_id']}\n"
            f"Имя: {user['name']}\n"
            f"Username: @{user['username']}\n"
            f"Дата рождения: {user['birthdate']}\n"
            f"Знак: {user['zodiac']}\n"
            f"Пробных раскладов: {user['trial_left']}\n"
            f"Подписка: {sub}\n"
            f"Зарегистрирован: {user['registered_at']}"
        )
    except ValueError:
        await message.answer("Неверный ID")


@router.message(Command("give_sub"))
async def cmd_give_sub(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: /give_sub 123456 30")
        return
    try:
        user_id = int(parts[1])
        days = int(parts[2])
        add_subscription(user_id, days, sub_type="admin_gift")
        await message.answer(f"✅ Дано {days} дней подписки пользователю {user_id}")
    except ValueError:
        await message.answer("Неверные данные")


@router.message(Command("give_trials"))
async def cmd_give_trials(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: /give_trials 123456 3")
        return
    try:
        user_id = int(parts[1])
        count = int(parts[2])
        conn = get_conn()
        conn.execute("UPDATE users SET trial_left=trial_left+? WHERE user_id=?", (count, user_id))
        conn.commit()
        conn.close()
        await message.answer(f"✅ Добавлено {count} пробных раскладов пользователю {user_id}")
    except ValueError:
        await message.answer("Неверные данные")


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /ban 123456")
        return
    try:
        user_id = int(parts[1])
        update_user(user_id, is_banned=1)
        await message.answer(f"✅ Пользователь {user_id} заблокирован")
    except ValueError:
        await message.answer("Неверный ID")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /unban 123456")
        return
    try:
        user_id = int(parts[1])
        update_user(user_id, is_banned=0)
        await message.answer(f"✅ Пользователь {user_id} разблокирован")
    except ValueError:
        await message.answer("Неверный ID")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Использование: /broadcast Текст сообщения")
        return
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(user["user_id"], f"📬 Сообщение от Бабушки AIda:\n\n{text}")
            sent += 1
        except:
            failed += 1
    await message.answer(f"✅ Отправлено: {sent}\n❌ Не доставлено: {failed}")


@router.message(Command("broadcast_paid"))
async def cmd_broadcast_paid(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/broadcast_paid", "").strip()
    if not text:
        await message.answer("Использование: /broadcast_paid Текст сообщения")
        return
    users = get_paying_users()
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user["user_id"], f"⭐ {text}")
            sent += 1
        except:
            pass
    await message.answer(f"✅ Отправлено платным подписчикам: {sent}")


@router.message(Command("help_admin"))
async def cmd_help_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🔧 Админ-команды:\n\n"
        "/stats — статистика\n"
        "/users — список пользователей\n"
        "/users_export — CSV выгрузка пользователей\n"
        "/paying — список платников\n"
        "/user 123456 — инфо о юзере\n"
        "/give_sub 123456 30 — дать подписку\n"
        "/give_trials 123456 3 — добавить расклады\n"
        "/ban 123456 — забанить\n"
        "/unban 123456 — разбанить\n"
        "/broadcast Текст — всем\n"
        "/broadcast_paid Текст — только платным\n"
    )
