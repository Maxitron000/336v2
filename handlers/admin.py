# handlers/admin.py
from aiogram import Router, types
from aiogram.filters import Command
from services.db_service import DBService
from utils.localization import get_text
import aiosqlite
from config import DB_NAME

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

@router.message(Command("users"))
async def cmd_users(message: types.Message):
    user = await DBService.get_user(message.from_user.id)
    if not user or not user.get("is_admin"):
        await message.answer(get_text("error", message.from_user.language_code))
        return
    # Пример: получить первых 10 пользователей
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, full_name, is_admin FROM users LIMIT 10") as cursor:
            users = [row async for row in cursor]
    text = "\n".join([f"{u[0]}: {u[1]} {'(admin)' if u[2] else ''}" for u in users])
    await message.answer(f"Пользователи:\n{text}")

@router.message(Command("make_admin"))
async def cmd_make_admin(message: types.Message):
    # /make_admin <user_id>
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте: /make_admin <user_id>")
        return
    user_id = int(parts[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        await db.commit()
    await message.answer(f"Пользователь {user_id} теперь админ.")

@router.message(Command("remove_admin"))
async def cmd_remove_admin(message: types.Message):
    # /remove_admin <user_id>
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте: /remove_admin <user_id>")
        return
    user_id = int(parts[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
        await db.commit()
    await message.answer(f"Пользователь {user_id} больше не админ.")