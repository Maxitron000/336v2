import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from handlers import user, admin, stats, notifications
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

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
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)
    dp.include_router(notifications.router)

    scheduler = AsyncIOScheduler()
    # scheduler.add_job(..., trigger='cron', ...) # Добавить задачи напоминаний и очистки
    scheduler.start()

    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())