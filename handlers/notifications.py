from aiogram import Router, Bot
from aiogram.types import Message
from services.db_service import DatabaseService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

router = Router()
db = DatabaseService()
scheduler = AsyncIOScheduler()

async def send_reminders(bot: Bot):
    """Отправка напоминаний"""
    try:
        # Получаем всех пользователей
        users = db.get_all_users()
        reminder_text = "🔔 Напоминание: не забудьте отметиться в системе табеля!"

        for user in users:
            try:
                await bot.send_message(user['id'], reminder_text)
            except Exception as e:
                logging.error(f"Ошибка отправки напоминания пользователю {user['id']}: {e}")

        logging.info(f"Отправлено напоминаний: {len(users)}")
    except Exception as e:
        logging.error(f"Ошибка отправки напоминаний: {e}")

async def cleanup_old_records():
    """Очистка старых записей"""
    try:
        deleted_count = db.cleanup_old_records(days=180)  # Удаляем записи старше 6 месяцев
        logging.info(f"Очищено старых записей: {deleted_count}")
    except Exception as e:
        logging.error(f"Ошибка очистки записей: {e}")

def setup_scheduler(bot: Bot):
    """Настройка планировщика"""
    try:
        # Добавление задач в планировщик
        scheduler.add_job(
            send_reminders,
            'cron',
            hour=18,
            minute=30,
            args=[bot],
            id='reminder_job'
        )

        scheduler.add_job(
            cleanup_old_records,
            'cron',
            hour=3,
            minute=0,
            id='cleanup_job'
        )

        scheduler.start()
        logging.info("Планировщик уведомлений запущен")

    except Exception as e:
        logging.error(f"Ошибка настройки планировщика: {e}")