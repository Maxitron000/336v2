
from aiogram import Router
from aiogram.types import Message
from services.db_service import DBService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import logging

router = Router()

scheduler = AsyncIOScheduler()

async def send_reminders(bot: Bot):
    """Отправка напоминаний"""
    try:
        # TODO: Получать список пользователей и отправлять напоминания
        logging.info("Отправка напоминаний...")
    except Exception as e:
        logging.error(f"Ошибка отправки напоминания: {e}")

async def cleanup_old_records():
    """Очистка старых записей"""
    try:
        # TODO: Реализовать удаление старых записей
        logging.info("Очистка старых записей...")
    except Exception as e:
        logging.error(f"Ошибка очистки записей: {e}")

def setup_scheduler(bot: Bot):
    """Настройка планировщика"""
    try:
        # Добавление задач в планировщик
        # scheduler.add_job(send_reminders, 'cron', hour=18, args=[bot])
        # scheduler.add_job(cleanup_old_records, 'cron', day=1)
        # scheduler.start()
        logging.info("Планировщик настроен")
    except Exception as e:
        logging.error(f"Ошибка настройки планировщика: {e}")
