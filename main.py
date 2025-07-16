import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import Handlers
from database import Database
from telegram import Update
import time
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def cleanup_old_records():
    """Очистка старых записей каждые 24 часа"""
    db = Database()
    while True:
        try:
            deleted_count = db.cleanup_old_records(6)  # 6 месяцев
            if deleted_count > 0:
                logger.info(f"Очищено {deleted_count} старых записей")
            await asyncio.sleep(86400)  # 24 часа
        except Exception as e:
            logger.error(f"Ошибка при очистке записей: {e}")
            await asyncio.sleep(3600)  # 1 час при ошибке

async def send_reminders(application):
    """Фоновая задача для отправки напоминаний"""
    from database import Database
    db = Database()
    while True:
        now = datetime.now()
        # Следующее срабатывание в 18:40
        next_1840 = now.replace(hour=18, minute=40, second=0, microsecond=0)
        if now >= next_1840:
            next_1840 += timedelta(days=1)
        # Следующее срабатывание в 19:00
        next_1900 = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if now >= next_1900:
            next_1900 += timedelta(days=1)
        # Ждём до ближайшего события
        sleep_seconds = min((next_1840 - now).total_seconds(), (next_1900 - now).total_seconds())
        await asyncio.sleep(sleep_seconds)
        now = datetime.now()
        if now.hour == 18 and now.minute == 40:
            # Напоминания бойцам
            soldiers = db.get_soldiers_by_status('вне_части')
            for user in soldiers:
                try:
                    await application.bot.send_message(
                        user['id'],
                        "⏰ Напоминание! Не забудьте отметить приход в часть."
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания бойцу {user['id']}: {e}")
        if now.hour == 19 and now.minute == 0:
            # Сводка для админов
            admins = db.get_all_admins()
            all_soldiers, _, _ = db.get_users_list(page=1, per_page=10000)
            from datetime import datetime
            out_list = []
            in_list = []
            for user in all_soldiers:
                location = user['last_location'] or "-"
                try:
                    time_str = datetime.fromisoformat(user['last_status_change']).strftime('%H:%M') if user['last_status_change'] else "--:--"
                except Exception:
                    time_str = "--:--"
                line = f"{user['full_name']} — {location} ({time_str})"
                if user['status'] == 'вне_части':
                    out_list.append(line)
                else:
                    in_list.append(line)
            summary = "📋 Сводка по бойцам на 19:00:\n\n"
            summary += "🚶 ВНЕ ЧАСТИ:\n" + ("\n".join(out_list) if out_list else "—") + "\n\n"
            summary += "🏠 В ЧАСТИ:\n" + ("\n".join(in_list) if in_list else "—")
            for admin in admins:
                try:
                    await application.bot.send_message(
                        admin['id'],
                        summary
                    )
                except Exception as e:
                    print(f"Ошибка отправки сводки админу {admin['id']}: {e}")

async def main():
    """Основная функция запуска бота"""
    # Создаем экземпляр обработчиков
    handlers = Handlers()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    
    # Запускаем очистку старых записей в фоне
    asyncio.create_task(cleanup_old_records())
    # Запускаем фоновую задачу напоминаний
    asyncio.create_task(send_reminders(application))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())