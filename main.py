import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from database.db import init_db
from handlers.start import router as start_router
from handlers.reading import router as reading_router
from handlers.subscription import router as subscription_router
from handlers.admin import router as admin_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


async def setup_bot_commands(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
        ],
        scope=BotCommandScopeDefault(),
    )
    if ADMIN_ID:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Главное меню"),
                BotCommand(command="stats", description="Статистика"),
                BotCommand(command="users", description="Пользователи"),
                BotCommand(command="paying", description="Платные подписчики"),
                BotCommand(command="user", description="Карточка пользователя"),
                BotCommand(command="give_sub", description="Выдать подписку"),
                BotCommand(command="give_trials", description="Добавить расклады"),
                BotCommand(command="ban", description="Забанить"),
                BotCommand(command="unban", description="Разбанить"),
                BotCommand(command="broadcast", description="Рассылка всем"),
                BotCommand(command="broadcast_paid", description="Рассылка платным"),
                BotCommand(command="help_admin", description="Админ-команды"),
            ],
            scope=BotCommandScopeChat(chat_id=ADMIN_ID),
        )


async def notify_admin_startup(bot: Bot):
    if not ADMIN_ID:
        return
    try:
        await bot.send_message(
            ADMIN_ID,
            "🔮 Бабушка AIda запустилась.\n"
            "Я на месте, дитя моё. Можно проверять расклады.",
        )
    except Exception as exc:
        logger.warning("Could not send startup notification to admin: %s", exc)


async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем роутеры
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(reading_router)
    dp.include_router(subscription_router)

    logger.info("🔮 Бабушка AIda запускается...")

    await setup_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await notify_admin_startup(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
