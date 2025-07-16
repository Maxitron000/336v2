
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.db_service import DBService
from config import MAIN_ADMIN_ID
import logging

router = Router()

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    if user_id == MAIN_ADMIN_ID:
        return True
    user = await DBService.get_user(user_id)
    return user and user.get('is_admin', False)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показать статистику"""
    try:
        if not await is_admin(message.from_user.id):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        stats = await DBService.get_statistics()
        stats_text = f"""
📊 Статистика системы:

👥 Пользователей: {stats.get('users', 0)}
        """
        await message.answer(stats_text)
    except Exception as e:
        logging.error(f"Ошибка в cmd_stats: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("export"))
async def cmd_export(message: Message):
    """Экспорт данных"""
    try:
        if not await is_admin(message.from_user.id):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        await message.answer("📊 Функция экспорта будет реализована позже")
    except Exception as e:
        logging.error(f"Ошибка в cmd_export: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
