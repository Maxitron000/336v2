
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DBService
from config import LOCATIONS, MAIN_ADMIN_ID
from keyboards import get_main_menu_keyboard, get_location_keyboard, get_back_keyboard
import logging
from datetime import datetime
import pytz

router = Router()

class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_comment = State()

def get_kaliningrad_time():
    """Получить текущее время в Калининграде"""
    tz = pytz.timezone('Europe/Kaliningrad')
    now = datetime.now(tz)
    return now.strftime('%H:%M:%S')

def get_kaliningrad_date():
    """Получить текущую дату в Калининграде"""
    tz = pytz.timezone('Europe/Kaliningrad')
    now = datetime.now(tz)
    return now.strftime('%d.%m.%Y')

def get_welcome_preview():
    """Создать красивую превью для приветствия"""
    time = get_kaliningrad_time()
    date = get_kaliningrad_date()
    
    preview = f"""
🏛️ **СИСТЕМА ВОЕННОГО ТАБЕЛЯ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 **Калининград**
📅 Дата: {date}
🕐 Время: {time}

⚓ **Рота В**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔐 **Система готова к работе**
👤 Для начала работы введите /start
    """
    return preview

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    try:
        user = await DBService.get_user(message.from_user.id)
        if user:
            is_admin = user['is_admin'] or message.from_user.id == MAIN_ADMIN_ID
            time = get_kaliningrad_time()
            date = get_kaliningrad_date()
            
            welcome_text = f"""
🏛️ **СИСТЕМА ВОЕННОГО ТАБЕЛЯ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 **Калининград**
📅 {date} | 🕐 {time}

⚓ **Рота В**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👋 **Добро пожаловать, {user['full_name']}!**
🔐 Статус: {'🛡️ Администратор' if is_admin else '👤 Пользователь'}

📋 Выберите действие:
            """
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(is_admin),
                parse_mode="Markdown"
            )
        else:
            preview = get_welcome_preview()
            await message.answer(
                preview,
                parse_mode="Markdown"
            )
            await message.answer(
                "📝 **Регистрация в системе**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Введите ваше **ФИО** для регистрации:\n"
                "*(Например: Иванов Иван Иванович)*",
                parse_mode="Markdown"
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
        
        # Защита от дурака - валидация ФИО
        if len(full_name) < 5:
            await message.answer(
                "❌ **Ошибка валидации**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "ФИО должно содержать минимум 5 символов.\n"
                "**Пример:** Иванов И.И.\n\n"
                "Попробуйте еще раз:",
                parse_mode="Markdown"
            )
            return
        
        # Проверка на бессмысленные строки
        if full_name.lower() in ['аaa', '123', 'ааа', 'test', 'тест', '...', 'abc']:
            await message.answer(
                "❌ **Некорректное ФИО**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Введите реальное ФИО.\n"
                "**Пример:** Петров П.П.\n\n"
                "Попробуйте еще раз:",
                parse_mode="Markdown"
            )
            return
        
        # Проверка на минимум две части (фамилия и инициалы)
        parts = full_name.split()
        if len(parts) < 2:
            await message.answer(
                "❌ **Неполное ФИО**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "ФИО должно содержать фамилию и инициалы.\n"
                "**Пример:** Сидоров С.С.\n\n"
                "Попробуйте еще раз:",
                parse_mode="Markdown"
            )
            return
        
        success = await DBService.add_user(
            message.from_user.id,
            message.from_user.username or "",
            full_name
        )
        
        if success:
            time = get_kaliningrad_time()
            date = get_kaliningrad_date()
            
            success_text = f"""
✅ **РЕГИСТРАЦИЯ ЗАВЕРШЕНА**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **{full_name}**
🆔 ID: {message.from_user.id}
📅 {date} | 🕐 {time}

⚓ **Рота В**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Система готова к работе!**
📋 Выберите действие:
            """
            
            await message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(False),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer(
                "❌ **Ошибка регистрации**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Ошибка в process_name: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать профиль пользователя"""
    try:
        # Удаляем команду
        try:
            await message.delete()
        except:
            pass
            
        user = await DBService.get_user(message.from_user.id)
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start")
            return
        
        records = await DBService.get_user_records(message.from_user.id, 5)
        time = get_kaliningrad_time()
        date = get_kaliningrad_date()
        
        # Определяем текущий статус
        current_status = "❓ Статус неизвестен"
        if records:
            last_record = records[0]
            if last_record['action'] == 'прибыл':
                current_status = f"🏠 **В ЧАСТИ** ({last_record['location']})"
            else:
                current_status = f"🚶 **НЕ В ЧАСТИ** ({last_record['location']})"
        
        profile_text = f"""
👤 **ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 **Калининград**
📅 {date} | 🕐 {time}

⚓ **Рота В**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **{user['full_name']}**
🆔 ID: {user['id']}
🛡️ Права: {'🛡️ Администратор' if user['is_admin'] else '👤 Пользователь'}

📍 **ТЕКУЩИЙ СТАТУС:**
{current_status}

📋 **ПОСЛЕДНИЕ ЗАПИСИ:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        if records:
            for record in records:
                action_emoji = "🏠" if record['action'] == 'прибыл' else "🚶"
                time_formatted = format_kaliningrad_time(record['timestamp'])
                profile_text += f"\n{action_emoji} **{record['action'].upper()}** - {record['location']}"
                profile_text += f"\n   ⏰ {time_formatted}\n"
        else:
            profile_text += "\n📝 Записей пока нет"
        
        await message.answer(
            profile_text, 
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user.get('is_admin', False))
        )
    except Exception as e:
        logging.error(f"Ошибка в cmd_profile: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

def format_kaliningrad_time(dt_str):
    """Форматирование времени в калининградский часовой пояс"""
    try:
        import pytz
        from datetime import datetime
        KALININGRAD_TZ = pytz.timezone('Europe/Kaliningrad')
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        kld_time = dt.astimezone(KALININGRAD_TZ)
        return kld_time.strftime('%d.%m.%Y %H:%M')
    except:
        return dt_str

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать справку"""
    time = get_kaliningrad_time()
    date = get_kaliningrad_date()
    
    help_text = f"""
🆘 **СПРАВКА ПО СИСТЕМЕ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 **Калининград**
📅 {date} | 🕐 {time}

⚓ **Рота В**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **КОМАНДЫ:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 `/start` - Регистрация в системе
🔹 `/profile` - Ваш профиль и записи
🔹 `/admin` - Админ-панель
🔹 `/stats` - Статистика
🔹 `/export` - Экспорт данных
🔹 `/help` - Эта справка

📝 **Для создания записи используйте кнопки в меню**

⚙️ **Техническая поддержка:**
Обратитесь к администратору системы
    """
    await message.answer(help_text, parse_mode="Markdown")

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
