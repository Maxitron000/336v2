from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from services.db_service import DBService
from config import MAIN_ADMIN_ID
from keyboards import get_admin_panel_keyboard, get_back_keyboard
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

        from keyboards import get_admin_panel_keyboard
        
        admin_text = """
🛡️ Админ-панель:

/stats - Показать статистику
/export - Экспорт данных в Excel
        """
        await message.answer(
            admin_text,
            reply_markup=get_admin_panel_keyboard(message.from_user.id == MAIN_ADMIN_ID)
        )
    except Exception as e:
        logging.error(f"Ошибка в cmd_admin: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery):
    """Админ-панель через callback"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора")
            return
        
        await callback.message.edit_text(
            "🛡️ Админ-панель\n\nВыберите действие:",
            reply_markup=get_admin_panel_keyboard(callback.from_user.id == MAIN_ADMIN_ID)
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_panel: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    """Статистика через callback"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора")
            return
        
        stats = await DBService.get_statistics()
        stats_text = f"""
📊 Статистика системы:

👥 Пользователей: {stats.get('users', 0)}
📝 Записей: {stats.get('records', 0)}
        """
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_back_keyboard("admin_panel")
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_stats: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery):
    """Список пользователей через callback"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора")
            return
        
        users = await DBService.get_all_users()
        
        if not users:
            text = "👥 Пользователей нет"
        else:
            text = "👥 Список пользователей:\n\n"
            for user in users:
                admin_mark = "👑" if user['is_admin'] else "👤"
                text += f"{admin_mark} {user['full_name']}\n"
                text += f"   ID: {user['id']}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_panel")
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_users: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "admin_records")
async def callback_admin_records(callback: CallbackQuery):
    """Все записи через callback"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора")
            return
        
        records = await DBService.get_all_records(10)
        
        if not records:
            text = "📝 Записей нет"
        else:
            text = "📝 Последние 10 записей:\n\n"
            for record in records:
                action_emoji = "🚶" if record['action'] == 'убыл' else "🏠"
                text += f"{action_emoji} {record['full_name']}\n"
                text += f"   {record['action']} - {record['location']}\n"
                text += f"   {record['timestamp']}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_panel")
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_records: {e}")
        await callback.answer("Произошла ошибка")