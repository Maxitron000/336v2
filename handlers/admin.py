
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DBService
from config import MAIN_ADMIN_ID, LOCATIONS
from keyboards import *
import logging
import os
from datetime import datetime, timedelta
import pytz
import json
import io
import aiofiles
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import asyncio

router = Router()

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_admin_id = State()
    waiting_for_user_delete = State()
    waiting_for_confirmation = State()
    waiting_for_export_name = State()

# Калининградский часовой пояс
KALININGRAD_TZ = pytz.timezone('Europe/Kaliningrad')

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    if user_id == MAIN_ADMIN_ID:
        return True
    user = await DBService.get_user(user_id)
    return user and user.get('is_admin', False)

async def is_main_admin(user_id: int) -> bool:
    """Проверка главного админа"""
    return user_id == MAIN_ADMIN_ID

def format_kaliningrad_time(dt_str):
    """Форматирование времени в калининградский часовой пояс"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        kld_time = dt.astimezone(KALININGRAD_TZ)
        return kld_time.strftime('%d.%m.%Y %H:%M')
    except:
        return dt_str

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Админ-панель через команду"""
    try:
        if not await is_admin(message.from_user.id):
            await message.answer("❌ У вас нет прав администратора")
            return

        await state.clear()
        
        # Удаляем команду пользователя
        try:
            await message.delete()
        except:
            pass

        admin_text = """
🛡️ **АДМИН-ПАНЕЛЬ**
336 инженерно-маскировочный батальон

🎯 Система управления электронным табелем
⚡ Выберите раздел для работы:
        """
        
        await message.answer(
            admin_text,
            reply_markup=get_admin_main_keyboard(await is_main_admin(message.from_user.id)),
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Ошибка в cmd_admin: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Главная админ-панель"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return
        
        await state.clear()
        
        admin_text = """
🛡️ **АДМИН-ПАНЕЛЬ**
336 инженерно-маскировочный батальон

🎯 Система управления электронным табелем
⚡ Выберите раздел для работы:
        """
        
        await callback.message.edit_text(
            admin_text,
            reply_markup=get_admin_main_keyboard(await is_main_admin(callback.from_user.id)),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_panel: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data == "admin_personnel")
async def callback_admin_personnel(callback: CallbackQuery):
    """Управление личным составом"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        users = await DBService.get_all_users()
        soldiers = [u for u in users if not u.get('is_admin', False)]
        admins = [u for u in users if u.get('is_admin', False)]
        
        text = f"""
👥 **УПРАВЛЕНИЕ ЛИЧНЫМ СОСТАВОМ**

📊 **Сводка:**
• 👨‍💼 Администраторов: {len(admins)}
• 🪖 Личный состав: {len(soldiers)}
• 📝 Всего пользователей: {len(users)}

⚙️ Выберите действие:
        """
        
        await callback.message.edit_text(
            text,
            reply_markup=get_personnel_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_personnel: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "personnel_list")
async def callback_personnel_list(callback: CallbackQuery):
    """Список личного состава"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        users = await DBService.get_all_users()
        soldiers = sorted([u for u in users if not u.get('is_admin', False)], 
                         key=lambda x: x['full_name'])
        
        if not soldiers:
            text = "👥 **ЛИЧНЫЙ СОСТАВ**\n\n❌ Личный состав пуст"
        else:
            text = f"👥 **ЛИЧНЫЙ СОСТАВ** ({len(soldiers)} чел.)\n\n"
            
            # Разбиваем на две колонки для компактности
            for i in range(0, len(soldiers), 2):
                left = soldiers[i]
                right = soldiers[i + 1] if i + 1 < len(soldiers) else None
                
                # Получаем последний статус
                records = await DBService.get_user_records(left['id'], 1)
                left_status = "🏠" if records and records[0]['action'] == 'прибыл' else "🚶"
                
                line = f"{left_status} {left['full_name']}"
                
                if right:
                    right_records = await DBService.get_user_records(right['id'], 1)
                    right_status = "🏠" if right_records and right_records[0]['action'] == 'прибыл' else "🚶"
                    line += f"  |  {right_status} {right['full_name']}"
                
                text += line + "\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_personnel"),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_personnel_list: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "personnel_status")
async def callback_personnel_status(callback: CallbackQuery):
    """Статус всех бойцов"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        text = """
📊 **СТАТУС ЛИЧНОГО СОСТАВА**

🎯 Выберите отображение:
        """
        
        await callback.message.edit_text(
            text,
            reply_markup=get_status_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_personnel_status: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data.startswith("status_"))
async def callback_status_display(callback: CallbackQuery):
    """Отображение статуса"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        status_type = callback.data.split("_")[1]  # all, present, absent
        
        users = await DBService.get_all_users()
        soldiers = sorted([u for u in users if not u.get('is_admin', False)], 
                         key=lambda x: x['full_name'])
        
        present = []
        absent = []
        
        for soldier in soldiers:
            records = await DBService.get_user_records(soldier['id'], 1)
            if records and records[0]['action'] == 'прибыл':
                present.append((soldier, records[0]))
            else:
                absent.append((soldier, records[0] if records else None))
        
        if status_type == "all":
            text = f"""
📊 **СТАТУС ВСЕХ** ({len(soldiers)} чел.)

🏠 **НА МЕСТЕ** ({len(present)} чел.):
"""
            for soldier, record in present:
                time_str = format_kaliningrad_time(record['timestamp']) if record else "—"
                location = record['location'] if record else "—"
                text += f"• {soldier['full_name']} ({time_str}, {location})\n"
            
            text += f"\n🚶 **УБЫЛИ** ({len(absent)} чел.):\n"
            for soldier, record in absent:
                time_str = format_kaliningrad_time(record['timestamp']) if record else "—"
                location = record['location'] if record else "—"
                text += f"• {soldier['full_name']} ({time_str}, {location})\n"
                
        elif status_type == "present":
            text = f"🏠 **НА МЕСТЕ** ({len(present)} чел.):\n\n"
            for soldier, record in present:
                time_str = format_kaliningrad_time(record['timestamp']) if record else "—"
                location = record['location'] if record else "—"
                text += f"• {soldier['full_name']}\n  📍 {location}\n  ⏰ {time_str}\n\n"
                
        else:  # absent
            text = f"🚶 **УБЫЛИ** ({len(absent)} чел.):\n\n"
            for soldier, record in absent:
                time_str = format_kaliningrad_time(record['timestamp']) if record else "—"
                location = record['location'] if record else "—"
                text += f"• {soldier['full_name']}\n  📍 {location}\n  ⏰ {time_str}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("personnel_status"),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_status_display: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "personnel_delete")
async def callback_personnel_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление бойца"""
    try:
        if not await is_main_admin(callback.from_user.id):
            await callback.answer("❌ Доступно только главному админу", show_alert=True)
            return
        
        users = await DBService.get_all_users()
        soldiers = sorted([u for u in users if not u.get('is_admin', False)], 
                         key=lambda x: x['full_name'])
        
        if not soldiers:
            await callback.answer("❌ Нет бойцов для удаления", show_alert=True)
            return
        
        text = """
❌ **УДАЛЕНИЕ БОЙЦА**

⚠️ **ВНИМАНИЕ!** Это действие необратимо!
Будут удалены все записи бойца.

📝 Введите **точную фамилию** бойца для удаления:

📋 **Доступные бойцы:**
"""
        
        for soldier in soldiers:
            text += f"• {soldier['full_name']}\n"
        
        await state.set_state(AdminStates.waiting_for_user_delete)
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_personnel"),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_personnel_delete: {e}")
        await callback.answer("❌ Ошибка")

@router.message(AdminStates.waiting_for_user_delete)
async def process_user_delete(message: Message, state: FSMContext):
    """Обработка удаления пользователя"""
    try:
        name_to_delete = message.text.strip()
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        
        # Ищем пользователя
        users = await DBService.get_all_users()
        target_user = None
        
        for user in users:
            if user['full_name'] == name_to_delete and not user.get('is_admin', False):
                target_user = user
                break
        
        if not target_user:
            await message.answer(
                f"❌ Боец с именем '{name_to_delete}' не найден!\n\nВведите точную фамилию:",
                reply_markup=get_back_keyboard("admin_personnel")
            )
            return
        
        # Просим подтверждение
        await state.update_data(user_to_delete=target_user['id'])
        await state.set_state(AdminStates.waiting_for_confirmation)
        
        confirm_text = f"""
⚠️ **ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ**

👤 **Боец:** {target_user['full_name']}
🆔 **ID:** {target_user['id']}

❗ **Это действие НЕОБРАТИМО!**
Будут удалены ВСЕ записи этого бойца.

🔴 Для подтверждения введите: **ДА**
        """
        
        await message.answer(
            confirm_text,
            reply_markup=get_back_keyboard("admin_personnel"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Ошибка в process_user_delete: {e}")
        await message.answer("❌ Произошла ошибка")

@router.message(AdminStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения удаления"""
    try:
        confirmation = message.text.strip().upper()
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        
        if confirmation != "ДА":
            await message.answer(
                "❌ Удаление отменено.\n\nДля подтверждения нужно ввести: **ДА**",
                reply_markup=get_back_keyboard("admin_personnel"),
                parse_mode='Markdown'
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        user_id = data.get('user_to_delete')
        
        if not user_id:
            await message.answer(
                "❌ Ошибка: пользователь не найден",
                reply_markup=get_back_keyboard("admin_personnel")
            )
            await state.clear()
            return
        
        # Удаляем пользователя
        success = await DBService.delete_user(user_id)
        
        if success:
            await message.answer(
                "✅ **Боец успешно удален!**\n\nВсе его записи также удалены из системы.",
                reply_markup=get_back_keyboard("admin_personnel"),
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "❌ Ошибка при удалении бойца",
                reply_markup=get_back_keyboard("admin_personnel")
            )
        
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в process_confirmation: {e}")
        await message.answer("❌ Произошла ошибка")
        await state.clear()

@router.callback_query(F.data == "admin_manage")
async def callback_admin_manage(callback: CallbackQuery):
    """Управление администраторами"""
    try:
        if not await is_main_admin(callback.from_user.id):
            await callback.answer("❌ Доступно только главному админу", show_alert=True)
            return
        
        admins = await DBService.get_all_admins()
        
        text = f"""
👑 **УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ**

📊 **Текущие администраторы:** {len(admins)}

"""
        
        for admin in admins:
            role = "👑 Главный" if admin['id'] == MAIN_ADMIN_ID else "🛡️ Админ"
            text += f"• {role} {admin['full_name']}\n"
        
        text += "\n⚙️ Выберите действие:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_manage_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_manage: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "add_admin")
async def callback_add_admin(callback: CallbackQuery, state: FSMContext):
    """Добавление администратора"""
    try:
        if not await is_main_admin(callback.from_user.id):
            await callback.answer("❌ Доступно только главному админу", show_alert=True)
            return
        
        users = await DBService.get_all_users()
        soldiers = [u for u in users if not u.get('is_admin', False)]
        
        if not soldiers:
            await callback.answer("❌ Нет доступных пользователей", show_alert=True)
            return
        
        text = """
➕ **ДОБАВЛЕНИЕ АДМИНИСТРАТОРА**

📝 Введите **Telegram ID** пользователя:

💡 **Как узнать ID:**
1. Попросите пользователя написать боту /start
2. Найдите его ID в списке ниже

📋 **Доступные пользователи:**
"""
        
        for soldier in sorted(soldiers, key=lambda x: x['full_name']):
            text += f"• {soldier['full_name']} (ID: `{soldier['id']}`)\n"
        
        await state.set_state(AdminStates.waiting_for_admin_id)
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_manage"),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_add_admin: {e}")
        await callback.answer("❌ Ошибка")

@router.message(AdminStates.waiting_for_admin_id)
async def process_admin_id(message: Message, state: FSMContext):
    """Обработка добавления админа"""
    try:
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        
        try:
            admin_id = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ Неверный формат ID!\n\nВведите числовой ID:",
                reply_markup=get_back_keyboard("admin_manage")
            )
            return
        
        # Проверяем существование пользователя
        user = await DBService.get_user(admin_id)
        if not user:
            await message.answer(
                f"❌ Пользователь с ID {admin_id} не найден!\n\nПроверьте ID:",
                reply_markup=get_back_keyboard("admin_manage")
            )
            return
        
        # Проверяем, не админ ли уже
        if user.get('is_admin', False):
            await message.answer(
                f"❌ {user['full_name']} уже является администратором!",
                reply_markup=get_back_keyboard("admin_manage")
            )
            await state.clear()
            return
        
        # Добавляем права админа
        success = await DBService.set_admin_status(admin_id, True)
        
        if success:
            await message.answer(
                f"✅ **{user['full_name']}** назначен администратором!",
                reply_markup=get_back_keyboard("admin_manage"),
                parse_mode='Markdown'
            )
            
            # Уведомляем нового админа
            try:
                from main import bot
                await bot.send_message(
                    admin_id,
                    "🎉 **Поздравляем!**\n\nВам предоставлены права администратора в системе электронного табеля.",
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await message.answer(
                "❌ Ошибка при назначении администратора",
                reply_markup=get_back_keyboard("admin_manage")
            )
        
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в process_admin_id: {e}")
        await message.answer("❌ Произошла ошибка")
        await state.clear()

@router.callback_query(F.data == "admin_journal")
async def callback_admin_journal(callback: CallbackQuery):
    """Журнал событий"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        stats = await DBService.get_statistics()
        
        text = f"""
📖 **ЖУРНАЛ СОБЫТИЙ**

📊 **Статистика:**
• 📝 Всего записей: {stats.get('records', 0)}
• 👥 Пользователей: {stats.get('users', 0)}
• 🕐 За сегодня: {stats.get('today_records', 0)}

⚙️ Выберите действие:
        """
        
        await callback.message.edit_text(
            text,
            reply_markup=get_journal_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_admin_journal: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "journal_view")
async def callback_journal_view(callback: CallbackQuery):
    """Просмотр журнала"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        records = await DBService.get_all_records_with_names(20)
        
        if not records:
            text = "📖 **ЖУРНАЛ СОБЫТИЙ**\n\n❌ Записей нет"
        else:
            text = f"📖 **ЖУРНАЛ СОБЫТИЙ** (последние 20)\n\n"
            
            # Сортируем по алфавиту ФИО
            records_sorted = sorted(records, key=lambda x: x['full_name'])
            
            for record in records_sorted[:20]:
                action_emoji = "🏠" if record['action'] == 'прибыл' else "🚶"
                time_str = format_kaliningrad_time(record['timestamp'])
                
                text += f"{action_emoji} **{record['full_name']}**\n"
                text += f"   📍 {record['action']} - {record['location']}\n"
                text += f"   ⏰ {time_str}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin_journal"),
            parse_mode='Markdown'
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в callback_journal_view: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "journal_export")
async def callback_journal_export(callback: CallbackQuery, state: FSMContext):
    """Экспорт журнала"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        await callback.answer("📤 Создание файла...", show_alert=True)
        
        # Получаем все записи с именами
        records = await DBService.get_all_records_with_names(1000)
        
        if not records:
            await callback.message.edit_text(
                "❌ **Нет данных для экспорта**",
                reply_markup=get_back_keyboard("admin_journal"),
                parse_mode='Markdown'
            )
            return
        
        # Создаем Excel файл
        excel_file = await create_excel_export(records)
        
        if excel_file:
            # Отправляем файл
            file = FSInputFile(excel_file, filename=f"journal_{datetime.now().strftime('%d_%m_%Y')}.xlsx")
            
            await callback.message.answer_document(
                file,
                caption=f"📊 **Журнал табеля выхода в город**\n\n📅 Дата: {datetime.now(KALININGRAD_TZ).strftime('%d.%m.%Y %H:%M')}\n📝 Записей: {len(records)}\n🏛️ 336 инженерно-маскировочный батальон",
                parse_mode='Markdown'
            )
            
            # Удаляем временный файл
            try:
                os.remove(excel_file)
            except:
                pass
            
            await callback.message.edit_text(
                "✅ **Журнал успешно экспортирован!**",
                reply_markup=get_back_keyboard("admin_journal"),
                parse_mode='Markdown'
            )
        else:
            await callback.message.edit_text(
                "❌ **Ошибка создания файла**",
                reply_markup=get_back_keyboard("admin_journal"),
                parse_mode='Markdown'
            )
    except Exception as e:
        logging.error(f"Ошибка в callback_journal_export: {e}")
        await callback.answer("❌ Ошибка экспорта")

async def create_excel_export(records):
    """Создание Excel файла с красивым оформлением"""
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Журнал выходов"
        
        # Заголовки
        headers = ['№', 'ФИО', 'Действие', 'Локация', 'Дата', 'Время']
        ws.append(headers)
        
        # Стиль заголовков
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Данные
        arrive_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")  # Зеленый
        leave_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")   # Красный
        
        # Сортируем записи по ФИО
        sorted_records = sorted(records, key=lambda x: (x['full_name'], x['timestamp']))
        
        for idx, record in enumerate(sorted_records, 1):
            dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            kld_time = dt.astimezone(KALININGRAD_TZ)
            
            row_data = [
                idx,
                record['full_name'],
                record['action'],
                record['location'],
                kld_time.strftime('%d.%m.%Y'),
                kld_time.strftime('%H:%M')
            ]
            
            ws.append(row_data)
            
            # Применяем цветовую заливку
            fill = arrive_fill if record['action'] == 'прибыл' else leave_fill
            for col in range(1, len(row_data) + 1):
                ws.cell(row=idx + 1, column=col).fill = fill
        
        # Настройка ширины колонок
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 8
        
        # Добавляем заголовок документа
        ws.insert_rows(1)
        ws.merge_cells('A1:F1')
        title_cell = ws['A1']
        title_cell.value = f"ЖУРНАЛ ВЫХОДА В ГОРОД - 336 инженерно-маскировочный батальон ({datetime.now(KALININGRAD_TZ).strftime('%d.%m.%Y')})"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")
        
        # Сохраняем файл
        filename = f"journal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)
        
        return filename
    except Exception as e:
        logging.error(f"Ошибка создания Excel: {e}")
        return None
