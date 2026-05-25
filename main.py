import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database.db import init_db
from handlers.start import router as start_router
from handlers.reading import router as reading_router
from handlers.subscription import router as subscription_router
from handlers.admin import router as admin_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")


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

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
