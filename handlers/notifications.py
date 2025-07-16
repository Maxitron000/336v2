# handlers/notifications.py
from aiogram import Router
from aiogram.types import Message
from services.db_service import DBService
from utils.localization import get_text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import logging

router = Router()

# Здесь будут функции для отправки напоминаний и уведомлений

scheduler = AsyncIOScheduler()

async def send_reminders(bot: Bot):
    # TODO: Получать список пользователей и отправлять напоминания
    users = []  # await DBService.get_users_for_reminder()
    for user in users:
        try:
            await bot.send_message(user["id"], "Не забудьте отметиться!")
        except Exception as e:
            logging.error(f"Ошибка отправки напоминания: {e}")

async def cleanup_old_records():
    # TODO: Реализовать удаление старых записей
    pass

def setup_scheduler(bot: Bot):
    scheduler.add_job(send_reminders, "cron", hour=18, minute=40, args=[bot])
    scheduler.add_job(cleanup_old_records, "cron", hour=3, args=[])
    scheduler.start()