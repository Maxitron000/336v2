from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID

router = Router()
db = DatabaseService()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - показать статистику"""
    # Проверяем права доступа
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ У вас нет прав для просмотра статистики.")
        return

    try:
        stats = db.get_current_status()

        stats_text = f"""📊 **Текущая статистика**

👥 Всего личного состава: {stats['total']}
✅ Присутствуют: {stats['present']}
❌ Отсутствуют: {stats['absent']}

**📍 Отсутствующие:**
"""

        if stats['absent_list']:
            for person in stats['absent_list']:
                stats_text += f"• {person['name']} ({person['location']})\n"
        else:
            stats_text += "Все на месте! ✅"

        await message.answer(stats_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}")
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID
import logging
from datetime import datetime, timedelta

router = Router()
db = DatabaseService()

async def is_admin(user_id: int) -> bool:
    """Проверить права администратора"""
    if user_id == MAIN_ADMIN_ID:
        return True
    return db.is_admin(user_id)

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    """Показать расширенную статистику"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        # Получаем статистику за разные периоды
        stats_today = db.get_all_records(days=1)
        stats_week = db.get_all_records(days=7)
        stats_month = db.get_all_records(days=30)
        
        current_status = db.get_current_status()
        
        text = "📊 **Расширенная статистика**\n\n"
        
        # Текущий статус
        text += "🔄 **Текущий статус:**\n"
        text += f"👥 Всего бойцов: {current_status['total']}\n"
        text += f"✅ В части: {current_status['present']}\n"
        text += f"❌ Вне части: {current_status['absent']}\n\n"
        
        # Активность по периодам
        text += "📈 **Активность:**\n"
        text += f"📅 Сегодня: {len(stats_today)} записей\n"
        text += f"📅 За неделю: {len(stats_week)} записей\n"
        text += f"📅 За месяц: {len(stats_month)} записей\n\n"
        
        # ТОП локации за неделю
        if stats_week:
            locations = {}
            for record in stats_week:
                if record['action'] == 'не в части':
                    loc = record['location']
                    locations[loc] = locations.get(loc, 0) + 1
            
            if locations:
                text += "🏆 **ТОП локации (неделя):**\n"
                sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (location, count) in enumerate(sorted_locations, 1):
                    text += f"{i}. {location}: {count} раз\n"
        
        keyboard = [
            [InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка в admin_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)

@router.callback_query(F.data == "admin_journal_stats")
async def callback_journal_stats(callback: CallbackQuery):
    """Статистика по журналу"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        # Получаем записи за последние 7 дней
        records = db.get_all_records(days=7, limit=1000)
        
        if not records:
            text = "📊 **Статистика журнала**\n\nНет данных за последние 7 дней."
        else:
            # Подсчет по действиям
            actions_count = {}
            users_activity = {}
            locations_count = {}
            
            for record in records:
                # Подсчет действий
                action = record['action']
                actions_count[action] = actions_count.get(action, 0) + 1
                
                # Активность пользователей
                user_name = record['full_name']
                users_activity[user_name] = users_activity.get(user_name, 0) + 1
                
                # Популярные локации для убытия
                if action == 'не в части':
                    location = record['location']
                    locations_count[location] = locations_count.get(location, 0) + 1
            
            text = "📊 **Статистика журнала (7 дней)**\n\n"
            
            # Статистика по действиям
            text += "📋 **По действиям:**\n"
            for action, count in actions_count.items():
                emoji = "🟢" if action == "в части" else "🔴"
                text += f"{emoji} {action}: {count} раз\n"
            text += "\n"
            
            # ТОП активных пользователей
            text += "👥 **Самые активные (ТОП-5):**\n"
            sorted_users = sorted(users_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (user, count) in enumerate(sorted_users, 1):
                text += f"{i}. {user}: {count} записей\n"
            text += "\n"
            
            # ТОП локации для убытия
            if locations_count:
                text += "📍 **Популярные места убытия:**\n"
                sorted_locations = sorted(locations_count.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (location, count) in enumerate(sorted_locations, 1):
                    text += f"{i}. {location}: {count} раз\n"
        
        keyboard = [
            [InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_journal_export")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_journal")]
        ]
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка в journal_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)

@router.callback_query(F.data == "admin_journal_export")
async def callback_journal_export(callback: CallbackQuery):
    """Экспорт журнала в Excel"""
    user_id = callback.from_user.id

    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    try:
        filename = db.export_to_excel(days=30)
        if filename:
            from aiogram.types import FSInputFile
            document = FSInputFile(filename, filename="journal_export.xlsx")
            await callback.message.answer_document(
                document,
                caption="📤 **Экспорт журнала** за последние 30 дней",
                parse_mode="Markdown"
            )
            await callback.answer("✅ Файл отправлен")
        else:
            await callback.answer("❌ Нет данных для экспорта", show_alert=True)
    except Exception as e:
        logging.error(f"Ошибка экспорта журнала: {e}")
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats для админов"""
    user_id = message.from_user.id

    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return

    try:
        current_status = db.get_current_status()
        
        text = "📊 **Быстрая сводка**\n\n"
        text += f"👥 Всего бойцов: {current_status['total']}\n"
        text += f"✅ В части: {current_status['present']}\n"
        text += f"❌ Вне части: {current_status['absent']}\n\n"
        
        # Отображаем группировку по локациям
        if current_status.get('location_groups'):
            text += "📍 **Группировка по локациям:**\n\n"
            
            # Сначала показываем тех, кто в части
            if 'В части' in current_status['location_groups']:
                group = current_status['location_groups']['В части']
                text += f"🟢 **В части: {group['count']}**\n"
                for name in group['names'][:10]:  # Показываем максимум 10
                    text += f"• {name}\n"
                if len(group['names']) > 10:
                    text += f"... и еще {len(group['names']) - 10}\n"
                text += "\n"
            
            # Затем показываем отсутствующих по локациям
            for location, group in current_status['location_groups'].items():
                if location != 'В части':
                    text += f"🔴 **{location}: {group['count']}**\n"
                    for name in group['names'][:5]:  # Показываем максимум 5 для внешних локаций
                        text += f"• {name}\n"
                    if len(group['names']) > 5:
                        text += f"... и еще {len(group['names']) - 5}\n"
                    text += "\n"
        
        if current_status['total'] == 0:
            text += "ℹ️ Нет зарегистрированных бойцов"
        
        keyboard = [
            [InlineKeyboardButton(text="📈 Подробная статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")]
        ]
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Ошибка в cmd_stats: {e}")
        await message.answer("❌ Ошибка получения статистики")
