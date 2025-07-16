import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import Handlers
from database import Database
from telegram import Update
import time
from datetime import datetime, timedelta
import json, os
from random_phrases import get_random_phrase

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
    db = Database()
    def get_times():
        fname = 'notification_times.json'
        times = {"soldiers": "18:40", "admins": "19:00"}
        if os.path.exists(fname):
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    times = json.load(f)
            except Exception:
                pass
        return times
    while True:
        times = get_times()
        soldiers_time = times.get('soldiers', '18:40')
        admins_time = times.get('admins', '19:00')
        from datetime import datetime, timedelta
        now = datetime.now()
        # Следующее срабатывание для бойцов
        h_s, m_s = map(int, soldiers_time.split(':'))
        next_soldiers = now.replace(hour=h_s, minute=m_s, second=0, microsecond=0)
        if now >= next_soldiers:
            next_soldiers += timedelta(days=1)
        # Следующее срабатывание для админов
        h_a, m_a = map(int, admins_time.split(':'))
        next_admins = now.replace(hour=h_a, minute=m_a, second=0, microsecond=0)
        if now >= next_admins:
            next_admins += timedelta(days=1)
        # Ждём до ближайшего события
        sleep_seconds = min((next_soldiers - now).total_seconds(), (next_admins - now).total_seconds())
        await asyncio.sleep(sleep_seconds)
        now = datetime.now()
        # Проверяем, что сейчас время для бойцов
        if now.hour == h_s and now.minute == m_s:
            soldiers = db.get_soldiers_by_status('вне_части')
            for user in soldiers:
                try:
                    await application.bot.send_message(
                        user['id'],
                        get_random_phrase(),
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания бойцу {user['id']}: {e}")
        # Проверяем, что сейчас время для админов
        if now.hour == h_a and now.minute == m_a:
            admins = db.get_all_admins()
            all_soldiers, _, _ = db.get_users_list(page=1, per_page=10000)
            all_soldiers = sorted(all_soldiers, key=lambda u: u['full_name'])
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
            summary = "📋 Сводка по бойцам:\n\n"
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