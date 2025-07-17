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
    try:
        user = message.from_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        full_name = message.text.strip() if message.text else ""

        # Проверка на пустое сообщение
        if not full_name:
            await message.answer(
                "❌ Пустое сообщение!\n\n"
                "Введите ваше ФИО в формате: Фамилия И.О.\n"
                "Пример: Иванов И.И."
            )
            return

        # Проверка длины
        if len(full_name) < 5 or len(full_name) > 50:
            await message.answer(
                "❌ ФИО должно содержать от 5 до 50 символов!\n\n"
                f"Введено: {len(full_name)} символов\n"
                "Попробуйте еще раз:"
            )
            return

        # Проверка на недопустимые символы
        if any(char in full_name for char in ['<', '>', '&', '"', "'", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
            await message.answer(
                "❌ ФИО не должно содержать цифры или символы: < > & \" '\n\n"
                "Правильный формат: Фамилия И.О.\n"
                "Пример: Иванов И.И.\n\n"
                "Попробуйте еще раз:"
            )
            return

        # Валидация формата ФИО
        if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', full_name):
            await message.answer(
                "❌ Неверный формат ФИО!\n\n"
                "Правильный формат: Фамилия И.О.\n"
                "Пример: Иванов И.И.\n\n"
                "Требования:\n"
                "• Фамилия с большой буквы\n"
                "• Пробел\n"
                "• Инициалы через точку\n\n"
                "Попробуйте еще раз:"
            )
            return

        # Проверка на уже существующего пользователя
        existing_user = db.get_user(user_id)
        if existing_user:
            await state.clear()
            await message.answer(
                f"❌ Вы уже зарегистрированы как: {existing_user['full_name']}\n"
                "Для смены ФИО обратитесь к администратору."
            )
            is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
            await message.answer(
                "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
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
            await message.answer("❌ Ошибка при регистрации. Попробуйте еще раз или обратитесь к администратору.")
    except Exception as e:
        logging.error(f"Ошибка в handle_name_input: {e}")
        await state.clear()
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте команду /start")

@router.message(StateFilter(UserStates.waiting_for_custom_location))
async def handle_custom_location(message: Message, state: FSMContext):
    """Обработка ввода кастомной локации"""
    try:
        custom_location = message.text.strip() if message.text else ""

        # Проверка на пустое сообщение
        if not custom_location:
            await message.answer(
                "❌ Пустое сообщение!\n"
                "Введите название локации (от 3 до 50 символов):"
            )
            return

        # Проверка длины
        if len(custom_location) < 3 or len(custom_location) > 50:
            await message.answer(
                "❌ Название локации должно быть от 3 до 50 символов.\n"
                f"Сейчас: {len(custom_location)} символов\n"
                "Попробуйте еще раз:"
            )
            return

        # Проверка на недопустимые символы
        if any(char in custom_location for char in ['<', '>', '&', '"', "'"]):
            await message.answer(
                "❌ Название не должно содержать символы: < > & \" '\n"
                "Попробуйте еще раз:"
            )
            return

        # Получаем сохраненные данные
        user_data = await state.get_data()
        action = user_data.get('action', 'убыл')
        user_id = message.from_user.id

        # Проверяем пользователя
        if not db.get_user(user_id):
            await state.clear()
            await message.answer(
                "❌ Вы не зарегистрированы в системе!\n"
                "Отправьте команду /start для регистрации."
            )
            return

        # Для убыли записываем статус "не в части"
        if action == "убыл":
            action = "не в части"

        # Добавляем запись
        if db.add_record(user_id, action, custom_location):
            await state.clear()

            status_text = "не в части" if action == "не в части" else "в части"
            await message.answer(
                f"✅ Статус обновлен!\n"
                f"📍 Статус: {status_text}\n"
                f"🏠 Локация: {custom_location}\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

            is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
            await message.answer(
                "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
        else:
            await message.answer("❌ Ошибка при добавлении записи. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка в handle_custom_location: {e}")
        await state.clear()
        await message.answer("❌ Произошла ошибка. Попробуйте начать заново.")

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
    try:
        user_id = callback.from_user.id
        
        # Проверяем, зарегистрирован ли пользователь
        if not db.get_user(user_id):
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Отправьте команду /start для регистрации."
            )
            await callback.answer()
            return

        if "arrive" in callback.data:
            # Проверяем последнее действие пользователя
            last_records = db.get_user_records(user_id, 1)
            if last_records and last_records[0]['action'] == "в части":
                await callback.message.edit_text(
                    "⚠️ Вы уже отмечены как находящийся в части!\n"
                    "Последняя отметка: " + datetime.fromisoformat(last_records[0]['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
                )
                await asyncio.sleep(2)
                is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
                await callback.message.edit_text(
                    "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                    reply_markup=get_main_menu_keyboard(is_admin)
                )
                await callback.answer()
                return

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
                await callback.message.edit_text("❌ Ошибка при добавлении записи. Попробуйте позже.")
        else:
            # Проверяем последнее действие для "убыл"
            last_records = db.get_user_records(user_id, 1)
            if last_records and last_records[0]['action'] == "не в части":
                await callback.message.edit_text(
                    "⚠️ Вы уже отмечены как отсутствующий!\n"
                    f"Локация: {last_records[0]['location']}\n"
                    "Последняя отметка: " + datetime.fromisoformat(last_records[0]['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
                )
                await asyncio.sleep(2)
                is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
                await callback.message.edit_text(
                    "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                    reply_markup=get_main_menu_keyboard(is_admin)
                )
                await callback.answer()
                return

            # Для "Убыл" показываем выбор локаций
            await callback.message.edit_text(
                "Выберите локацию, куда вы убыли:",
                reply_markup=get_location_keyboard("убыл")
            )

        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_action_selection: {e}")
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()

@router.callback_query(F.data.startswith("location_"))
async def callback_location_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора локации"""
    try:
        parts = callback.data.split("_", 2)
        if len(parts) < 3:
            await callback.message.edit_text("❌ Некорректные данные.")
            await callback.answer()
            return

        action = parts[1]
        location = parts[2]
        user_id = callback.from_user.id

        # Проверяем, зарегистрирован ли пользователь
        if not db.get_user(user_id):
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Отправьте команду /start для регистрации."
            )
            await callback.answer()
            return

        # Валидация действия
        if action not in ["убыл", "прибыл"]:
            await callback.message.edit_text("❌ Некорректное действие.")
            await callback.answer()
            return

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
                "📝 Введите название (от 3 до 50 символов):"
            )
            await callback.answer()
            return

        # Валидация локации
        if not location or len(location.strip()) < 2:
            await callback.message.edit_text("❌ Некорректная локация.")
            await callback.answer()
            return

        # Для убыли записываем статус "не в части"
        if action == "убыл":
            action = "не в части"

        # Добавляем запись
        if db.add_record(user_id, action, location):
            status_text = "не в части" if action == "не в части" else "в части"
            await callback.message.edit_text(
                f"✅ Статус обновлен!\n"
                f"📍 Статус: {status_text}\n"
                f"🏠 Локация: {location}\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

            # Показываем главное меню через 2 секунды
            await asyncio.sleep(2)
            is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
            await callback.message.edit_text(
                "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
        else:
            await callback.message.edit_text("❌ Ошибка при добавлении записи. Попробуйте позже.")

        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_location_selection: {e}")
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()

@router.callback_query(F.data == "show_journal")
async def callback_show_journal(callback: CallbackQuery):
    """Показать журнал пользователя"""
    try:
        user_id = callback.from_user.id
        
        # Проверяем, зарегистрирован ли пользователь
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Отправьте команду /start для регистрации."
            )
            await callback.answer()
            return

        records = db.get_user_records(user_id, 5)

        if not records:
            text = "📋 Ваш журнал пуст.\n\nУ вас пока нет записей.\nОтметьтесь, используя кнопки меню."
        else:
            text = "📋 Ваш журнал (последние 5 записей):\n\n"
            for i, record in enumerate(records, 1):
                try:
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    formatted_time = timestamp.strftime('%d.%m %H:%M')
                    
                    if record['action'] == "не в части":
                        action_emoji = "🔴"
                        action_text = "не в части"
                    elif record['action'] == "в части":
                        action_emoji = "🟢"
                        action_text = "в части"
                    else:
                        # Для старых записей
                        action_emoji = "🔴" if "убыл" in record['action'] else "🟢"
                        action_text = record['action']
                    
                    location = record['location'][:30] + "..." if len(record['location']) > 30 else record['location']
                    text += f"{i}. {action_emoji} {action_text}\n"
                    text += f"📍 {location}\n"
                    text += f"⏰ {formatted_time}\n\n"
                except Exception as e:
                    logging.error(f"Ошибка обработки записи: {e}")
                    continue

        await callback.message.edit_text(text, reply_markup=get_journal_keyboard())
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_show_journal: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке журнала.\nПопробуйте позже.",
            reply_markup=get_journal_keyboard()
        )
        await callback.answer()

# Словарь для отслеживания последних действий пользователей
user_last_action = {}

def can_user_make_action(user_id: int) -> bool:
    """Проверяет, может ли пользователь сделать новое действие (защита от спама)"""
    now = datetime.now()
    if user_id in user_last_action:
        last_action_time = user_last_action[user_id]
        if (now - last_action_time).total_seconds() < 10:  # Минимум 10 секунд между действиями
            return False
    return True

def update_user_last_action(user_id: int):
    """Обновляет время последнего действия пользователя"""
    user_last_action[user_id] = datetime.now()

# Обработчик неизвестных сообщений
@router.message()
async def handle_unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    try:
        user_id = message.from_user.id
        
        # Проверяем частоту сообщений (защита от спама)
        if not can_user_make_action(user_id):
            return  # Игнорируем частые сообщения
        
        update_user_last_action(user_id)
        
        # Проверяем, зарегистрирован ли пользователь
        user = db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы в системе!\n"
                "Отправьте команду /start для регистрации."
            )
        else:
            await message.answer(
                "ℹ️ Используйте кнопки меню для навигации.\n"
                "Для возврата к главному меню отправьте /start"
            )
    except Exception as e:
        logging.error(f"Ошибка в handle_unknown_message: {e}")