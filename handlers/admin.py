from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель"""
    try:
        if not await is_admin(message.from_user.id):
            await message.answer("❌ У вас нет прав администратора")
            return

        admin_text = """
🛡️ Админ-панель:

/stats - Показать статистику
/export - Экспорт данных в Excel
        """
        await message.answer(admin_text)
    except Exception as e:
        logging.error(f"Ошибка в cmd_admin: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")