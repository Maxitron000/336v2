# handlers/admin.py
from aiogram import Router, types
from aiogram.filters import Command
from services.db_service import DBService
from utils.localization import get_text

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Проверка прав
    user = await DBService.get_user(message.from_user.id)
    if not user or not user.get("is_admin"):
        await message.answer(get_text("error", message.from_user.language_code))
        return
    await message.answer(get_text("main_menu", message.from_user.language_code))
    # Здесь будут кнопки управления пользователями, экспортом и т.д.