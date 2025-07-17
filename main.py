import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import user, admin, stats, notifications
from services.db_service import DatabaseService
from config import BOT_TOKEN
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Основная функция для запуска бота"""
    try:
        # Инициализация базы данных
        db = DatabaseService()
        db.init_db()

        # Создание бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Регистрация роутеров
        dp.include_router(user.router)
        dp.include_router(admin.router)
        dp.include_router(stats.router)
        dp.include_router(notifications.router)

        # Настройка планировщика уведомлений
        notifications.setup_scheduler(bot)

        print("🤖 Бот запущен и готов к работе...")
        print(f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

        # Запуск бота
        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"❌ Ошибка запуска бота: {e}")
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())