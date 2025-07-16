
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DBService
from config import LOCATIONS, MAIN_ADMIN_ID
from keyboards import get_main_menu_keyboard, get_location_keyboard, get_back_keyboard
import logging

router = Router()

class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_comment = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    try:
        user = await DBService.get_user(message.from_user.id)
        if user:
            is_admin = user['is_admin'] or message.from_user.id == MAIN_ADMIN_ID
            await message.answer(
                f"Добро пожаловать обратно, {user['full_name']}!\n"
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
        else:
            await message.answer(
                "Добро пожаловать в систему военного табеля!\n"
                "Введите ваше ФИО для регистрации:"
            )
            await state.set_state(UserStates.waiting_for_name)
    except Exception as e:
        logging.error(f"Ошибка в cmd_start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(UserStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени при регистрации"""
    try:
        full_name = message.text.strip()
        if len(full_name) < 3:
            await message.answer("ФИО должно содержать минимум 3 символа. Попробуйте еще раз:")
            return
        
        success = await DBService.add_user(
            message.from_user.id,
            message.from_user.username or "",
            full_name
        )
        
        if success:
            await message.answer(
                f"Регистрация завершена, {full_name}!\n"
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard(False)
            )
            await state.clear()
        else:
            await message.answer("Ошибка регистрации. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка в process_name: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать профиль пользователя"""
    try:
        user = await DBService.get_user(message.from_user.id)
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start")
            return
        
        records = await DBService.get_user_records(message.from_user.id, 5)
        
        profile_text = f"👤 Профиль: {user['full_name']}\n"
        profile_text += f"🆔 ID: {user['id']}\n"
        profile_text += f"🛡️ Админ: {'Да' if user['is_admin'] else 'Нет'}\n\n"
        
        if records:
            profile_text += "📋 Последние записи:\n"
            for record in records:
                action_emoji = "🟢" if record['action'] == 'прибыл' else "🔴"
                profile_text += f"{action_emoji} {record['action']} - {record['location']}\n"
                profile_text += f"   {record['timestamp']}\n"
        else:
            profile_text += "📋 Записей пока нет"
        
        await message.answer(profile_text)
    except Exception as e:
        logging.error(f"Ошибка в cmd_profile: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать справку"""
    help_text = """
🆘 Справка по боту:

/start - Регистрация в системе
/profile - Ваш профиль и последние записи
/admin - Админ-панель (только для админов)
/stats - Статистика (только для админов)
/export - Экспорт данных (только для админов)
/help - Эта справка

📝 Для создания записи используйте кнопки в меню.
    """
    await message.answer(help_text)

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Главное меню"""
    try:
        user = await DBService.get_user(callback.from_user.id)
        if not user:
            await callback.answer("Сначала зарегистрируйтесь командой /start")
            return
        
        is_admin = user['is_admin'] or callback.from_user.id == MAIN_ADMIN_ID
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_main_menu: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith("action_"))
async def callback_action(callback: CallbackQuery):
    """Обработка действий убыл/прибыл"""
    try:
        action = callback.data.split("_")[1]
        action_text = "убыл" if action == "leave" else "прибыл"
        
        await callback.message.edit_text(
            f"Вы выбрали: {action_text}\n"
            "Выберите локацию:",
            reply_markup=get_location_keyboard(action)
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_action: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith("location_"))
async def callback_location(callback: CallbackQuery):
    """Обработка выбора локации"""
    try:
        data_parts = callback.data.split("_", 2)
        action = data_parts[1]
        location = data_parts[2]
        
        action_text = "убыл" if action == "leave" else "прибыл"
        
        success = await DBService.add_record(
            callback.from_user.id,
            action_text,
            location
        )
        
        if success:
            user = await DBService.get_user(callback.from_user.id)
            is_admin = user['is_admin'] or callback.from_user.id == MAIN_ADMIN_ID
            
            await callback.message.edit_text(
                f"✅ Запись добавлена!\n"
                f"🚶 {action_text} - {location}\n"
                f"🕒 Время: {callback.message.date.strftime('%H:%M')}",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при добавлении записи",
                reply_markup=get_back_keyboard()
            )
    except Exception as e:
        logging.error(f"Ошибка в callback_location: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "show_journal")
async def callback_show_journal(callback: CallbackQuery):
    """Показать журнал пользователя"""
    try:
        records = await DBService.get_user_records(callback.from_user.id, 5)
        
        if not records:
            text = "📋 Ваш журнал пуст.\nУ вас пока нет записей."
        else:
            text = "📋 Ваш журнал (последние 5 записей):\n\n"
            for record in records:
                action_emoji = "🚶" if record['action'] == 'убыл' else "🏠"
                text += f"{action_emoji} {record['action']} - {record['location']}\n"
                text += f"🕒 {record['timestamp']}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_show_journal: {e}")
        await callback.answer("Произошла ошибка")
