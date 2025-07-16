import re
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from keyboards import *
from config import MAIN_ADMIN_ID

class Handlers:
    def __init__(self):
        self.db = Database()
        self.user_states = {}  # Для хранения состояний пользователей
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        
        # Проверяем, зарегистрирован ли пользователь
        existing_user = self.db.get_user(user_id)
        
        if not existing_user:
            # Запрашиваем ФИО
            self.user_states[user_id] = {'state': 'waiting_for_name'}
            await update.message.reply_text(
                "Добро пожаловать в систему электронного табеля выхода в город!\n\n"
                "Для регистрации введите ваше ФИО в формате:\n"
                "Фамилия И.О.\n\n"
                "Пример: Иванов И.И."
            )
            return
        
        # Пользователь уже зарегистрирован
        is_admin = self.db.is_admin(user_id)
        await self.show_main_menu(update, context, is_admin)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            await update.message.reply_text("Используйте кнопки меню для навигации.")
            return
        
        state = self.user_states[user_id]['state']
        
        if state == 'waiting_for_name':
            await self.handle_name_input(update, context)
        elif state == 'waiting_for_custom_location':
            await self.handle_custom_location(update, context)
        else:
            await update.message.reply_text("Используйте кнопки меню для навигации.")
    
    async def handle_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ФИО"""
        user = update.effective_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        full_name = update.message.text.strip()
        
        # Валидация формата ФИО
        if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', full_name):
            await update.message.reply_text(
                "Неверный формат ФИО!\n\n"
                "Правильный формат: Фамилия И.О.\n"
                "Пример: Иванов И.И.\n\n"
                "Попробуйте еще раз:"
            )
            return
        
        # Сохраняем пользователя
        if self.db.add_user(user_id, username, full_name):
            del self.user_states[user_id]
            is_admin = self.db.is_admin(user_id)
            await update.message.reply_text(
                f"Регистрация успешно завершена!\n"
                f"Добро пожаловать, {full_name}!"
            )
            await self.show_main_menu(update, context, is_admin)
        else:
            await update.message.reply_text(
                "Ошибка при регистрации. Попробуйте еще раз или обратитесь к администратору."
            )
    
    async def handle_custom_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода кастомной локации"""
        user_id = update.effective_user.id
        custom_location = update.message.text.strip()
        
        if len(custom_location) < 3 or len(custom_location) > 50:
            await update.message.reply_text(
                "Название локации должно быть от 3 до 50 символов.\n"
                "Попробуйте еще раз:"
            )
            return
        
        # Получаем сохраненные данные
        state_data = self.user_states[user_id]
        action = state_data['action']
        
        # Добавляем запись
        if self.db.add_record(user_id, action, custom_location):
            del self.user_states[user_id]
            
            action_text = "убыл" if action == "убыл" else "прибыл"
            await update.message.reply_text(
                f"✅ Запись добавлена!\n"
                f"Действие: {action_text}\n"
                f"Локация: {custom_location}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            # Уведомляем главного админа
            if MAIN_ADMIN_ID:
                user = self.db.get_user(user_id)
                await context.bot.send_message(
                    MAIN_ADMIN_ID,
                    f"🔔 Новая запись:\n"
                    f"Боец: {user['full_name']}\n"
                    f"Действие: {action_text}\n"
                    f"Локация: {custom_location}"
                )
            
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin)
        else:
            await update.message.reply_text(
                "Ошибка при добавлении записи. Попробуйте еще раз."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback'ов"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # Проверяем регистрацию
        user = self.db.get_user(user_id)
        if not user:
            await query.edit_message_text(
                "Пожалуйста, сначала зарегистрируйтесь с помощью /start"
            )
            return
        
        is_admin = self.db.is_admin(user_id)
        is_main_admin = self.db.is_main_admin(user_id)
        
        if data == "main_menu":
            await self.show_main_menu(update, context, is_admin, query)
        
        elif data.startswith("action_"):
            await self.handle_action_selection(update, context, query, data)
        
        elif data.startswith("location_"):
            await self.handle_location_selection(update, context, query, data)
        
        elif data == "show_journal":
            await self.show_journal(update, context, query)
        
        elif data.startswith("journal_"):
            await self.handle_journal_expansion(update, context, query, data)
        
        elif data == "admin_panel":
            await self.show_admin_panel(update, context, query, is_main_admin)
        
        elif data.startswith("admin_"):
            await self.handle_admin_actions(update, context, query, data, is_main_admin)
        
        elif data == "cancel":
            await self.show_main_menu(update, context, is_admin, query)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           is_admin: bool, query=None):
        """Показать главное меню"""
        keyboard = get_main_menu_keyboard(is_admin)
        text = "🎖️ Электронный табель выхода в город\n\nВыберите действие:"
        
        if query:
            await query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    
    async def handle_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    query, data: str):
        """Обработка выбора действия (убыл/прибыл)"""
        action = "убыл" if "leave" in data else "прибыл"
        keyboard = get_location_keyboard(action)
        
        action_text = "убыл" if action == "убыл" else "прибыл"
        text = f"Выберите локацию для отметки о том, что вы {action_text}:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def handle_location_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      query, data: str):
        """Обработка выбора локации"""
        parts = data.split("_", 2)
        action = parts[1]
        location = parts[2]
        
        user_id = update.effective_user.id
        
        if location == "📝 Другое":
            # Запрашиваем кастомную локацию
            self.user_states[user_id] = {
                'state': 'waiting_for_custom_location',
                'action': action
            }
            
            await query.edit_message_text(
                "Введите название локации:\n\n"
                "Примеры:\n"
                "• Дом родителей\n"
                "• Торговый центр\n"
                "• Кафе\n"
                "• Другое место\n\n"
                "Введите название:"
            )
            return
        
        # Добавляем запись
        if self.db.add_record(user_id, action, location):
            action_text = "убыл" if action == "убыл" else "прибыл"
            await query.edit_message_text(
                f"✅ Запись добавлена!\n"
                f"Действие: {action_text}\n"
                f"Локация: {location}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            # Уведомляем главного админа
            if MAIN_ADMIN_ID:
                user = self.db.get_user(user_id)
                await context.bot.send_message(
                    MAIN_ADMIN_ID,
                    f"🔔 Новая запись:\n"
                    f"Боец: {user['full_name']}\n"
                    f"Действие: {action_text}\n"
                    f"Локация: {location}"
                )
            
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin, query)
        else:
            await query.edit_message_text(
                "Ошибка при добавлении записи. Попробуйте еще раз.",
                reply_markup=get_back_keyboard()
            )
    
    async def show_journal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать журнал пользователя"""
        user_id = update.effective_user.id
        records = self.db.get_user_records(user_id, 3)
        
        if not records:
            text = "📋 Ваш журнал пуст.\nУ вас пока нет записей о выходе и приходе."
        else:
            text = "📋 Ваш журнал (последние 3 записи):\n\n"
            for record in records:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m.%Y %H:%M')
                action_emoji = "🚶" if record['action'] == "убыл" else "🏠"
                text += f"{action_emoji} {record['action'].title()} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"
        
        keyboard = get_journal_keyboard(expanded=False)
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def handle_journal_expansion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     query, data: str):
        """Обработка разворачивания/сворачивания журнала"""
        user_id = update.effective_user.id
        expanded = "expand" in data
        
        limit = 10 if expanded else 3
        records = self.db.get_user_records(user_id, limit)
        
        if not records:
            text = "📋 Ваш журнал пуст.\nУ вас пока нет записей о выходе и приходе."
        else:
            text = f"📋 Ваш журнал (последние {len(records)} записей):\n\n"
            for record in records:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m.%Y %H:%M')
                action_emoji = "🚶" if record['action'] == "убыл" else "🏠"
                text += f"{action_emoji} {record['action'].title()} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"
        
        keyboard = get_journal_keyboard(expanded=expanded)
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             query, is_main_admin: bool):
        """Показать панель администратора"""
        keyboard = get_admin_panel_keyboard(is_main_admin)
        text = "⚙️ Панель администратора\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def handle_admin_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 query, data: str, is_main_admin: bool):
        """Обработка админских действий"""
        if data == "admin_stats":
            await self.show_admin_statistics(update, context, query)
        elif data == "admin_records":
            await self.show_admin_records(update, context, query)
        elif data == "admin_export":
            await self.export_admin_data(update, context, query)
        elif data == "admin_manage" and is_main_admin:
            await self.show_admin_management(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("admin_panel")
            )
    
    async def show_admin_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать статистику для админа"""
        stats = self.db.get_statistics(30)
        
        text = "📊 Статистика за последние 30 дней:\n\n"
        text += f"📈 Всего записей: {stats['total_records']}\n"
        text += f"👥 Активных пользователей: {stats['active_users']}\n\n"
        
        text += "📊 По действиям:\n"
        for action, count in stats['action_stats'].items():
            emoji = "🚶" if action == "убыл" else "🏠"
            text += f"{emoji} {action}: {count}\n"
        
        text += "\n🏆 Топ локаций:\n"
        for i, (location, count) in enumerate(list(stats['location_stats'].items())[:5], 1):
            text += f"{i}. {location}: {count}\n"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_panel"))
    
    async def show_admin_records(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать все записи для админа"""
        records = self.db.get_all_records(7)  # За последнюю неделю
        
        if not records:
            text = "📋 Записей за последнюю неделю не найдено."
        else:
            text = "📋 Все записи за последнюю неделю:\n\n"
            for record in records[:10]:  # Показываем только первые 10
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m.%Y %H:%M')
                action_emoji = "🚶" if record['action'] == "убыл" else "🏠"
                text += f"👤 {record['full_name']}\n"
                text += f"{action_emoji} {record['action']} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"
            
            if len(records) > 10:
                text += f"... и еще {len(records) - 10} записей"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_panel"))
    
    async def export_admin_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Экспорт данных для админа"""
        try:
            filename = self.db.export_to_excel(30)
            if filename:
                with open(filename, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=file,
                        caption="📤 Экспорт данных за последние 30 дней"
                    )
                await query.edit_message_text(
                    "✅ Данные успешно экспортированы!",
                    reply_markup=get_back_keyboard("admin_panel")
                )
            else:
                await query.edit_message_text(
                    "❌ Нет данных для экспорта.",
                    reply_markup=get_back_keyboard("admin_panel")
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка при экспорте: {str(e)}",
                reply_markup=get_back_keyboard("admin_panel")
            )
    
    async def show_admin_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать управление админами"""
        keyboard = get_admin_management_keyboard()
        text = "👥 Управление администраторами\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Добавление нового админа"""
        text = ("➕ Добавление администратора\n\n"
                "Для добавления нового админа:\n"
                "1. Попросите пользователя отправить боту /start\n"
                "2. Введите его Telegram ID\n\n"
                "Введите ID пользователя:")
        
        user_id = update.effective_user.id
        self.user_states[user_id] = {'state': 'waiting_for_admin_id'}
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_manage"))
    
    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Удаление админа"""
        # Получаем список всех админов
        admins = self.db.get_all_admins()
        
        if not admins:
            text = "❌ Администраторы не найдены."
            await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_manage"))
            return
        
        text = "➖ Удаление администратора\n\nВыберите админа для удаления:\n\n"
        keyboard = []
        
        for admin in admins:
            if admin['id'] != MAIN_ADMIN_ID:  # Не показываем главного админа
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {admin['full_name']} (@{admin['username']})",
                        callback_data=f"remove_admin_{admin['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_manage")])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))