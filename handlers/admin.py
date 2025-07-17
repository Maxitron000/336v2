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
        [InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")],
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
    # Главный админ всегда имеет права
    if user_id == MAIN_ADMIN_ID:
        return True
    # Проверяем в базе данных
    return db.is_admin(user_id)

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

        # Отображаем группировку по локациям
        if stats.get('location_groups'):
            text += "📍 **Группировка по локациям:**\n\n"
            
            # Сначала показываем тех, кто в части
            if 'В части' in stats['location_groups']:
                group = stats['location_groups']['В части']
                text += f"🟢 **В части: {group['count']}**\n"
                for name in group['names'][:10]:  # Показываем максимум 10
                    text += f"• {name}\n"
                if len(group['names']) > 10:
                    text += f"... и еще {len(group['names']) - 10}\n"
                text += "\n"
            
            # Затем показываем отсутствующих по локациям
            for location, group in stats['location_groups'].items():
                if location != 'В части':
                    text += f"🔴 **{location}: {group['count']}**\n"
                    for name in group['names'][:5]:  # Показываем максимум 5 для внешних локаций
                        text += f"• {name}\n"
                    if len(group['names']) > 5:
                        text += f"... и еще {len(group['names']) - 5}\n"
                    text += "\n"
        
        if stats['total'] == 0:
            text += "ℹ️ Нет зарегистрированных бойцов"

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
    """Показать журнал событий с пагинацией"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    #await show_admin_journal_page(callback, 1)
    #await callback.answer()
    await show_admin_journal(callback)
    await callback.answer()

async def show_admin_journal(callback: CallbackQuery):
    """Показать записи журнала для админа"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    try:
        # Получаем последние 10 записей за неделю
        records = db.get_all_records(days=7, limit=10)

        if not records:
            text = "📋 **Журнал записей**\n\n📝 Записей за последние 7 дней не найдено."
        else:
            text = "📋 **Журнал записей**\n"
            text += "─" * 30 + "\n\n"

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

                text += f"{status_color} {i}. 👤 **{record['full_name']}**\n"
                text += f"{action_emoji} {action_text} - {record['location']}\n"
                text += f"📅 {formatted_date} в {formatted_time}\n"

                if i < len(records):
                    text += "─" * 25 + "\n\n"

        keyboard = [
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_journal_stats")],
            [InlineKeyboardButton(text="📤 Экспорт Excel", callback_data="admin_journal_export")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]

        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_journal_stats")],
            [InlineKeyboardButton(text="📤 Экспорт Excel", callback_data="admin_journal_export")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ])
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка получения журнала: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении журнала.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_journal")]])
        )
        await callback.answer()

#async def show_admin_journal_page(callback: CallbackQuery, page: int, days: int = 7):
#    """Показать страницу админского журнала"""
#    try:
#        per_page = 8
#
#        # Получаем записи с пагинацией
#        result = db.get_records_paginated(page=page, per_page=per_page, days=days)
#
#        if not result['records']:
#            text = f"📋 Записей за последние {days} дней не найдено."
#            keyboard = get_back_keyboard("admin_panel")
#        else:
#            text = f"📋 Журнал событий за {days} дней (стр. {page}/{result['total_pages']}):\n\n"
#
#            for i, record in enumerate(result['records'], 1):
#                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
#                formatted_time = timestamp.strftime('%d.%m %H:%M')
#
#                if record['action'] == "не в части":
#                    action_emoji = "🔴"
#                    action_text = "не в части"
#                elif record['action'] == "в части":
#                    action_emoji = "🟢"
#                    action_text = "в части"
#                else:
#                    action_emoji = "🔴" if "убыл" in record['action'] else "🟢"
#                    action_text = record['action']
#
#                location = record['location'][:20] + "..." if len(record['location']) > 20 else record['location']
#                text += f"{i}. 👤 {record['full_name']}\n"
#                text += f"   {action_emoji} {action_text} - {location}\n"
#                text += f"   ⏰ {formatted_time}\n\n"
#
#            text += f"📊 Всего записей: {result['total_records']}"
#
#            # Создаем клавиатуру с пагинацией
#            keyboard = get_admin_journal_keyboard(page, result['total_pages'], days)
#
#        await callback.message.edit_text(text, reply_markup=keyboard)
#
#    except Exception as e:
#        logging.error(f"Ошибка в show_admin_journal_page: {e}")
#        await callback.answer("❌ Ошибка получения данных", show_alert=True)

#def get_admin_journal_keyboard(current_page: int, total_pages: int, days: int = 7):
#    """Создать клавиатуру админского журнала с пагинацией"""
#    keyboard = []
#
#    # Кнопки фильтров по периоду
#    period_row = []
#    period_row.append(InlineKeyboardButton(text="1д" if days == 1 else "📅1д", callback_data="admin_journal_1"))
#    period_row.append(InlineKeyboardButton(text="7д" if days == 7 else "📅7д", callback_data="admin_journal_7"))
#    period_row.append(InlineKeyboardButton(text="30д" if days == 30 else "📅30д", callback_data="admin_journal_30"))
#    keyboard.append(period_row)
#
#    # Пагинация
#    if total_pages > 1:
#        pagination_row = []
#
#        if current_page > 1:
#            pagination_row.append(InlineKeyboardButton(text="⬅️ Пред", callback_data=f"admin_journal_page_{current_page - 1}_{days}"))
#
#        pagination_row.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="admin_journal_info"))
#
#        if current_page < total_pages:
#            pagination_row.append(InlineKeyboardButton(text="След ➡️", callback_data=f"admin_journal_page_{current_page + 1}_{days}"))
#
#        keyboard.append(pagination_row)
#
#    # Дополнительные функции
#    keyboard.append([InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_export")])
#    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
#
#    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Обработчики пагинации админского журнала
#@router.callback_query(F.data.startswith("admin_journal_page_"))
#async def callback_admin_journal_pagination(callback: CallbackQuery):
#    """Обработка пагинации админского журнала"""
#    try:
#        parts = callback.data.split("_")
#        page = int(parts[3])
#        days = int(parts[4]) if len(parts) > 4 else 7
#
#        await show_admin_journal_page(callback, page, days)
#        await callback.answer()
#    except Exception as e:
#        logging.error(f"Ошибка в admin_journal_pagination: {e}")
#        await callback.answer("❌ Ошибка при переходе по страницам")

#@router.callback_query(F.data.in_(["admin_journal_1", "admin_journal_7", "admin_journal_30"]))
#async def callback_admin_journal_period(callback: CallbackQuery):
#    """Обработка смены периода в админском журнале"""
#    try:
#        days = int(callback.data.split("_")[-1])
#        await show_admin_journal_page(callback, 1, days)
#        await callback.answer()
#    except Exception as e:
#        logging.error(f"Ошибка в admin_journal_period: {e}")
#        await callback.answer("❌ Ошибка при смене периода")

@router.callback_query(F.data == "admin_journal_info")
async def callback_admin_journal_info(callback: CallbackQuery):
    """Информационная кнопка"""
    await callback.answer()

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