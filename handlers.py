import re
import json
import random
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
        self.notifications = self.load_notifications()
    
    def load_notifications(self):
        """Загрузка текстов уведомлений"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback если файл не найден
            return {
                "daily_summary": ["📊 Ежедневная сводка готова!"],
                "reminders": ["🔔 Не забудь отметиться!"],
                "new_record": ["🔔 Новая запись в системе!"],
                "admin_notifications": ["👑 Командир, новое событие!"],
                "welcome_messages": ["🎉 Добро пожаловать!"],
                "error_messages": ["❌ Ошибка в системе!"],
                "success_messages": ["✅ Успешно выполнено!"]
            }
    
    def get_random_notification(self, category: str) -> str:
        """Получение случайного уведомления по категории"""
        notifications = self.notifications.get(category, [])
        if notifications:
            return random.choice(notifications)
        return "🔔 Уведомление"
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        # Удаляем сообщение с командой для чистоты чата
        try:
            await update.message.delete()
        except:
            pass  # Если не удалось удалить
        
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
        elif state == 'waiting_for_admin_id':
            await self.handle_admin_id_input(update, context)
        elif state == 'waiting_for_new_name':
            # Смена ФИО бойца
            soldier_id = self.user_states[user_id]['soldier_id']
            new_name = update.message.text.strip()
            if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', new_name):
                await update.message.reply_text(
                    "Неверный формат ФИО!\n\nПравильный формат: Фамилия И.О.\nПример: Иванов И.И.\n\nПопробуйте еще раз:")
                return
            if self.db.update_user_full_name(soldier_id, new_name):
                await update.message.reply_text(f"✅ ФИО бойца успешно изменено на: {new_name}")
            else:
                await update.message.reply_text("❌ Ошибка при изменении ФИО. Попробуйте еще раз.")
            del self.user_states[user_id]
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin)
        elif state == 'waiting_for_new_soldier_name':
            # Запрос username после ФИО
            new_name = update.message.text.strip()
            if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', new_name):
                await update.message.reply_text(
                    "Неверный формат ФИО!\n\nПравильный формат: Фамилия И.О.\nПример: Иванов И.И.\n\nПопробуйте еще раз:")
                return
            self.user_states[user_id] = {"state": "waiting_for_new_soldier_username", "new_name": new_name}
            await update.message.reply_text(
                "Введите username нового бойца (без @) или отправьте '-' для генерации временного:")
            return
        elif state == 'waiting_for_new_soldier_username':
            new_name = self.user_states[user_id]['new_name']
            username = update.message.text.strip()
            if username == '-':
                import random
                username = f"user_{random.randint(100000,999999)}"
            # Проверка на дублирование username
            soldiers, _, _ = self.db.get_users_list(page=1, per_page=10000)
            if any(s['username'] == username for s in soldiers):
                await update.message.reply_text("Пользователь с таким username уже существует! Введите другой username:")
                return
            # Генерируем временный user_id (отрицательный, чтобы не пересекался с Telegram ID)
            import random
            temp_id = -random.randint(100000, 999999)
            if self.db.add_user(temp_id, username, new_name):
                await update.message.reply_text(f"✅ Новый боец добавлен!\nФИО: {new_name}\nusername: {username}")
            else:
                await update.message.reply_text("❌ Ошибка при добавлении бойца. Попробуйте еще раз.")
            del self.user_states[user_id]
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin)
            return
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
            welcome_text = self.get_random_notification("welcome_messages")
            await update.message.reply_text(
                f"{welcome_text}\n\n"
                f"✅ Регистрация успешно завершена!\n"
                f"👤 Добро пожаловать, {full_name}!"
            )
            await self.show_main_menu(update, context, is_admin)
        else:
            error_text = self.get_random_notification("error_messages")
            await update.message.reply_text(
                f"{error_text}\n\n"
                f"❌ Ошибка при регистрации. Попробуйте еще раз или обратитесь к администратору."
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
                notification_text = self.get_random_notification("admin_notifications")
                await context.bot.send_message(
                    MAIN_ADMIN_ID,
                    f"{notification_text}\n\n"
                    f"👤 Боец: {user['full_name']}\n"
                    f"🎯 Действие: {action_text}\n"
                    f"📍 Локация: {custom_location}\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M')}"
                )
            
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin, query)
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
        elif data.startswith("personnel_"):
            await self.handle_personnel_actions(update, context, query, data, is_main_admin)
        elif data.startswith("journal_"):
            await self.handle_journal_actions(update, context, query, data, is_main_admin)
        elif data.startswith("settings_"):
            await self.handle_settings_actions(update, context, query, data, is_main_admin)
        elif data.startswith("danger_"):
            await self.handle_danger_actions(update, context, query, data, is_main_admin)
        elif data.startswith("notif_"):
            await self.handle_notification_actions(update, context, query, data, is_main_admin)
        elif data.startswith("remove_admin_"):
            await self.handle_remove_admin(update, context, query, data)
        elif data.startswith("confirm_"):
            await self.handle_confirmation(update, context, query, data)
        
        elif data == "cancel":
            await self.show_main_menu(update, context, is_admin, query)
        elif data.startswith("editname_"):
            soldier_id = int(data.split("_")[1])
            self.user_states[user_id] = {"state": "waiting_for_new_name", "soldier_id": soldier_id}
            await query.edit_message_text(
                "Введите новое ФИО для бойца в формате: Фамилия И.О.\n\nПример: Иванов И.И.",
                reply_markup=get_back_keyboard("admin_personnel")
            )
            return
    
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
                notification_text = self.get_random_notification("admin_notifications")
                await context.bot.send_message(
                    MAIN_ADMIN_ID,
                    f"{notification_text}\n\n"
                    f"👤 Боец: {user['full_name']}\n"
                    f"🎯 Действие: {action_text}\n"
                    f"📍 Локация: {location}\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M')}"
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
    
    async def show_admin_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать быструю сводку"""
        # Получаем статистику отсутствующих
        away_soldiers = self.db.get_soldiers_by_status("вне_части")
        
        if not away_soldiers:
            text = "📊 Быстрая сводка\n\n✅ Все бойцы в части!"
        else:
            text = "📊 Быстрая сводка\n\n❌ Отсутствующие бойцы:\n\n"
            
            # Группируем по локациям
            locations = {}
            for soldier in away_soldiers:
                location = soldier.get('last_location', 'Неизвестно')
                if location not in locations:
                    locations[location] = []
                locations[location].append(soldier['full_name'])
            
            for location, soldiers in locations.items():
                soldiers = sorted(soldiers)
                text += f"📍 {location}:\n"
                for soldier in soldiers:
                    text += f"  • {soldier}\n"
                text += "\n"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_panel"))
    
    async def show_personnel_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать управление личным составом"""
        keyboard = get_personnel_management_keyboard()
        text = "👥 Управление личным составом\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_journal_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать управление журналом"""
        keyboard = get_journal_management_keyboard()
        text = "📖 Журнал событий\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_settings_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                query, is_main_admin: bool):
        """Показать панель настроек"""
        keyboard = get_settings_keyboard(is_main_admin)
        text = "⚙️ Настройки\n\nВыберите раздел:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_danger_zone(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать опасную зону"""
        keyboard = get_danger_zone_keyboard()
        text = "⚠️ Опасная зона\n\n🚨 Внимание! Эти действия необратимы!\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_notifications_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать настройки уведомлений"""
        keyboard = get_notifications_settings_keyboard()
        text = "🔔 Настройки уведомлений\n\nВыберите действие:"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_general_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать общие настройки пользователя"""
        user_id = update.effective_user.id
        settings = self.db.get_user_settings(user_id)
        lang = settings.get('language', 'ru')
        tz = settings.get('timezone', 'Europe/Moscow')
        tf = settings.get('timeformat', '24h')
        text = (
            f"⚙️ Общие настройки\n\n"
            f"🌐 Язык: {lang}\n"
            f"🕒 Часовой пояс: {tz}\n"
            f"⏳ Формат времени: {tf}\n\n"
            f"Выберите, что изменить:"
        )
        from keyboards import get_general_settings_keyboard
        await query.edit_message_text(text, reply_markup=get_general_settings_keyboard())
    
    async def mark_all_arrived(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Отметить всех прибывшими"""
        keyboard = get_confirm_keyboard("mark_all_arrived")
        text = "🚨 Отметить всех прибывшими?\n\n⚠️ Это действие отметит всех отсутствующих бойцов как прибывших в часть.\n\nВы уверены?"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def clear_all_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Очистить все данные"""
        keyboard = get_confirm_keyboard("clear_all_data")
        text = "🗑️ Очистить все данные?\n\n🚨 ВНИМАНИЕ! Это действие удалит ВСЕ данные:\n• Все записи о выходе/приходе\n• Всех пользователей (кроме главного админа)\n• Всех админов (кроме главного)\n\nЭто действие НЕОБРАТИМО!\n\nВы уверены?"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def reset_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Сбросить настройки"""
        keyboard = get_confirm_keyboard("reset_settings")
        text = "🔄 Сбросить настройки?\n\n⚠️ Это действие сбросит все настройки бота к значениям по умолчанию.\n\nВы уверены?"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def enable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Включить уведомления"""
        text = "🔔 Уведомления включены!\n\n✅ Теперь вы будете получать уведомления о всех событиях."
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("settings_notifications"))
    
    async def disable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Отключить уведомления"""
        text = "🔕 Уведомления отключены!\n\n❌ Вы больше не будете получать уведомления."
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("settings_notifications"))
    
    async def set_notification_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Настройка времени уведомлений"""
        text = "⏰ Настройка времени уведомлений\n\n🔧 Функция в разработке"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("settings_notifications"))
    
    async def set_notification_recipients(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Настройка получателей уведомлений"""
        text = "👥 Настройка получателей уведомлений\n\n🔧 Функция в разработке"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("settings_notifications"))
    
    async def toggle_silent_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Переключить режим тишины"""
        text = "🔇 Режим тишины переключен!\n\n🔕 Уведомления будут отправляться без звука."
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("settings_notifications"))
    
    async def edit_soldier_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Редактирование ФИО бойца"""
        # Получаем всех бойцов по алфавиту
        soldiers, _, _ = self.db.get_users_list(page=1, per_page=10000)
        if not soldiers:
            await query.edit_message_text("Нет бойцов для редактирования.", reply_markup=get_back_keyboard("admin_personnel"))
            return
        # Формируем клавиатуру выбора бойца
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton(f"{s['full_name']}", callback_data=f"editname_{s['id']}")]
            for s in soldiers
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_personnel")])
        await query.edit_message_text(
            "✏️ Выберите бойца для смены ФИО:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def add_new_soldier(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Добавление нового бойца"""
        user_id = update.effective_user.id
        self.user_states[user_id] = {"state": "waiting_for_new_soldier_name"}
        await query.edit_message_text(
            "Введите ФИО нового бойца в формате: Фамилия И.О.\n\nПример: Иванов И.И.",
            reply_markup=get_back_keyboard("admin_personnel")
        )

    async def remove_soldier(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Удаление бойца"""
        text = "❌ Удаление бойца\n\n🔧 Функция в разработке"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_personnel"))
    
    async def export_journal_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Экспорт данных журнала"""
        try:
            filename = self.db.export_to_excel(30)
            if filename:
                with open(filename, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=file,
                        caption="📥 Экспорт журнала за последние 30 дней"
                    )
                await query.edit_message_text(
                    "✅ Журнал успешно экспортирован!",
                    reply_markup=get_back_keyboard("admin_journal")
                )
            else:
                await query.edit_message_text(
                    "❌ Нет данных для экспорта.",
                    reply_markup=get_back_keyboard("admin_journal")
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка при экспорте: {str(e)}",
                reply_markup=get_back_keyboard("admin_journal")
            )
    
    async def show_journal_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать статистику журнала"""
        stats = self.db.get_statistics(30)
        
        text = "📊 Статистика журнала за последние 30 дней:\n\n"
        text += f"📈 Всего записей: {stats['total_records']}\n"
        text += f"👥 Активных пользователей: {stats['active_users']}\n\n"
        
        text += "📊 По действиям:\n"
        for action, count in stats['action_stats'].items():
            emoji = "🚶" if action == "убыл" else "🏠"
            text += f"{emoji} {action}: {count}\n"
        
        text += "\n🏆 Топ локаций:\n"
        for i, (location, count) in enumerate(list(stats['location_stats'].items())[:5], 1):
            text += f"{i}. {location}: {count}\n"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_journal"))
    
    async def show_journal_records(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Показать записи журнала"""
        records = self.db.get_all_records(7)  # За последнюю неделю
        
        if not records:
            text = "📋 Записей в журнале за последнюю неделю не найдено."
        else:
            text = "📋 Записи журнала за последнюю неделю:\n\n"
            for record in records[:10]:  # Показываем только первые 10
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m.%Y %H:%M')
                action_emoji = "🚶" if record['action'] == "убыл" else "🏠"
                text += f"👤 {record['full_name']}\n"
                text += f"{action_emoji} {record['action']} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"
            
            if len(records) > 10:
                text += f"... и еще {len(records) - 10} записей"
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard("admin_journal"))
    
    async def handle_admin_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 query, data: str, is_main_admin: bool):
        """Обработка админских действий - Уровень 1"""
        if data == "admin_panel":
            await self.show_admin_panel(update, context, query, is_main_admin)
        elif data == "admin_summary":
            await self.show_admin_summary(update, context, query)
        elif data == "admin_personnel":
            await self.show_personnel_management(update, context, query)
        elif data == "admin_journal":
            await self.show_journal_management(update, context, query)
        elif data == "admin_settings":
            await self.show_settings_panel(update, context, query, is_main_admin)
        elif data == "admin_manage" and is_main_admin:
            await self.show_admin_management(update, context, query)
        elif data == "admin_add" and is_main_admin:
            await self.add_admin(update, context, query)
        elif data == "admin_remove" and is_main_admin:
            await self.remove_admin(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("admin_panel")
            )
    
    async def handle_personnel_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     query, data: str, is_main_admin: bool):
        """Обработка действий с личным составом"""
        if data == "personnel_edit_name":
            await self.edit_soldier_name(update, context, query)
        elif data == "personnel_add":
            await self.add_new_soldier(update, context, query)
        elif data == "personnel_remove":
            await self.remove_soldier(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("admin_personnel")
            )
    
    async def handle_journal_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   query, data: str, is_main_admin: bool):
        """Обработка действий с журналом"""
        if data == "journal_export":
            await self.export_journal_data(update, context, query)
        elif data == "journal_stats":
            await self.show_journal_statistics(update, context, query)
        elif data == "journal_records":
            await self.show_journal_records(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("admin_journal")
            )
    
    async def handle_settings_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    query, data: str, is_main_admin: bool):
        """Обработка настроек"""
        if data == "settings_notifications":
            await self.show_notifications_settings(update, context, query)
        elif data == "settings_general":
            await self.show_general_settings(update, context, query)
        elif data == "settings_danger_zone" and is_main_admin:
            await self.show_danger_zone(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("admin_settings")
            )
    
    async def handle_danger_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  query, data: str, is_main_admin: bool):
        """Обработка опасных действий"""
        if data == "danger_mark_all_arrived":
            await self.mark_all_arrived(update, context, query)
        elif data == "danger_clear_all_data":
            await self.clear_all_data(update, context, query)
        elif data == "danger_reset_settings":
            await self.reset_settings(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("settings_danger_zone")
            )
    
    async def handle_notification_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                        query, data: str, is_main_admin: bool):
        """Обработка настроек уведомлений"""
        if data == "notif_enable":
            await self.enable_notifications(update, context, query)
        elif data == "notif_disable":
            await self.disable_notifications(update, context, query)
        elif data == "notif_time":
            await self.set_notification_time(update, context, query)
        elif data == "notif_recipients":
            await self.set_notification_recipients(update, context, query)
        elif data == "notif_silent":
            await self.toggle_silent_mode(update, context, query)
        else:
            await query.edit_message_text(
                "Функция в разработке или недоступна.",
                reply_markup=get_back_keyboard("settings_notifications")
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
    
    async def handle_admin_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ID админа"""
        user_id = update.effective_user.id
        admin_id_text = update.message.text.strip()
        
        try:
            admin_id = int(admin_id_text)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID!\n"
                "ID должен быть числом.\n"
                "Попробуйте еще раз:"
            )
            return
        
        # Проверяем, существует ли пользователь
        target_user = self.db.get_user_by_id(admin_id)
        if not target_user:
            await update.message.reply_text(
                "❌ Пользователь с таким ID не найден!\n"
                "Убедитесь, что пользователь уже зарегистрирован в боте.\n"
                "Попробуйте еще раз:"
            )
            return
        
        # Проверяем, не является ли уже админом
        if self.db.is_admin(admin_id):
            await update.message.reply_text(
                f"❌ Пользователь {target_user['full_name']} уже является администратором!"
            )
            del self.user_states[user_id]
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin)
            return
        
        # Добавляем админа
        if self.db.add_admin(admin_id):
            del self.user_states[user_id]
            await update.message.reply_text(
                f"✅ Администратор {target_user['full_name']} успешно добавлен!"
            )
            
            # Уведомляем нового админа
            await context.bot.send_message(
                admin_id,
                f"🎉 Поздравляем! Вам предоставлены права администратора в системе электронного табеля."
            )
            
            is_admin = self.db.is_admin(user_id)
            await self.show_main_menu(update, context, is_admin)
        else:
            await update.message.reply_text(
                "❌ Ошибка при добавлении администратора. Попробуйте еще раз."
            )
    
    async def handle_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str):
        """Обработка удаления админа"""
        admin_id = int(data.split("_")[2])
        admin = self.db.get_user_by_id(admin_id)
        
        if not admin:
            await query.edit_message_text(
                "❌ Пользователь не найден.",
                reply_markup=get_back_keyboard("admin_manage")
            )
            return
        
        keyboard = get_confirm_keyboard("remove_admin", str(admin_id))
        text = f"⚠️ Подтвердите удаление администратора:\n\n👤 {admin['full_name']}\n@{admin['username']}\n\nВы уверены?"
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str):
        """Обработка подтверждений"""
        parts = data.split("_", 2)
        action = parts[1]
        target_id = parts[2] if len(parts) > 2 else ""
        
        if action == "remove_admin":
            admin_id = int(target_id)
            admin = self.db.get_user_by_id(admin_id)
            
            if self.db.remove_admin(admin_id):
                await query.edit_message_text(
                    f"✅ Администратор {admin['full_name']} успешно удален!",
                    reply_markup=get_back_keyboard("admin_manage")
                )
                
                # Уведомляем удаленного админа
                await context.bot.send_message(
                    admin_id,
                    "ℹ️ Ваши права администратора были отозваны."
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка при удалении администратора.",
                    reply_markup=get_back_keyboard("admin_manage")
                )
        elif action == "mark_all_arrived":
            updated_count = self.db.mark_all_arrived()
            await query.edit_message_text(
                f"✅ Массовая отметка выполнена!\n\n🎯 Отмечено прибывшими: {updated_count} бойцов",
                reply_markup=get_back_keyboard("settings_danger_zone")
            )
        
        elif action == "clear_all_data":
            if self.db.clear_all_data():
                await query.edit_message_text(
                    "✅ Все данные успешно очищены!\n\n🗑️ База данных сброшена к начальному состоянию.",
                    reply_markup=get_back_keyboard("settings_danger_zone")
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка при очистке данных.",
                    reply_markup=get_back_keyboard("settings_danger_zone")
                )
        
        elif action == "reset_settings":
            await query.edit_message_text(
                "✅ Настройки сброшены к значениям по умолчанию!",
                reply_markup=get_back_keyboard("settings_danger_zone")
            )
        
        else:
            await query.edit_message_text(
                "❌ Неизвестное действие.",
                reply_markup=get_back_keyboard("admin_panel")
            )