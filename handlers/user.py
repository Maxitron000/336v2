import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID, LOCATIONS
from datetime import datetime
import logging

router = Router()

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_custom_location = State()

# Инициализация базы данных
db = DatabaseService()

def get_main_menu_keyboard(is_admin: bool = False):
    """Создать главное меню"""
    keyboard = [
        [
            InlineKeyboardButton(text="❌ Убыл", callback_data="action_leave"),
            InlineKeyboardButton(text="✅ Прибыл", callback_data="action_arrive")
        ],
        [InlineKeyboardButton(text="📋 Мой журнал", callback_data="show_journal")]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_location_keyboard(action: str):
    """Создать клавиатуру локаций"""
    keyboard = []
    for i in range(0, len(LOCATIONS), 2):
        row = []
        for j in range(i, min(i + 2, len(LOCATIONS))):
            location = LOCATIONS[j]
            row.append(InlineKeyboardButton(
                text=location,
                callback_data=f"location_{action}_{location}"
            ))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_keyboard():
    """Создать клавиатуру журнала"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user = message.from_user
    user_id = user.id
    username = user.username or f"user_{user_id}"

    # Проверяем, зарегистрирован ли пользователь
    existing_user = db.get_user(user_id)

    if not existing_user:
        # Запрашиваем ФИО
        await state.set_state(UserStates.waiting_for_name)
        await message.answer(
            "🎖️ Добро пожаловать в систему электронного табеля!\n\n"
            "Для регистрации введите ваше ФИО в формате:\n"
            "Фамилия И.О.\n\n"
            "Пример: Иванов И.И."
        )
        return

    # Пользователь уже зарегистрирован
    is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
    await message.answer(
        "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin)
    )

@router.message(StateFilter(UserStates.waiting_for_name))
async def handle_name_input(message: Message, state: FSMContext):
    """Обработка ввода ФИО"""
    user = message.from_user
    user_id = user.id
    username = user.username or f"user_{user_id}"
    full_name = message.text.strip()

    # Валидация формата ФИО
    if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', full_name):
        await message.answer(
            "❌ Неверный формат ФИО!\n\n"
            "Правильный формат: Фамилия И.О.\n"
            "Пример: Иванов И.И.\n\n"
            "Попробуйте еще раз:"
        )
        return

    # Сохраняем пользователя
    if db.add_user(user_id, username, full_name):
        await state.clear()
        is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
        await message.answer(
            f"✅ Регистрация успешно завершена!\n"
            f"👤 Добро пожаловать, {full_name}!"
        )
        await message.answer(
            "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    else:
        await message.answer("❌ Ошибка при регистрации. Попробуйте еще раз.")

@router.message(StateFilter(UserStates.waiting_for_custom_location))
async def handle_custom_location(message: Message, state: FSMContext):
    """Обработка ввода кастомной локации"""
    custom_location = message.text.strip()

    if len(custom_location) < 3 or len(custom_location) > 50:
        await message.answer(
            "Название локации должно быть от 3 до 50 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    # Получаем сохраненные данные
    user_data = await state.get_data()
    action = user_data.get('action')
    user_id = message.from_user.id

    # Добавляем запись
    if db.add_record(user_id, action, custom_location):
        await state.clear()

        action_text = "убыл" if action == "убыл" else "прибыл"
        await message.answer(
            f"✅ Запись добавлена!\n"
            f"Действие: {action_text}\n"
            f"Локация: {custom_location}\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
        await message.answer(
            "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    else:
        await message.answer("❌ Ошибка при добавлении записи.")

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Показать главное меню"""
    user_id = callback.from_user.id
    is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID

    await callback.message.edit_text(
        "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("action_"))
async def callback_action_selection(callback: CallbackQuery):
    """Обработка выбора действия"""
    user_id = callback.from_user.id

    if "arrive" in callback.data:
        # Для "Прибыл" сразу добавляем запись "в части"
        action = "в части"
        location = "Часть"

        if db.add_record(user_id, action, location):
            await callback.message.edit_text(
                f"✅ Статус обновлен!\n"
                f"📍 Вы в части\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

            # Показываем главное меню через 2 секунды
            await asyncio.sleep(2)
            is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
            await callback.message.edit_text(
                "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
        else:
            await callback.message.edit_text("❌ Ошибка при добавлении записи.")
    else:
        # Для "Убыл" показываем выбор локаций
        await callback.message.edit_text(
            "Выберите локацию, куда вы убыли:",
            reply_markup=get_location_keyboard("убыл")
        )

    await callback.answer()

@router.callback_query(F.data.startswith("location_"))
async def callback_location_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора локации"""
    parts = callback.data.split("_", 2)
    action = parts[1]
    location = parts[2]

    user_id = callback.from_user.id

    if location == "📝 Другое":
        # Запрашиваем кастомную локацию
        await state.set_state(UserStates.waiting_for_custom_location)
        await state.update_data(action=action)

        await callback.message.edit_text(
            "Введите название локации:\n\n"
            "Примеры:\n"
            "• Дом родителей\n"
            "• Торговый центр\n"
            "• Кафе\n\n"
            "Введите название:"
        )
        await callback.answer()
        return

    # Добавляем запись
    if db.add_record(user_id, action, location):
        action_text = "убыл" if action == "убыл" else "прибыл"
        await callback.message.edit_text(
            f"✅ Запись добавлена!\n"
            f"Действие: {action_text}\n"
            f"Локация: {location}\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        # Показываем главное меню через 2 секунды
        await asyncio.sleep(2)
        is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
        await callback.message.edit_text(
            "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    else:
        await callback.message.edit_text("❌ Ошибка при добавлении записи.")

    await callback.answer()

@router.callback_query(F.data == "show_journal")
async def callback_show_journal(callback: CallbackQuery):
    """Показать журнал пользователя"""
    user_id = callback.from_user.id
    records = db.get_user_records(user_id, 5)

    if not records:
        text = "📋 Ваш журнал пуст.\nУ вас пока нет записей."
    else:
        text = "📋 Ваш журнал (последние 5 записей):\n\n"
        for record in records:
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            formatted_time = timestamp.strftime('%d.%m %H:%M')
            action_emoji = "🔴" if record['action'] == "убыл" else "🟢"
            text += f"{action_emoji} {record['action']} - {record['location']}\n"
            text += f"⏰ {formatted_time}\n\n"

    await callback.message.edit_text(text, reply_markup=get_journal_keyboard())
    await callback.answer()

# Обработчик неизвестных сообщений
@router.message()
async def handle_unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    await message.answer("Используйте кнопки меню для навигации.")