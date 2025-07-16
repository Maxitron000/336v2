import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import Handlers
from database import Database
from telegram import Update

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
    
    # Запускаем бота
    logger.info("Бот запущен!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())