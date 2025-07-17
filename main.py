
import asyncio
import logging
from datetime import datetime
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from services.db_service import DatabaseService
from config import BOT_TOKEN, MAIN_ADMIN_ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class BotHandler:
    def __init__(self, db_service):
        self.db = db_service
        self.user_states = {}

    async def start(self, update, context):
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
                "🎖️ Добро пожаловать в систему электронного табеля!\n\n"
                "Для регистрации введите ваше ФИО в формате:\n"
                "Фамилия И.О.\n\n"
                "Пример: Иванов И.И."
            )
            return
        
        # Пользователь уже зарегистрирован
        await self.show_main_menu(update, context)

    async def handle_message(self, update, context):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if user_id in self.user_states:
            state = self.user_states[user_id].get('state')
            
            if state == 'waiting_for_name':
                await self.handle_name_input(update, context, text)
            elif state == 'waiting_for_custom_location':
                await self.handle_custom_location(update, context, text)
        else:
            await update.message.reply_text(
                "Используйте кнопки меню для навигации."
            )

    async def handle_name_input(self, update, context, full_name):
        """Обработка ввода ФИО"""
        import re
        user = update.effective_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        
        # Валидация формата ФИО
        if not re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$', full_name):
            await update.message.reply_text(
                "❌ Неверный формат ФИО!\n\n"
                "Правильный формат: Фамилия И.О.\n"
                "Пример: Иванов И.И.\n\n"
                "Попробуйте еще раз:"
            )
            return
        
        # Сохраняем пользователя
        if self.db.add_user(user_id, username, full_name):
            del self.user_states[user_id]
            await update.message.reply_text(
                f"✅ Регистрация успешно завершена!\n"
                f"👤 Добро пожаловать, {full_name}!"
            )
            await self.show_main_menu(update, context)
        else:
            await update.message.reply_text(
                "❌ Ошибка при регистрации. Попробуйте еще раз."
            )

    async def handle_custom_location(self, update, context, location):
        """Обработка ввода кастомной локации"""
        user_id = update.effective_user.id
        
        if len(location) < 3 or len(location) > 50:
            await update.message.reply_text(
                "Название локации должно быть от 3 до 50 символов.\nПопробуйте еще раз:"
            )
            return
        
        state_data = self.user_states[user_id]
        action = state_data['action']
        
        if self.db.add_record(user_id, action, location):
            del self.user_states[user_id]
            
            action_text = "убыл" if action == "убыл" else "прибыл"
            await update.message.reply_text(
                f"✅ Запись добавлена!\n"
                f"Действие: {action_text}\n"
                f"Локация: {location}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            await self.show_main_menu(update, context)
        else:
            await update.message.reply_text("❌ Ошибка при добавлении записи.")

    async def handle_callback(self, update, context):
        """Обработчик callback'ов"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        if data.startswith("action_"):
            await self.handle_action_selection(update, context, query, data)
        elif data.startswith("location_"):
            await self.handle_location_selection(update, context, query, data)
        elif data == "show_journal":
            await self.show_journal(update, context, query)
        elif data == "main_menu":
            await self.show_main_menu(update, context, query)

    async def handle_action_selection(self, update, context, query, data):
        """Обработка выбора действия"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        action = "убыл" if "leave" in data else "прибыл"
        
        locations = [
            "🏥 Поликлиника", "⚓ ОБРМП", "🌆 Калининград", 
            "🛒 Магазин", "🍲 Столовая", "🏨 Госпиталь",
            "⚙️ Рабочка", "🩺 ВВК", "🏛️ МФЦ", "🚓 Патруль"
        ]
        
        keyboard = []
        for i in range(0, len(locations), 2):
            row = []
            for j in range(i, min(i+2, len(locations))):
                location = locations[j]
                row.append(InlineKeyboardButton(
                    location, 
                    callback_data=f"location_{action}_{location}"
                ))
            keyboard.append(row)
        
        # Кнопка "Другое"
        keyboard.append([InlineKeyboardButton(
            "📝 Другое", 
            callback_data=f"location_{action}_custom"
        )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
        
        action_text = "убыли" if action == "убыл" else "прибыли"
        await query.edit_message_text(
            f"Выберите локацию для отметки о том, что вы {action_text}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_location_selection(self, update, context, query, data):
        """Обработка выбора локации"""
        parts = data.split("_", 2)
        action = parts[1]
        location = parts[2]
        
        user_id = update.effective_user.id
        
        if location == "custom":
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
                "• Кафе\n\n"
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
            
            # Показываем главное меню через 2 секунды
            await asyncio.sleep(2)
            await self.show_main_menu(update, context, query)
        else:
            await query.edit_message_text("❌ Ошибка при добавлении записи.")

    async def show_main_menu(self, update, context, query=None):
        """Показать главное меню"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("🚶 Убыл", callback_data="action_leave"),
                InlineKeyboardButton("🏠 Прибыл", callback_data="action_arrive")
            ],
            [InlineKeyboardButton("📋 Мой журнал", callback_data="show_journal")]
        ]
        
        # Проверяем права админа
        user_id = update.effective_user.id
        if self.db.is_admin(user_id) or user_id == MAIN_ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
        
        text = "🎖️ Электронный табель выхода в город\n\nВыберите действие:"
        
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_journal(self, update, context, query):
        """Показать журнал пользователя"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from datetime import datetime
        
        user_id = update.effective_user.id
        records = self.db.get_user_records(user_id, 5)
        
        if not records:
            text = "📋 Ваш журнал пуст.\nУ вас пока нет записей."
        else:
            text = "📋 Ваш журнал (последние 5 записей):\n\n"
            for record in records:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%d.%m %H:%M')
                action_emoji = "🚶" if record['action'] == "убыл" else "🏠"
                text += f"{action_emoji} {record['action']} - {record['location']}\n"
                text += f"⏰ {formatted_time}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main():
    """Основная функция для запуска бота"""
    try:
        # Инициализация базы данных
        db = DatabaseService()

        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()

        # Удаляем меню команд
        await application.bot.delete_my_commands()
        await application.bot.set_my_commands([])

        # Инициализация хэндлера
        bot_handler = BotHandler(db)

        # Регистрация хэндлеров
        application.add_handler(CommandHandler("start", bot_handler.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_message))
        application.add_handler(CallbackQueryHandler(bot_handler.handle_callback))

        # Запуск бота
        print("🤖 Бот запущен и готов к работе...")
        await application.run_polling()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())
