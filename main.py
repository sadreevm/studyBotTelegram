import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from bot.config import Config
from bot.handlers import routes
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.storage.memory import MemoryStorage

from bot.db.database import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()          # Логирование в консоль
    ]
)

storage = MemoryStorage()

# Инициализация бота и диспетчера
bot = Bot(
    token=Config.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
# setup_handlers(dp)

# Запуск бота[]
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