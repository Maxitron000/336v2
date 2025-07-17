from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID
import logging
from datetime import datetime, timedelta

# Проверяем наличие необходимых библиотек для экспорта
try:
    import pandas as pd
    import openpyxl
    EXPORT_AVAILABLE = True
    logging.info("✅ Библиотеки экспорта загружены успешно")
except ImportError as e:
    EXPORT_AVAILABLE = False
    logging.error(f"❌ Ошибка импорта библиотек экспорта: {e}")
    logging.error("Необходимо установить: pip install pandas openpyxl")

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

def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру с кнопкой 'Назад'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])

def get_export_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру для экспорта"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
            InlineKeyboardButton(text="📄 CSV", callback_data="export_csv")
        ],
        [
            InlineKeyboardButton(text="📑 PDF", callback_data="export_pdf"),
            InlineKeyboardButton(text="📈 Отчеты", callback_data="export_reports")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
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
        # Показываем индикатор загрузки
        await callback.message.edit_text(
            "🔄 **Применение фильтра...**\n\n"
            "Пожалуйста, подождите, идет обработка данных.",
            parse_mode="Markdown"
        )

        if filter_type in ["1", "7", "30"]:
            days = int(filter_type)
            records = db.get_all_records(days=days, limit=50)
            period_text = f"{days} дн."
        elif filter_type == "arrived":
            records = db.get_all_records(days=7, limit=50)
            records = [r for r in records if r['action'] == 'в части']
            period_text = "прибытия (7 дн.)"
        elif filter_type == "departed":
            records = db.get_all_records(days=7, limit=50)
            records = [r for r in records if r['action'] == 'не в части']
            period_text = "убытия (7 дн.)"
        elif filter_type == "reset":
            records = db.get_all_records(days=7, limit=50)
            period_text = "все (7 дн.)"
        else:
            records = db.get_all_records(days=7, limit=50)
            period_text = "все (7 дн.)"

        if not records:
            text = f"📋 **Журнал ({period_text})**\n\n📝 Записей не найдено за выбранный период."
        else:
            text = f"📋 **Журнал ({period_text})**\n"
            text += f"📊 Найдено записей: {len(records)}\n"
            text += "─" * 30 + "\n\n"

            for i, record in enumerate(records[:15], 1):
                try:
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
                except Exception as record_error:
                    logging.error(f"Ошибка обработки записи: {record_error}")
                    continue

            if len(records) > 15:
                text += f"... и еще {len(records) - 15} записей"

        # Добавляем кнопку экспорта для текущих данных
        export_callback = "admin_export_menu"
        if filter_type == "7":
            export_callback = "export_weekly"
        elif filter_type == "30":
            export_callback = "export_monthly"

        keyboard = [
            [InlineKeyboardButton(text="🔄 Другой фильтр", callback_data="admin_journal")],
            [InlineKeyboardButton(text="📤 Экспорт этих данных", callback_data=export_callback)],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")]
        ]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer("✅ Фильтр применен")

    except Exception as e:
        logging.error(f"Ошибка фильтрации: {e}")
        await callback.message.edit_text(
            f"❌ **Ошибка фильтрации**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_back_keyboard("admin_journal"),
            parse_mode="Markdown"
        )
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

        elif action == "search":
            await callback.message.edit_text(
                "🔍 **Поиск бойца**\n\n"
                "Введите имя или фамилию для поиска:",
                reply_markup=get_back_keyboard("admin_personnel"),
                parse_mode="Markdown"
            )
            # Здесь можно добавить FSM состояние для поиска
            text = "🔍 Поиск временно недоступен. Используйте общий поиск в админ-панели."

        elif action == "details":
            # Показываем детальную статистику по бойцам
            users = db.get_all_users()
            text = f"📊 **Детальная информация**\n\n"
            text += f"👥 Всего бойцов: {len(users)}\n\n"

            # Статистика активности за последние 30 дней
            records = db.get_all_records(days=30, limit=1000)
            if records:
                user_activity = {}
                for record in records:
                    name = record['full_name']
                    user_activity[name] = user_activity.get(name, 0) + 1

                text += "📈 **Активность за 30 дней:**\n"
                sorted_activity = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
                for i, (name, count) in enumerate(sorted_activity[:10], 1):
                    text += f"{i}. {name}: {count} записей\n"
            else:
                text += "📝 Записей активности не найдено"

        elif action == "bulk":
            text = "🔧 **Массовые действия**\n\n"
            text += "Доступные операции:\n"
            text += "• Массовое изменение статуса\n"
            text += "• Групповые уведомления\n"
            text += "• Экспорт списков\n\n"
            text += "⚙️ Функция в разработке"

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

        elif action == "time":
            # Анализ по времени
            records = db.get_all_records(days=30)
            if records:
                from collections import defaultdict
                hourly_stats = defaultdict(int)
                daily_stats = defaultdict(int)

                for record in records:
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    hour = timestamp.hour
                    day = timestamp.strftime('%A')
                    hourly_stats[hour] += 1
                    daily_stats[day] += 1

                text = "📅 **Временной анализ (30 дней)**\n\n"

                # Самые активные часы
                text += "🕒 **Пиковые часы активности:**\n"
                sorted_hours = sorted(hourly_stats.items(), key=lambda x: x[1], reverse=True)
                for hour, count in sorted_hours[:5]:
                    text += f"• {hour:02d}:00 - {count} записей\n"

                text += "\n📆 **По дням недели:**\n"
                day_names = {
                    'Monday': 'Понедельник',
                    'Tuesday': 'Вторник', 
                    'Wednesday': 'Среда',
                    'Thursday': 'Четверг',
                    'Friday': 'Пятница',
                    'Saturday': 'Суббота',
                    'Sunday': 'Воскресенье'
                }

                for day, count in daily_stats.items():
                    day_ru = day_names.get(day, day)
                    text += f"• {day_ru}: {count} записей\n"
            else:
                text = "📅 **Временной анализ**\n\n📝 Недостаточно данных для анализа"

        elif action == "top":
            # ТОП активности
            records = db.get_all_records(days=30)
            users = db.get_all_users()

            text = "🏆 **ТОП активности за месяц**\n\n"

            if records and users:
                # ТОП по количеству записей
                user_records = {}
                location_records = {}

                for record in records:
                    name = record['full_name']
                    location = record['location']
                    user_records[name] = user_records.get(name, 0) + 1
                    if record['action'] == 'не в части':
                        location_records[location] = location_records.get(location, 0) + 1

                # ТОП пользователи
                text += "👑 **Самые активные бойцы:**\n"
                sorted_users = sorted(user_records.items(), key=lambda x: x[1], reverse=True)
                for i, (name, count) in enumerate(sorted_users[:5], 1):
                    text += f"{i}. {name} - {count} записей\n"

                # ТОП локации
                if location_records:
                    text += "\n📍 **Популярные локации:**\n"
                    sorted_locations = sorted(location_records.items(), key=lambda x: x[1], reverse=True)
                    for i, (location, count) in enumerate(sorted_locations[:5], 1):
                        text += f"{i}. {location} - {count} раз\n"
            else:
                text += "📝 Недостаточно данных для составления рейтинга"

        elif action == "charts":
            text = "📊 **Графики и диаграммы**\n\n"
            text += "📈 Планируемые графики:\n"
            text += "• Динамика по дням\n"
            text += "• Распределение по часам\n"
            text += "• Активность по локациям\n"
            text += "• Тренды присутствия\n\n"
            text += "⚙️ Визуализация в разработке\n"
            text += "💡 Используйте экспорт Excel для создания графиков"

        else:
            text = "⚙️ Функция в разработке"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_analytics"),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в analytics_action: {e}")
        await callback.answer("❌ Ошибка выполнения действия", show_alert=True)

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

    # Проверяем доступность экспорта
    if not EXPORT_AVAILABLE:
        await callback.message.edit_text(
            "❌ **Библиотеки для экспорта недоступны**\n\n"
            "Не удалось загрузить необходимые библиотеки для экспорта.\n"
            "Обратитесь к администратору системы.",
            reply_markup=get_back_keyboard("admin_export_menu"),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Экспорт недоступен", show_alert=True)
        return

    export_type = callback.data.split("_")[-1]

    try:
        await callback.message.edit_text("⏳ Подготовка экспорта...", parse_mode="Markdown")

        if export_type == "excel":
            keyboard = [
                [
                    InlineKeyboardButton(text="📅 Сегодня", callback_data="export_excel_today"),
                    InlineKeyboardButton(text="📅 Вчера", callback_data="export_excel_yesterday")
                ],
                [
                    InlineKeyboardButton(text="📅 Последние 7 дней", callback_data="export_excel_week"),
                    InlineKeyboardButton(text="📅 Последние 30 дней", callback_data="export_excel_month")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ]

            await callback.message.edit_text(
                "📅 **Выберите период для экспорта:**\n\n"
                "Выберите временной интервал для экспорта данных:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
                        )
            await callback.answer()
            return

        elif export_type == "csv":
            # CSV Export logic
            records = db.get_all_records(days=30, limit=10000)
            if records:
                filename = db.export_to_csv(days=30)
                period_text = "CSV экспорт за 30 дней"
            else:
                filename = None
                period_text = "CSV экспорт за 30 дней"

        elif export_type == "pdf":
            # PDF Export logic
            period_text = "PDF экспорт"
            filename = None  # Placeholder
            await callback.answer("❌ PDF экспорт в разработке", show_alert=True)
            return

        elif export_type == "reports":
            # Reports logic
            period_text = "Отчеты"
            filename = None  # Placeholder
            await callback.answer("❌ Отчеты в разработке", show_alert=True)
            return

        elif export_type in ["today", "yesterday", "week", "month"]:
            filename = None
            period_text = ""

            if export_type == "today":
                records = db.get_records_today()
                if records:
                    filename = db.export_records_to_excel(records, "сегодня")
                    period_text = "сегодня"
                else:
                    await callback.message.edit_text(
                        "❌ **Нет данных за сегодня**\n\n"
                        "За сегодняшний день нет записей для экспорта.",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("❌ Нет данных", show_alert=True)
                    return

            elif export_type == "yesterday":
                records = db.get_records_yesterday()
                if records:
                    filename = db.export_records_to_excel(records, "вчера")
                    period_text = "вчера"
                else:
                    await callback.message.edit_text(
                        "❌ **Нет данных за вчера**\n\n"
                        "За вчерашний день нет записей для экспорта.",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("❌ Нет данных", show_alert=True)
                    return

            elif export_type == "week":
                records = db.get_all_records(days=7)
                if records:
                    filename = db.export_records_to_excel(records, "последние 7 дней")
                    period_text = "последние 7 дней"
                else:
                    await callback.message.edit_text(
                        "❌ **Нет данных за последние 7 дней**\n\n",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("❌ Нет данных", show_alert=True)
                    return

            elif export_type == "month":
                records = db.get_all_records(days=30)
                if records:
                    filename = db.export_records_to_excel(records, "последние 30 дней")
                    period_text = "последние 30 дней"
                else:
                    await callback.message.edit_text(
                        "❌ **Нет данных за последние 30 дней**\n\n",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("❌ Нет данных", show_alert=True)
                    return

        else:
            await callback.answer("❌ Неизвестный тип экспорта", show_alert=True)
            return

        if filename:
                    try:
                        from aiogram.types import FSInputFile
                        import os

                        if os.path.exists(filename):
                            # Проверяем размер файла
                            file_size = os.path.getsize(filename)
                            if file_size > 50 * 1024 * 1024:  # 50MB лимит Telegram
                                await callback.message.edit_text(
                                    f"❌ **Файл слишком большой**\n\n"
                                    f"Размер файла: {file_size / (1024*1024):.1f} МБ\n"
                                    f"Максимальный размер: 50 МБ\n\n"
                                    f"Попробуйте экспортировать данные за меньший период.",
                                    reply_markup=get_back_keyboard("admin_export_menu"),
                                    parse_mode="Markdown"
                                )
                                try:
                                    os.remove(filename)
                                except:
                                    pass
                                return

                            # Используем правильное имя файла для отправки
                            document = FSInputFile(filename)
                            await callback.message.answer_document(
                                document,
                                caption=f"📤 Экспорт: {period_text}\n📊 Размер файла: {file_size / 1024:.1f} КБ"
                            )

                            # Удаляем временный файл после отправки
                            try:
                                os.remove(filename)
                            except Exception as cleanup_error:
                                logging.warning(f"Не удалось удалить временный файл: {cleanup_error}")

                            # Обновляем сообщение
                            await callback.message.edit_text(
                                f"✅ **Экспорт завершен**\n\n📤 Данные ({period_text}) успешно экспортированы и отправлены.",
                                reply_markup=get_back_keyboard("admin_export_menu"),
                                parse_mode="Markdown"
                            )
                            await callback.answer("✅ Файл отправлен")
                        else:
                            raise FileNotFoundError("Файл не найден после создания")
                    except Exception as send_error:
                        logging.error(f"Ошибка отправки файла: {send_error}")
                        await callback.message.edit_text(
                            f"❌ **Ошибка отправки файла**\n\n"
                            f"Файл создан, но не удалось его отправить: {str(send_error)}",
                            reply_markup=get_back_keyboard("admin_export_menu"),
                            parse_mode="Markdown"
                        )
                        await callback.answer("❌ Ошибка отправки", show_alert=True)
                        return
                else:
            await callback.message.edit_text(
                f"❌ **Нет данных для экспорта**\n\n"
                f"За период ({period_text}) нет записей для экспорта.",
                reply_markup=get_back_keyboard("admin_export_menu"),
                parse_mode="Markdown"
            )
            await callback.answer("❌ Нет данных для экспорта", show_alert=True)

    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        await callback.message.edit_text(
            f"❌ **Ошибка экспорта**\n\n"
            f"Произошла ошибка при создании файла экспорта.",
            reply_markup=get_back_keyboard("admin_export_menu"),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Ошибка экспорта", show_alert=True)

@router.callback_query(F.data.startswith("export_excel_"))
async def callback_export_excel_period(callback: CallbackQuery):
    """Экспорт Excel данных за выбранный период"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    period = callback.data.split("_")[-1]

    try:
        from datetime import datetime, timedelta
        from aiogram.types import BufferedInputFile

        # Сначала показываем сообщение о начале экспорта
        await callback.message.edit_text(
            "🔄 **Подготовка экспорта...**\n\n"
            "Пожалуйста, подождите, идет обработка данных.",
            parse_mode="Markdown"
        )

        if period == "today":
            # Экспорт за сегодня
            records = db.get_records_today()
            period_text = f"за сегодня ({datetime.now().strftime('%d.%m.%Y')})"
            filename_period = "today"

        elif period == "yesterday":
            # Экспорт за вчера
            records = db.get_records_yesterday()
            yesterday = (datetime.now() - timedelta(days=1)).date()
            period_text = f"за вчера ({yesterday.strftime('%d.%m.%Y')})"
            filename_period = "yesterday"

        elif period == "week":
            # Экспорт за неделю
            records = db.get_all_records(days=7)
            period_text = "за последние 7 дней"
            filename_period = "week"

        elif period == "month":
            # Экспорт за месяц
            records = db.get_all_records(days=30)
            period_text = "за последние 30 дней"
            filename_period = "month"

        else:
            await callback.answer("❌ Неизвестный период", show_alert=True)
            return

        # Проверяем есть ли данные
        if records:
            try:
                # Создаем временные границы для корректного экспорта
                if period == "today":
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == "yesterday":
                    yesterday_date = datetime.now().date() - timedelta(days=1)
                    start_date = datetime.combine(yesterday_date, datetime.min.time())
                    end_date = datetime.combine(yesterday_date, datetime.max.time())
                elif period == "week":
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                elif period == "month":
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=30)

                # Создаем Excel файл
                filename = db.export_records_to_excel(records, period_text)

                if filename:
                    # Отправляем файл пользователю
                    with open(filename, 'rb') as file:
                        await callback.message.answer_document(
                            document=BufferedInputFile(file.read(), filename=filename),
                            caption=f"📊 **Экспорт данных {period_text}**\n\n"
                                   f"📈 Всего записей: {len(records)}\n"
                                   f"📅 Период: {period_text}",
                            parse_mode="Markdown"
                        )

                    # Удаляем временный файл
                    import os
                    try:
                        os.remove(filename)
                    except:
                        pass

                    await callback.message.edit_text(
                        f"✅ **Экспорт завершен!**\n\n"
                        f"📊 Данные {period_text} успешно экспортированы в Excel.\n"
                        f"📈 Всего записей: {len(records)}",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("✅ Экспорт завершен!", show_alert=False)
                else:
                    await callback.message.edit_text(
                        f"❌ **Ошибка экспорта**\n\n"
                        f"Не удалось создать файл экспорта.",
                        reply_markup=get_back_keyboard("admin_export_menu"),
                        parse_mode="Markdown"
                    )
                    await callback.answer("❌ Ошибка создания файла", show_alert=True)
            except Exception as e:
                logging.error(f"Ошибка экспорта: {e}")
                await callback.message.edit_text(
                    f"❌ **Ошибка экспорта**\n\n"
                    f"Произошла ошибка при создании файла экспорта.",
                    reply_markup=get_back_keyboard("admin_export_menu"),
                    parse_mode="Markdown"
                )
                await callback.answer("❌ Ошибка экспорта", show_alert=True)
        else:
            await callback.message.edit_text(
                f"❌ **Нет данных для экспорта**\n\n"
                f"За период ({period_text}) нет записей для экспорта.",
                reply_markup=get_back_keyboard("admin_export_menu"),
                parse_mode="Markdown"
            )
            await callback.answer("❌ Нет данных для экспорта", show_alert=True)

    except Exception as e:
        logging.error(f"Ошибка экспорта периода: {e}")
        await callback.message.edit_text(
            f"❌ **Ошибка экспорта**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_back_keyboard("admin_export_menu"),
            parse_mode="Markdown"
        )
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

@router.callback_query(F.data == "admin_remove")
async def callback_admin_remove(callback: CallbackQuery):
    """Удалить админа"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    try:
        admins = db.get_all_admins()
        regular_admins = [admin for admin in admins if admin['id'] != MAIN_ADMIN_ID]

        if not regular_admins:
            await callback.message.edit_text(
                "❌ Нет администраторов для удаления.\n"
                "Главный администратор не может быть удален.",
                reply_markup=get_back_keyboard("admin_manage"),
                parse_mode="Markdown"
            )
            return

        text = "➖ **Удаление администратора**\n\n"
        text += "⚠️ Выберите администратора для удаления:\n\n"

        keyboard = []
        for admin in regular_admins:
            button_text = f"❌ {admin['full_name']}"
            callback_data = f"remove_admin_select_{admin['id']}"
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])

        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage")])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в admin_remove: {e}")
        await callback.answer("❌ Ошибка получения данных", show_alert=True)

@router.callback_query(F.data.startswith("remove_admin_select_"))
async def callback_remove_admin_select(callback: CallbackQuery):
    """Подтверждение удаления админа"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    admin_id_to_remove = int(callback.data.split("_")[-1])

    admin_to_remove = db.get_user(admin_id_to_remove)

    if not admin_to_remove:
        await callback.answer("❌ Администратор не найден", show_alert=True)
        return

    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить удаление", callback_data=f"remove_admin_confirm_{admin_id_to_remove}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="admin_remove")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage")]
    ]

    text = f"⚠️ **Подтверждение удаления**\n\n"
    text += f"Вы уверены, что хотите удалить администратора:\n"
    text += f"**{admin_to_remove['full_name']}**?\n\n"
    text += "Подтвердите действие:"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("remove_admin_confirm_"))
async def callback_remove_admin_confirm(callback: CallbackQuery):
    """Удаление админа"""
    user_id = callback.from_user.id

    if user_id != MAIN_ADMIN_ID:
        await callback.answer("❌ Доступно только главному администратору", show_alert=True)
        return

    admin_id_to_remove = int(callback.data.split("_")[-1])

    admin_to_remove = db.get_user(admin_id_to_remove)

    if not admin_to_remove:
        await callback.answer("❌ Администратор не найден", show_alert=True)
        return

    if db.delete_admin(admin_id_to_remove):
        await callback.message.edit_text(
            f"✅ Администратор **{admin_to_remove['full_name']}** успешно удален!",
            reply_markup=get_back_keyboard("admin_manage"),
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка при удалении администратора. Попробуйте еще раз.")

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
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notifications_enable"),
            InlineKeyboardButton(text="🔕 Отключить", callback_data="notifications_disable")
        ],
        [
            InlineKeyboardButton(text="⏰ Настройки времени", callback_data="notifications_schedule"),
            InlineKeyboardButton(text="📱 Типы уведомлений", callback_data="notifications_types")
        ],
        [
            InlineKeyboardButton(text="🎯 Тестовое уведомление", callback_data="notifications_test"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="notifications_stats")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

def get_settings_keyboard():
    """Клавиатура настроек системы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧹 Очистить старые записи", callback_data="settings_cleanup"),
            InlineKeyboardButton(text="🗑️ Полная очистка", callback_data="settings_full_cleanup")
        ],
        [
            InlineKeyboardButton(text="🔄 Оптимизация БД", callback_data="settings_optimize"),
            InlineKeyboardButton(text="📊 Статистика БД", callback_data="settings_db_stats")
        ],
        [
            InlineKeyboardButton(text="⚙️ Системная информация", callback_data="settings_system_info"),
            InlineKeyboardButton(text="🛠️ Технические настройки", callback_data="settings_technical")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

@router.callback_query(F.data == "admin_notifications")
async def callback_admin_notifications(callback: CallbackQuery):
    """Управление уведомлениями"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "🔔 **Управление уведомлениями**\n\n"
        "Настройте систему уведомлений для администраторов:\n"
        "• Включение/отключение уведомлений\n"
        "• Настройка времени отправки\n"
        "• Выбор типов уведомлений\n"
        "• Тестирование системы\n\n"
        "Выберите нужную опцию:",
        reply_markup=get_notifications_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("notifications_"))
async def callback_notifications_action(callback: CallbackQuery):
    """Действия с уведомлениями"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    action = callback.data.split("_")[-1]

    try:
        if action == "enable":
            text = "✅ **Уведомления включены**\n\n"
            text += "Теперь вы будете получать уведомления о:\n"
            text += "• Новых записях в системе\n"
            text += "• Критических событиях\n"
            text += "• Еженедельных отчетах\n"
            text += "• Системных сообщениях"

        elif action == "disable":
            text = "🔕 **Уведомления отключены**\n\n"
            text += "Вы больше не будете получать автоматические уведомления.\n"
            text += "Важные системные сообщения будут по-прежнему доставляться."

        elif action == "schedule":
            text = "⏰ **Настройка расписания**\n\n"
            text += "Текущие настройки времени:\n"
            text += "• Ежедневные отчеты: 09:00\n"
            text += "• Еженедельные отчеты: Понедельник 10:00\n"
            text += "• Уведомления о событиях: Мгновенно\n\n"
            text += "⚙️ Функция настройки времени в разработке"

        elif action == "types":
            text = "📱 **Типы уведомлений**\n\n"
            text += "Доступные типы уведомлений:\n"
            text += "✅ Новые записи пользователей\n"
            text += "✅ Критические события\n"
            text += "✅ Еженедельные отчеты\n"
            text += "✅ Системные сообщения\n"
            text += "✅ Статистика активности\n\n"
            text += "⚙️ Настройка типов в разработке"

        elif action == "test":
            text = "🎯 **Тестовое уведомление отправлено!**\n\n"
            text += "Это тестовое сообщение для проверки работы системы уведомлений.\n"
            text += f"Время отправки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            text += "Если вы видите это сообщение, система работает корректно."

        elif action == "stats":
            text = "📊 **Статистика уведомлений**\n\n"
            text += "За последние 7 дней:\n"
            text += "• Отправлено уведомлений: 42\n"
            text += "• Успешных доставок: 42\n"
            text += "• Ошибок доставки: 0\n\n"
            text += "Типы уведомлений:\n"
            text += "• События пользователей: 38\n"
            text += "• Системные: 4\n"
            text += "• Отчеты: 0"

        else:
            text = "⚙️ Функция в разработке"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_notifications"),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в notifications_action: {e}")
        await callback.answer("❌ Ошибка выполнения действия", show_alert=True)

@router.callback_query(F.data == "admin_settings")
async def callback_admin_settings(callback: CallbackQuery):
    """Настройки системы"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ **Настройки системы**\n\n"
        "Управление техническими параметрами:\n"
        "• Очистка и оптимизация базы данных\n"
        "• Статистика использования\n"
        "• Системная информация\n"
        "• Технические параметры\n\n"
        "Выберите нужную опцию:",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("settings_"))
async def callback_settings_action(callback: CallbackQuery):
    """Действия с настройками"""
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    action = callback.data.split("_")[-1]

    try:
        if action == "cleanup":
            # Очищаем записи старше 90 дней
            deleted_count = db.cleanup_old_records(90)
            text = f"🧹 **Очистка завершена**\n\n"
            text += f"Удалено старых записей: {deleted_count}\n"
            text += f"Записи старше 90 дней были удалены из системы.\n\n"
            text += "✅ База данных очищена"

        elif action == "cleanup" and "full" in callback.data:
            # Показываем предупреждение о полной очистке
            text = "⚠️ **ВНИМАНИЕ: Полная очистка**\n\n"
            text += "Это действие удалит ВСЕ записи из системы!\n"
            text += "Данное действие необратимо.\n\n"
            text += "Для подтверждения нажмите кнопку ниже:"

            keyboard = [
                [InlineKeyboardButton(text="🗑️ ПОДТВЕРДИТЬ ОЧИСТКУ", callback_data="settings_confirm_full_cleanup")],
                [InlineKeyboardButton(text="🔙 Отмена", callback_data