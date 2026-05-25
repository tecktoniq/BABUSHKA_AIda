from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import os

from database.db import (
    get_user, get_all_users, get_paying_users,
    add_subscription, add_bonus_days, get_stats,
    update_user, get_conn
)

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


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
    await message.answer(
        f"👥 Пользователей: {stats['total']}\n"
        f"💳 Платных: {stats['paying']}"
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
        "/users — кол-во пользователей\n"
        "/paying — список платников\n"
        "/user 123456 — инфо о юзере\n"
        "/give_sub 123456 30 — дать подписку\n"
        "/give_trials 123456 3 — добавить расклады\n"
        "/ban 123456 — забанить\n"
        "/unban 123456 — разбанить\n"
        "/broadcast Текст — всем\n"
        "/broadcast_paid Текст — только платным\n"
    )
