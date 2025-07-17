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
    waiting_for_search_query = State()
    waiting_for_filter_period = State()
    waiting_for_bulk_action = State()

# Инициализация базы данных
db = DatabaseService()

def get_admin_panel_keyboard(is_main_admin: bool = False):
    """Создать клавиатуру админ-панели"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Сводка", callback_data="admin_summary"),
            InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search")
        ],
        [
            InlineKeyboardButton(text="📋 Журнал", callback_data="admin_journal"),
            InlineKeyboardButton(text="📈 Аналитика", callback_data="admin_analytics")
        ],
        [
            InlineKeyboardButton(text="👥 Персонал", callback_data="admin_personnel"),
            InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_export_menu")
        ],
        [
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
        ]
    ]

    if is_main_admin:
        keyboard.append([InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage")])

    keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_filter_keyboard():
    """Клавиатура фильтров журнала"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 1 день", callback_data="filter_journal_1"),
            InlineKeyboardButton(text="📅 7 дней", callback_data="filter_journal_7"),
            InlineKeyboardButton(text="📅 30 дней", callback_data="filter_journal_30")
        ],
        [
            InlineKeyboardButton(text="🟢 Только прибытия", callback_data="filter_action_arrived"),
            InlineKeyboardButton(text="🔴 Только убытия", callback_data="filter_action_departed")
        ],
        [
            InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="filter_reset"),
            InlineKeyboardButton(text="📊 Показать все", callback_data="admin_journal_show")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

def get_personnel_keyboard():
    """Клавиатура управления персоналом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Список всех", callback_data="personnel_all"),
            InlineKeyboardButton(text="✅ В части", callback_data="personnel_present")
        ],
        [
            InlineKeyboardButton(text="❌ Отсутствуют", callback_data="personnel_absent"),
            InlineKeyboardButton(text="🔍 Поиск бойца", callback_data="personnel_search")
        ],
        [
            InlineKeyboardButton(text="📊 Детали по бойцу", callback_data="personnel_details"),
            InlineKeyboardButton(text="🔧 Массовые действия", callback_data="personnel_bulk")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

def get_analytics_keyboard():
    """Клавиатура аналитики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Общая статистика", callback_data="analytics_general"),
            InlineKeyboardButton(text="📍 По локациям", callback_data="analytics_locations")
        ],
        [
            InlineKeyboardButton(text="👤 По бойцам", callback_data="analytics_soldiers"),
            InlineKeyboardButton(text="📅 По времени", callback_data="analytics_time")
        ],
        [
            InlineKeyboardButton(text="🏆 ТОП активности", callback_data="analytics_top"),
            InlineKeyboardButton(text="📊 Графики", callback_data="analytics_charts")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

def get_export_keyboard():
    """Клавиатура экспорта"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Excel (все данные)", callback_data="export_excel_all"),
            InlineKeyboardButton(text="📋 Excel (фильтр)", callback_data="export_excel_filter")
        ],
        [
            InlineKeyboardButton(text="📝 CSV экспорт", callback_data="export_csv"),
            InlineKeyboardButton(text="📄 Отчет PDF", callback_data="export_pdf")
        ],
        [
            InlineKeyboardButton(text="📧 Еженедельный отчет", callback_data="export_weekly"),
            InlineKeyboardButton(text="📅 Месячный отчет", callback_data="export_monthly")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

def get_back_keyboard(callback_data: str = "admin_panel"):
    """Создать кнопку назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])

async def is_admin(user_id: int) -> bool:
    """Проверить права администратора"""
    if user_id == MAIN_ADMIN_ID:
        return True
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
        "⚙️ **Панель администратора**\n\n"
        "🎯 Расширенные возможности управления:\n"
        "• Детальная аналитика и фильтры\n"
        "• Поиск и массовые операции\n"
        "• Экспорт в различных форматах\n"
        "• Настройка уведомлений\n\n"
        "Выберите нужный раздел:",
        reply_markup=get_admin_panel_keyboard(is_main_admin),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_search")
async def callback_admin_search(callback: CallbackQuery, state: FSMContext):
    """Поиск записей"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_search_query)
    await callback.message.edit_text(
        "🔍 **Поиск по базе данных**\n\n"
        "Введите поисковый запрос:\n"
        "• Имя бойца\n"
        "• Локация\n"
        "• Часть имени или фамилии\n\n"
        "💡 Поиск не чувствителен к регистру",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_search_query)
async def handle_search_query(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    query = message.text.strip()
    await state.clear()

    try:
        # Поиск пользователей
        users = db.get_all_users()
        found_users = [u for u in users if query.lower() in u['full_name'].lower()]

        # Поиск записей
        records = db.get_all_records(days=30)
        found_records = [r for r in records if 
                        query.lower() in r['full_name'].lower() or 
                        query.lower() in r['location'].lower()]

        text = f"🔍 **Результаты поиска: '{query}'**\n\n"

        if found_users:
            text += f"👥 **Найдено бойцов: {len(found_users)}**\n"
            for user in found_users[:5]:
                text += f"• {user['full_name']}\n"
            if len(found_users) > 5:
                text += f"... и еще {len(found_users) - 5}\n"
            text += "\n"

        if found_records:
            text += f"📋 **Найдено записей: {len(found_records)}**\n"
            for record in found_records[:5]:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m %H:%M')
                action_emoji = "🔴" if record['action'] == "не в части" else "🟢"
                text += f"{action_emoji} {record['full_name']} - {record['location']} ({formatted_time})\n"
            if len(found_records) > 5:
                text += f"... и еще {len(found_records) - 5}\n"

        if not found_users and not found_records:
            text += "❌ Ничего не найдено\n\nПопробуйте изменить запрос"

        keyboard = [
            [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="admin_search")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")]
        ]

        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка поиска: {e}")
        await message.answer("❌ Ошибка при выполнении поиска")

@router.callback_query(F.data == "admin_journal")
async def callback_admin_journal(callback: CallbackQuery):
    """Журнал с фильтрами"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 **Журнал событий**\n\n"
        "Выберите фильтр для отображения записей:\n"
        "📅 По времени\n"
        "🎯 По типу действия\n"
        "🔄 Сбросить фильтры",
        reply_markup=get_journal_filter_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filter_"))
async def callback_filter_journal(callback: CallbackQuery):
    """Применить фильтр к журналу"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    filter_type = callback.data.split("_")[-1]

    try:
        if filter_type in ["1", "7", "30"]:
            days = int(filter_type)
            records = db.get_all_records(days=days, limit=20)
            period_text = f"{days} дн."
        elif filter_type == "arrived":
            records = db.get_all_records(days=7)
            records = [r for r in records if r['action'] == 'в части']
            period_text = "прибытия (7 дн.)"
        elif filter_type == "departed":
            records = db.get_all_records(days=7)
            records = [r for r in records if r['action'] == 'не в части']
            period_text = "убытия (7 дн.)"
        else:
            records = db.get_all_records(days=7, limit=20)
            period_text = "все (7 дн.)"

        if not records:
            text = f"📋 **Журнал ({period_text})**\n\n📝 Записей не найдено."
        else:
            text = f"📋 **Журнал ({period_text})**\n"
            text += f"📊 Найдено записей: {len(records)}\n"
            text += "─" * 30 + "\n\n"

            for i, record in enumerate(records[:15], 1):
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime('%d.%m')
                formatted_time = timestamp.strftime('%H:%M')

                if record['action'] == 'не в части':
                    action_emoji = "🔴"
                    status_color = "🚶"
                else:
                    action_emoji = "🟢"
                    status_color = "🏠"

                text += f"{action_emoji} **{record['full_name']}**\n"
                text += f"{status_color} {record['action']} - {record['location']}\n"
                text += f"📅 {formatted_date} в {formatted_time}\n\n"

            if len(records) > 15:
                text += f"... и еще {len(records) - 15} записей"

        keyboard = [
            [InlineKeyboardButton(text="🔄 Другой фильтр", callback_data="admin_journal")],
            [InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_export_menu")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")]
        ]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка фильтрации: {e}")
        await callback.answer("❌ Ошибка применения фильтра", show_alert=True)

@router.callback_query(F.data == "admin_personnel")
async def callback_admin_personnel(callback: CallbackQuery):
    """Управление персоналом"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 **Управление персоналом**\n\n"
        "Выберите действие:\n"
        "• Просмотр списков\n"
        "• Поиск конкретного бойца\n"
        "• Детальная информация\n"
        "• Массовые операции",
        reply_markup=get_personnel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("personnel_"))
async def callback_personnel_action(callback: CallbackQuery):
    """Действия с персоналом"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    action = callback.data.split("_")[-1]

    try:
        if action == "all":
            users = db.get_all_users()
            text = f"👥 **Все бойцы ({len(users)})**\n\n"
            for i, user in enumerate(users[:20], 1):
                text += f"{i}. {user['full_name']}\n"
            if len(users) > 20:
                text += f"... и еще {len(users) - 20}"

        elif action == "present":
            status = db.get_current_status()
            present_users = status.get('present_users', [])
            text = f"✅ **В части ({len(present_users)})**\n\n"
            for i, user in enumerate(present_users[:20], 1):
                text += f"{i}. {user['name']}\n"
            if len(present_users) > 20:
                text += f"... и еще {len(present_users) - 20}"

        elif action == "absent":
            status = db.get_current_status()
            absent_users = status.get('absent_users', [])
            text = f"❌ **Отсутствуют ({len(absent_users)})**\n\n"
            for i, user in enumerate(absent_users[:20], 1):
                text += f"{i}. {user['name']} - {user['location']}\n"
            if len(absent_users) > 20:
                text += f"... и еще {len(absent_users) - 20}"

        else:
            text = "⚙️ Функция в разработке"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_personnel"),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в personnel_action: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

@router.callback_query(F.data == "admin_analytics")
async def callback_admin_analytics(callback: CallbackQuery):
    """Аналитика"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "📈 **Аналитика и статистика**\n\n"
        "Выберите тип анализа:\n"
        "• Общая статистика системы\n"
        "• Анализ по локациям\n"
        "• Активность бойцов\n"
        "• Временные тренды",
        reply_markup=get_analytics_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("analytics_"))
async def callback_analytics_action(callback: CallbackQuery):
    """Действия аналитики"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    action = callback.data.split("_")[-1]

    try:
        if action == "general":
            # Общая статистика
            records = db.get_all_records(days=30)
            users = db.get_all_users()
            status = db.get_current_status()

            total_actions = len(records)
            departures = len([r for r in records if r['action'] == 'не в части'])
            arrivals = len([r for r in records if r['action'] == 'в части'])

            text = "📊 **Общая статистика за 30 дней**\n\n"
            text += f"👥 Всего бойцов: {len(users)}\n"
            text += f"✅ В части: {status.get('present', 0)}\n"
            text += f"❌ Отсутствуют: {status.get('absent', 0)}\n\n"
            text += f"📈 **Активность:**\n"
            text += f"• Всего записей: {total_actions}\n"
            text += f"• Убытий: {departures}\n"
            text += f"• Прибытий: {arrivals}\n"
            text += f"• Среднее в день: {total_actions // 30 if total_actions > 0 else 0}\n\n"
            text += f"📊 **Коэффициенты:**\n"
            text += f"• Активность: {(total_actions / len(users) * 100):.1f}%\n" if users else "• Активность: 0%\n"
            text += f"• Присутствие: {(status.get('present', 0) / len(users) * 100):.1f}%\n" if users else "• Присутствие: 0%\n"

        elif action == "locations":
            # Статистика по локациям
            records = db.get_all_records(days=30)
            locations = {}
            for record in records:
                if record['action'] == 'не в части':
                    loc = record['location']
                    locations[loc] = locations.get(loc, 0) + 1

            text = "📍 **Статистика по локациям (30 дней)**\n\n"
            if locations:
                sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)
                text += "🏆 **ТОП локации:**\n"
                for i, (location, count) in enumerate(sorted_locations[:10], 1):
                    percentage = (count / sum(locations.values()) * 100)
                    text += f"{i}. {location}: {count} ({percentage:.1f}%)\n"
            else:
                text += "📝 Данных по локациям не найдено"

        elif action == "soldiers":
            # Статистика по бойцам
            records = db.get_all_records(days=30)
            soldier_activity = {}
            for record in records:
                name = record['full_name']
                soldier_activity[name] = soldier_activity.get(name, 0) + 1

            text = "👤 **Активность бойцов (30 дней)**\n\n"
            if soldier_activity:
                sorted_soldiers = sorted(soldier_activity.items(), key=lambda x: x[1], reverse=True)
                text += "🏆 **Самые активные:**\n"
                for i, (name, count) in enumerate(sorted_soldiers[:10], 1):
                    text += f"{i}. {name}: {count} записей\n"

                text += f"\n📊 **Статистика:**\n"
                text += f"• Средняя активность: {sum(soldier_activity.values()) / len(soldier_activity):.1f}\n"
                text += f"• Максимальная: {max(soldier_activity.values())}\n"
                text += f"• Минимальная: {min(soldier_activity.values())}\n"
            else:
                text += "📝 Данных по активности не найдено"

        else:
            text = "⚙️ Функция в разработке"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_analytics"),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка аналитики: {e}")
        await callback.answer("❌ Ошибка получения аналитики", show_alert=True)

@router.callback_query(F.data == "admin_export_menu")
async def callback_admin_export_menu(callback: CallbackQuery):
    """Меню экспорта"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "📤 **Экспорт данных**\n\n"
        "Выберите формат и тип экспорта:\n"
        "• Excel с фильтрами\n"
        "• CSV для анализа\n"
        "• PDF отчеты\n"
        "• Готовые отчеты",
        reply_markup=get_export_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("export_"))
async def callback_export_action(callback: CallbackQuery):
    """Экспорт данных"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    export_type = callback.data.split("_")[-1]

    try:
        if export_type == "all":
            filename = db.export_to_excel(days=365)  # Все данные за год
            period_text = "все данные"
        elif export_type == "filter":
            filename = db.export_to_excel(days=30)  # Последние 30 дней
            period_text = "последние 30 дней"
        else:
            await callback.answer("⚙️ Функция в разработке", show_alert=True)
            return

        if filename:
            from aiogram.types import FSInputFile
            document = FSInputFile(filename, filename=f"military_records_{export_type}.xlsx")
            await callback.message.answer_document(
                document,
                caption=f"📤 Экспорт: {period_text}"
            )
            await callback.answer("✅ Файл отправлен")
        else:
            await callback.answer("❌ Нет данных для экспорта", show_alert=True)

    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)

# Остальные функции (summary, manage, и т.д.) остаются без изменений
@router.callback_query(F.data == "admin_summary")
async def callback_admin_summary(callback: CallbackQuery):
    """Показать быструю сводку"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        stats = db.get_current_status()

        text = "📊 **Быстрая сводка**\n\n"
        text += f"👥 Всего бойцов: {stats['total']}\n"
        text += f"✅ В части: {stats['present']}\n"
        text += f"❌ Вне части: {stats['absent']}\n\n"

        if stats.get('location_groups'):
            text += "📍 **Группировка по локациям:**\n\n"

            if 'В части' in stats['location_groups']:
                group = stats['location_groups']['В части']
                text += f"🟢 **В части: {group['count']}**\n"
                for name in group['names'][:10]:
                    text += f"• {name}\n"
                if len(group['names']) > 10:
                    text += f"... и еще {len(group['names']) - 10}\n"
                text += "\n"

            for location, group in stats['location_groups'].items():
                if location != 'В части':
                    text += f"🔴 **{location}: {group['count']}**\n"
                    for name in group['names'][:5]:
                        text += f"• {name}\n"
                    if len(group['names']) > 5:
                        text += f"... и еще {len(group['names']) - 5}\n"
                    text += "\n"

        if stats['total'] == 0:
            text += "ℹ️ Нет зарегистрированных бойцов"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_panel"),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_summary: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

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
        "👑 **Управление администраторами**\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
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
        "➕ **Добавление администратора**\n\n"
        "Для добавления нового админа:\n"
        "1. Попросите пользователя отправить боту /start\n"
        "2. Введите его Telegram ID\n\n"
        "Введите ID пользователя:",
        reply_markup=get_back_keyboard("admin_manage"),
        parse_mode="Markdown"
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

    target_user = db.get_user(admin_id)
    if not target_user:
        await message.answer(
            "❌ Пользователь с таким ID не найден!\n"
            "Убедитесь, что пользователь уже зарегистрирован в боте.\n"
            "Попробуйте еще раз:"
        )
        return

    if db.is_admin(admin_id):
        await message.answer(f"❌ Пользователь {target_user['full_name']} уже является администратором!")
        await state.clear()
        return

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
            text = "👑 **Список администраторов:**\n\n"
            for admin in admins:
                status = "👑 Главный" if admin['id'] == MAIN_ADMIN_ID else "⚙️ Админ"
                text += f"{status} **{admin['full_name']}**\n"
                text += f"ID: `{admin['id']}`\n"
                text += f"Username: @{admin['username']}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_manage"),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_list: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin"""
    user_id = message.from_user.id

    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return

    is_main_admin = user_id == MAIN_ADMIN_ID
    await message.answer(
        "⚙️ **Панель администратора**\n\n"
        "🎯 Расширенные возможности управления доступны",
        reply_markup=get_admin_panel_keyboard(is_main_admin),
        parse_mode="Markdown"
    )

def get_notifications_keyboard():
    """Клавиатура настроек уведомлений"""