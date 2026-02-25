import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Config
from bot.handlers import routes
from bot.db.database import init_db, async_session_maker  # 👈 Импортируем async_session_maker
from bot.middlewares.database import DatabaseMiddleware  # ✅ Правильный путь  # 👈 Наш middleware


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

storage = MemoryStorage()

bot = Bot(
    token=Config.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)

# ==========================================
# 🔧 Подключаем асинхронный middleware для БД
# ==========================================
dp.update.middleware(DatabaseMiddleware(async_session_maker))
# ==========================================

async def main():
    try:
        await init_db()
        logging.info("✅ Таблицы БД созданы/проверены")

        logging.info("Бот запущен")

        for router in routes:
            dp.include_router(router)
            logging.info(f'Router - {router}, connected')

        await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())