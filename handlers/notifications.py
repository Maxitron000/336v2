# handlers/notifications.py
from aiogram import Router
from aiogram.types import Message
from services.db_service import DBService
from utils.localization import get_text

router = Router()

# Здесь будут функции для отправки напоминаний и уведомлений