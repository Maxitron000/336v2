from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID
import logging
from datetime import datetime, timedelta

router = Router()

# Состояния для админ-панели
class AdminStates(StatesGroup):
    waiting_for_admin_id = State()

# Инициализация базы данных
db = DatabaseService()

def get_admin_panel_keyboard(is_main_admin: bool = False):
    """Создать клавиатуру админ-панели"""
    keyboard = [
        [InlineKeyboardButton(text="📊 Быстрая сводка", callback_data="admin_summary")],
        [InlineKeyboardButton(text="📋 Журнал событий", callback_data="admin_journal")],
        [InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export")]
    ]

    if is_main_admin:
        keyboard.append([InlineKeyboardButton(text="👥 Управление админами", callback_data="admin_manage")])

    keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard(callback_data: str = "admin_panel"):
    """Создать кнопку назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])

async def is_admin(user_id: int) -> bool:
    """Проверить права администратора"""
    return db.is_admin(user_id) or user_id == MAIN_ADMIN_ID

@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery):
    """Показать админ-панель"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    is_main_admin = user_id == MAIN_ADMIN_ID
    await callback.message.edit_text(
        "⚙️ Панель администратора\n\nВыберите действие:",
        reply_markup=get_admin_panel_keyboard(is_main_admin)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_summary")
async def callback_admin_summary(callback: CallbackQuery):
    """Показать быструю сводку"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        # Получаем статистику
        stats = db.get_current_status()

        text = "📊 Быстрая сводка\n\n"
        text += f"👥 Всего бойцов: {stats['total']}\n"
        text += f"✅ В части: {stats['present']}\n"
        text += f"❌ Вне части: {stats['absent']}\n\n"

        if stats['absent_list']:
            text += "🔴 Отсутствующие:\n"
            for person in stats['absent_list']:
                text += f"• {person['name']} - {person['location']}\n"
        else:
            text += "✅ Все бойцы в части!"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_panel")
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_summary: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

@router.callback_query(F.data == "admin_journal")
async def callback_admin_journal(callback: CallbackQuery):
    """Показать журнал событий"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        records = db.get_all_records(days=7, limit=10)

        if not records:
            text = "📋 Записей за последнюю неделю не найдено."
        else:
            text = "📋 Журнал событий (последние 10 записей за неделю):\n\n"
            for record in records:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m %H:%M')
                action_emoji = "🔴" if record['action'] == "убыл" else "🟢"
                text += f"👤 {record['full_name']}\n"
                text += f"{action_emoji} {record['action']} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_panel")
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_journal: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

@router.callback_query(F.data == "admin_export")
async def callback_admin_export(callback: CallbackQuery):
    """Экспорт данных"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        filename = db.export_to_excel(days=30)
        if filename:
            # Отправляем файл
            from aiogram.types import FSInputFile
            document = FSInputFile(filename, filename="military_records.xlsx")
            await callback.message.answer_document(
                document,
                caption="📤 Экспорт данных за последние 30 дней"
            )
            await callback.answer("✅ Файл отправлен")
        else:
            await callback.answer("❌ Нет данных для экспорта", show_alert=True)
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)

@router.callback_query(F.data == "admin_manage")
async def callback_admin_manage(callback: CallbackQuery):
    """Управление админами (только для главного админа)"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ]

    await callback.message.edit_text(
        "👥 Управление администраторами\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def callback_admin_add(callback: CallbackQuery, state: FSMContext):
    """Добавить админа"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_admin_id)
    await callback.message.edit_text(
        "➕ Добавление администратора\n\n"
        "Для добавления нового админа:\n"
        "1. Попросите пользователя отправить боту /start\n"
        "2. Введите его Telegram ID\n\n"
        "Введите ID пользователя:",
        reply_markup=get_back_keyboard("admin_manage")
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_admin_id)
async def handle_admin_id_input(message: Message, state: FSMContext):
    """Обработка ввода ID админа"""
    admin_id_text = message.text.strip()

    try:
        admin_id = int(admin_id_text)
    except ValueError:
        await message.answer(
            "❌ Неверный формат ID!\n"
            "ID должен быть числом.\n"
            "Попробуйте еще раз:"
        )
        return

    # Проверяем, существует ли пользователь
    target_user = db.get_user(admin_id)
    if not target_user:
        await message.answer(
            "❌ Пользователь с таким ID не найден!\n"
            "Убедитесь, что пользователь уже зарегистрирован в боте.\n"
            "Попробуйте еще раз:"
        )
        return

    # Проверяем, не является ли уже админом
    if db.is_admin(admin_id):
        await message.answer(f"❌ Пользователь {target_user['full_name']} уже является администратором!")
        await state.clear()
        return

    # Добавляем админа
    if db.add_admin(admin_id):
        await state.clear()
        await message.answer(f"✅ Администратор {target_user['full_name']} успешно добавлен!")
    else:
        await message.answer("❌ Ошибка при добавлении администратора. Попробуйте еще раз.")

@router.callback_query(F.data == "admin_list")
async def callback_admin_list(callback: CallbackQuery):
    """Показать список админов"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    try:
        admins = db.get_all_admins()

        if not admins:
            text = "👥 Администраторы не найдены."
        else:
            text = "👥 Список администраторов:\n\n"
            for admin in admins:
                status = "👑 Главный" if admin['id'] == MAIN_ADMIN_ID else "⚙️ Админ"
                text += f"{status} {admin['full_name']}\n"
                text += f"ID: {admin['id']}\n"
                text += f"Username: @{admin['username']}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_manage")
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_list: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

# Команда для прямого доступа к админ-панели
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin"""
    user_id = message.from_user.id

    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return

    is_main_admin = user_id == MAIN_ADMIN_ID
    await message.answer(
        "⚙️ Панель администратора\n\nВыберите действие:",
        reply_markup=get_admin_panel_keyboard(is_main_admin)
    )