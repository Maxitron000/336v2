
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from handlers import user, admin, stats, notifications
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from services.db_service import DBService

logging.basicConfig(level=logging.INFO)

async def init_database():
    """Инициализация базы данных"""
    try:
        # Создание таблиц если их нет
        import aiosqlite
        from config import DB_NAME
        
        async with aiosqlite.connect(DB_NAME) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица записей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    comment TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            await db.commit()
            logging.info("База данных инициализирована")
    except Exception as e:
        logging.error(f"Ошибка инициализации БД: {e}")

async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск/регистрация"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="admin", description="Админ-панель"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="export", description="Экспорт в Excel"),
        BotCommand(command="help", description="Справка")
    ]
    await bot.set_my_commands(commands)

async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация БД
    await init_database()
    
    # Подключение роутеров
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)
    dp.include_router(notifications.router)

    scheduler = AsyncIOScheduler()
    from handlers.notifications import setup_scheduler
    setup_scheduler(bot)

    await on_startup(bot)
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
