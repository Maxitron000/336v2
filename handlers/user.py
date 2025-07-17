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
    showing_duplicate_action_warning = State()

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

    # Показываем все локации кроме "Другое"
    locations_to_show = [loc for loc in LOCATIONS if loc != "📝 Другое"]

    for i in range(0, len(locations_to_show), 2):
        row = []
        for j in range(i, min(i + 2, len(locations_to_show))):
            location = locations_to_show[j]
            row.append(InlineKeyboardButton(
                text=location,
                callback_data=f"location_{action}_{location}"
            ))
        keyboard.append(row)

    # Добавляем кнопку "Другое" только для убыли
    if action == "убыл":
        keyboard.append([InlineKeyboardButton(text="📝 Другое", callback_data=f"location_{action}_📝 Другое")])

    # Добавляем кнопку "Назад"
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
    from aiogram.types import ReplyKeyboardRemove

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
            "Пример: Иванов И.И.",
            reply_markup=ReplyKeyboardRemove()
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

        # Проверка длины (минимум 3 символа)
        if len(full_name) < 3 or len(full_name) > 50:
            await message.answer(
                "❌ ФИО должно содержать от 3 до 50 символов!\n\n"
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
        if len(custom_location) < 2 or len(custom_location) > 50:
            await message.answer(
                "❌ Название локации должно быть от 2 до 50 символов.\n"
                f"Сейчас: {len(custom_location)} символов\n"
                "Попробуйте еще раз:"
            )
            return

        # Проверка на недопустимые символы
        if any(char in custom_location for char in ['<', '>', '&', '"', "'", '\n', '\r', '\t']):
            await message.answer(
                "❌ Название не должно содержать символы: < > & \" ' или переносы строк\n"
                "Попробуйте еще раз:"
            )
            return

        # Проверка на только пробелы или цифры
        if custom_location.isspace() or custom_location.isdigit():
            await message.answer(
                "❌ Название локации не может состоять только из пробелов или цифр\n"
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

            # Уведомляем главного админа ПОСЛЕ главного меню
            await send_admin_notification(message.bot, user_id, action, custom_location)
        else:
            await message.answer("❌ Ошибка при добавлении записи. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка в handle_custom_location: {e}")
        await state.clear()
        await message.answer("❌ Произошла ошибка. Попробуйте начать заново.")

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню"""
    user_id = callback.from_user.id
    is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID

    # Очищаем состояние если оно было установлено
    await state.clear()

    await callback.message.edit_text(
        "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("action_"))
async def callback_action_selection(callback: CallbackQuery, state: FSMContext):
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
                await state.set_state(UserStates.showing_duplicate_action_warning)
                last_time = datetime.fromisoformat(last_records[0]['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y в %H:%M')

                keyboard = [
                    [InlineKeyboardButton(text="🔙 Понятно, вернуться в меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

                await callback.message.edit_text(
                    "⚠️ **Повторная отметка о прибытии**\n\n"
                    "Вы уже отмечены как **находящийся в части**\n"
                    f"📍 Текущая локация: **{last_records[0]['location']}**\n"
                    f"⏰ Время отметки: {last_time}\n\n"
                    "💡 **Что делать дальше:**\n"
                    "1️⃣ Если хотите уйти — нажмите «❌ Убыл»\n"
                    "2️⃣ Если ошиблись — просто вернитесь в меню",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                await callback.answer()
                return

            # Для "Прибыл" сразу добавляем запись "в части"
            action = "в части"
            location = "Часть"

            if db.add_record(user_id, action, location):
                # Отправляем сообщение о статусе
                await callback.message.answer(
                    f"✅ Статус обновлен!\n"
                    f"📍 Вы в части\n"
                    f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )

                # Показываем главное меню сразу внизу
                is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
                await callback.message.answer(
                    "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                    reply_markup=get_main_menu_keyboard(is_admin)
                )

                # Уведомляем главного админа ПОСЛЕ главного меню
                await send_admin_notification(callback.message.bot, user_id, action, location)

                # Удаляем старое сообщение с кнопками
                try:
                    await callback.message.delete()
                except:
                    pass
        else:
            # Проверяем последнее действие для "убыл"
            last_records = db.get_user_records(user_id, 1)
            if last_records and last_records[0]['action'] == "не в части":
                await state.set_state(UserStates.showing_duplicate_action_warning)
                last_time = datetime.fromisoformat(last_records[0]['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y в %H:%M')

                keyboard = [
                    [InlineKeyboardButton(text="🔙 Понятно, вернуться в меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

                await callback.message.edit_text(
                    "⚠️ **Повторная отметка об убытии**\n\n"
                    "Вы уже отмечены как **отсутствующий**\n"
                    f"📍 Текущая локация: **{last_records[0]['location']}**\n"
                    f"⏰ Время отметки: {last_time}\n\n"
                    "💡 **Что делать дальше:**\n"
                    "1️⃣ Если вернулись — нажмите «✅ Прибыл»\n"
                    "2️⃣ Если хотите сменить локацию — сначала прибудьте, затем убудьте заново\n"
                    "3️⃣ Если ошиблись — просто вернитесь в меню",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
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
        if not location or len(location.strip()) < 1 or len(location.strip()) > 50:
            await callback.message.edit_text("❌ Некорректная локация (должна быть от 1 до 50 символов).")
            await callback.answer()
            return

        # Дополнительная проверка на безопасность
        if any(char in location for char in ['<', '>', '&', '"', "'", '\n', '\r', '\t']):
            await callback.message.edit_text("❌ Локация содержит недопустимые символы.")
            await callback.answer()
            return

        # Для убыли записываем статус "не в части"
        if action == "убыл":
            action = "не в части"

        # Добавляем запись
        if db.add_record(user_id, action, location):
            status_text = "не в части" if action == "не в части" else "в части"

            # Отправляем сообщение о статусе
            await callback.message.answer(
                f"✅ Статус обновлен!\n"
                f"📍 Статус: {status_text}\n"
                f"🏠 Локация: {location}\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

            # Показываем главное меню сразу внизу
            is_admin = db.is_admin(user_id) or user_id == MAIN_ADMIN_ID
            await callback.message.answer(
                "🎖️ Электронный табель выхода в город\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )

            # Уведомляем главного админа ПОСЛЕ главного меню
            await send_admin_notification(callback.message.bot, user_id, action, location)

            # Удаляем старое сообщение с кнопками
            try:
                await callback.message.delete()
            except:
                pass
        else:
            await callback.message.edit_text("❌ Ошибка при добавлении записи. Попробуйте позже.")

        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_location_selection: {e}")
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте позже.")
        await callback.answer()

@router.message(Command("journal"))
async def cmd_journal(message: Message, state: FSMContext):
    """Команда /journal - показать личный журнал пользователя"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    if not db.get_user(user_id):
        await message.answer(
            "❌ Вы не зарегистрированы в системе!\n"
            "Отправьте команду /start для регистрации."
        )
        return

    try:
        # Получаем последние 10 записей пользователя
        records = db.get_user_records(user_id, limit=10)

        if not records:
            await message.answer(
                "📋 **Мой журнал**\n\n"
                "📝 У вас пока нет записей в журнале.\n"
                "Сделайте первую отметку о прибытии или убытии!",
                parse_mode="Markdown"
            )
            return

        # Формируем красивый текст журнала
        text = "📋 **Мой журнал**\n"
        text += "─" * 25 + "\n\n"

        for i, record in enumerate(records, 1):
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            formatted_date = timestamp.strftime('%d.%m.%Y')
            formatted_time = timestamp.strftime('%H:%M')

            if record['action'] == 'не в части':
                action_emoji = "🚶"
                action_text = "**убыл**"
                status_color = "🔴"
            else:
                action_emoji = "🏠"
                action_text = "**прибыл**"
                status_color = "🟢"

            text += f"{status_color} {i}. {action_emoji} {action_text}\n"
            text += f"📍 {record['location']}\n"
            text += f"📅 {formatted_date} в {formatted_time}\n"

            if i < len(records):
                text += "─" * 20 + "\n\n"

        # Показываем текущий статус
        last_record = records[0]
        if last_record['action'] == 'не в части':
            current_status = "🔴 **Убыл (не в части)**"
        else:
            current_status = "🟢 **Прибыл (в части)**"

        text += f"\n━━━━━━━━━━━━━━━\n"
        text += f"📊 Текущий статус: {current_status}\n"
        text += f"📍 Последняя локация: {last_record['location']}"

        # Кнопка возврата в главное меню
        keyboard = [[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка получения журнала: {e}")
        await message.answer("❌ Ошибка при получении журнала. Попробуйте позже.")

# Убираем пагинацию журнала - не нужна для максимум 10 записей

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

        # Получаем последние 10 записей пользователя
        records = db.get_user_records(user_id, limit=10)

        if not records:
            await callback.message.edit_text(
                "📋 **Мой журнал**\n\n"
                "📝 У вас пока нет записей в журнале.\n"
                "Сделайте первую отметку о прибытии или убытии!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]])
            )
            await callback.answer()
            return

        # Формируем красивый текст журнала
        text = "📋 **Мой журнал**\n"
        text += "─" * 25 + "\n\n"

        for i, record in enumerate(records, 1):
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            formatted_date = timestamp.strftime('%d.%m.%Y')
            formatted_time = timestamp.strftime('%H:%M')

            if record['action'] == 'не в части':
                action_emoji = "🚶"
                action_text = "**убыл**"
                status_color = "🔴"
            else:
                action_emoji = "🏠"
                action_text = "**прибыл**"
                status_color = "🟢"

            text += f"{status_color} {i}. {action_emoji} {action_text}\n"
            text += f"📍 {record['location']}\n"
            text += f"📅 {formatted_date} в {formatted_time}\n"

            if i < len(records):
                text += "─" * 20 + "\n\n"

        # Показываем текущий статус
        last_record = records[0]
        if last_record['action'] == 'не в части':
            current_status = "🔴 **Убыл (не в части)**"
        else:
            current_status = "🟢 **Прибыл (в части)**"

        text += f"\n━━━━━━━━━━━━━━━\n"
        text += f"📊 Текущий статус: {current_status}\n"
        text += f"📍 Последняя локация: {last_record['location']}"

        # Кнопка возврата в главное меню
        keyboard = [[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в callback_show_journal: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке журнала.\nПопробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]])
        )
        await callback.answer()

async def show_user_journal_page(callback: CallbackQuery, user_id: int, page: int):
    """Показать страницу журнала пользователя"""
    try:
        per_page = 5
        offset = (page - 1) * per_page

        # Получаем общее количество записей
        all_records = db.get_user_records(user_id, 1000)  # Получаем все для подсчета
        total_records = len(all_records)
        total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1

        # Получаем записи для текущей страницы
        records = db.get_user_records(user_id, per_page)
        if offset > 0:
            # Для простоты берем нужные записи из общего списка
            records = all_records[offset:offset + per_page]

        if not records:
            text = "📋 Ваш журнал пуст.\n\nУ вас пока нет записей.\nОтметьтесь, используя кнопки меню."
            keyboard = get_journal_keyboard()
        else:
            text = f"📋 Ваш журнал (стр. {page}/{total_pages}):\n\n"
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

                    location = record['location'][:25] + "..." if len(record['location']) > 25 else record['location']
                    text += f"{i + offset}. {action_emoji} {action_text}\n"
                    text += f"📍 {location}\n"
                    text += f"⏰ {formatted_time}\n\n"
                except Exception as e:
                    logging.error(f"Ошибка обработки записи: {e}")
                    continue

            # Создаем клавиатуру с пагинацией
            keyboard = get_journal_keyboard_with_pagination(page, total_pages)

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка в show_user_journal_page: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке журнала.\nПопробуйте позже.",
            reply_markup=get_journal_keyboard()
        )

# Словарь для отслеживания последних действий пользователей
user_last_action = {}

def can_user_make_action(user_id: int) -> bool:
    """Проверяет, может ли пользователь сделать новое действие (защита от спама)"""
    now = datetime.now()
    if user_id in user_last_action:
        last_action_time = user_last_action[user_id]
        if (now - last_action_time).total_seconds() < 3:  # Минимум 3 секунды между действиями
            return False
    return True

def update_user_last_action(user_id: int):
    """Обновляет время последнего действия пользователя"""
    user_last_action[user_id] = datetime.now()

# Обработчики пагинации журнала
# @router.callback_query(F.data.startswith("journal_page_"))
# async def callback_journal_pagination(callback: CallbackQuery):
#     """Обработка пагинации журнала"""
#     try:
#         page = int(callback.data.split("_")[-1])
#         user_id = callback.from_user.id

#         await show_user_journal_page(callback, user_id, page)
#         await callback.answer()
#     except Exception as e:
#         logging.error(f"Ошибка в journal_pagination: {e}")
#         await callback.answer("❌ Ошибка при переходе по страницам")

@router.callback_query(F.data.startswith("locations_page_"))
async def callback_locations_pagination(callback: CallbackQuery):
    """Обработка пагинации локаций"""
    try:
        parts = callback.data.split("_")
        action = parts[2]
        page = int(parts[3])

        await callback.message.edit_text(
            "Выберите локацию, куда вы убыли:",
            reply_markup=get_location_keyboard_with_pagination(action, page)
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в locations_pagination: {e}")
        await callback.answer("❌ Ошибка при переходе по страницам")

@router.callback_query(F.data.in_(["journal_info", "locations_info"]))
async def callback_pagination_info(callback: CallbackQuery):
    """Обработка информационных кнопок пагинации"""
    await callback.answer()

# Обработчик неизвестных сообщений
@router.message()
async def handle_unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    try:
        user_id = message.from_user.id

        # Проверяем частоту сообщений (защита от спама)
        if not can_user_make_action(user_id):
            return

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

async def send_admin_notification(bot, user_id: int, action: str, location: str):
    """Отправляет уведомление главному админу о действиях пользователя."""
    try:
        user = db.get_user(user_id)
        if not user:
            logging.warning(f"Не удалось найти пользователя с ID {user_id} для уведомления админа.")
            return

        full_name = user['full_name']
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')

        if action == "в части":
            message = f"✅ [{timestamp}] Боец {full_name} прибыл в часть."
        elif action == "не в части":
            message = f"❌ [{timestamp}] Боец {full_name} убыл из части. Локация: {location}"
        else:
            message = f"ℹ️ [{timestamp}] Боец {full_name} совершил действие: {action}. Локация: {location}"

        await bot.send_message(MAIN_ADMIN_ID, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления админу: {e}")

@router.callback_query(F.data == "action_arrived")
async def callback_arrived(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Прибыл' - сразу записываем в часть без выбора локации"""
    user_id = callback.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = db.get_user(user_id)
    if not user:
        await callback.answer("❌ Сначала отправьте /start для регистрации", show_alert=True)
        return

    # Проверяем последнее действие
    last_records = db.get_user_records(user_id, 1)
    if last_records and last_records[0]['action'] == "прибыл":
        await state.set_state(UserStates.showing_duplicate_action_warning)
        last_time = datetime.fromisoformat(last_records[0]['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y в %H:%M')

        keyboard = [
            [InlineKeyboardButton(text="🔙 Понятно, вернуться в меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await callback.message.edit_text(
            "⚠️ **Повторная отметка о прибытии**\n\n"
            "Вы уже отмечены как **присутствующий в части**\n"
            f"⏰ Время отметки: {last_time}\n\n"
            "💡 **Что делать дальше:**\n"
            "1️⃣ Если нужно убыть — нажмите «❌ Убыл»\n"
            "2️⃣ Если ошиблись — просто вернитесь в меню",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    # Сразу записываем прибытие в часть
    if db.add_record(user_id, "прибыл", "В части"):
        # Очищаем состояние
        await state.clear()

        current_time = datetime.now().strftime('%H:%M')

        keyboard = [
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="show_journal")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await callback.message.edit_text(
            f"✅ **Прибытие зафиксировано!**\n\n"
            f"👤 **Боец:** {user['full_name']}\n"
            f"🏠 **Статус:** В части\n"
            f"⏰ **Время:** {current_time}\n\n"
            f"📝 Запись успешно добавлена в журнал.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при сохранении записи", show_alert=True)

    await callback.answer()