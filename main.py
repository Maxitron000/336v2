
import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from handlers import user, admin, stats, notifications
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from services.db_service import DBService

# Настройка красивого логгера
class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для логов"""
    
    # ANSI цвета
    COLORS = {
        'DEBUG': '\033[36m',    # Голубой
        'INFO': '\033[32m',     # Зеленый
        'WARNING': '\033[33m',  # Желтый
        'ERROR': '\033[31m',    # Красный
        'CRITICAL': '\033[35m', # Фиолетовый
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Добавляем цвет к уровню лога
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

# Настройка логгера
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создаем обработчик для консоли
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Создаем красивый формат
formatter = ColoredFormatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(formatter)

# Добавляем обработчик
logger.addHandler(console_handler)

# Отключаем дублирование логов aiogram
logging.getLogger('aiogram').setLevel(logging.WARNING)

def print_banner():
    """Красивый баннер запуска"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🎖️  ЭЛЕКТРОННЫЙ ТАБЕЛЬ ВЫХОДА В ГОРОД  🎖️                     ║
║                                                                  ║
║    📍 336 инженерно-маскировочный батальон                       ║
║    🤖 Telegram Bot v2.0                                          ║
║    ⚡ Powered by aiogram 3.x                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def init_database():
    """Инициализация базы данных"""
    try:
        print("🔧 Инициализация базы данных...")
        
        # Создание таблиц если их нет
        import aiosqlite
        from config import DB_NAME
        
        async with aiosqlite.connect(DB_NAME) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица записей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    comment TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            await db.commit()
            logging.info("✅ База данных успешно инициализирована")
            
            # Проверяем количество пользователей
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            user_count = (await cursor.fetchone())[0]
            logging.info(f"👥 Зарегистрировано пользователей: {user_count}")
            
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации БД: {e}")

async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск/регистрация"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="admin", description="Админ-панель"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="export", description="Экспорт в Excel"),
        BotCommand(command="help", description="Справка")
    ]
    await bot.set_my_commands(commands)

async def main():
    # Показываем красивый баннер
    print_banner()
    
    # Проверяем токен
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не найден в переменных окружения!")
        logging.error("💡 Проверьте файл .env")
        return
    
    logging.info("🔑 Токен бота найден")
    
    try:
        # Создаем бота
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        logging.info("🤖 Создан экземпляр бота")
        
        # Инициализация БД
        await init_database()
        
        # Подключение роутеров
        logging.info("📡 Подключение обработчиков...")
        dp.include_router(user.router)
        dp.include_router(admin.router)
        dp.include_router(stats.router)
        dp.include_router(notifications.router)
        logging.info("✅ Обработчики подключены")

        # Настройка планировщика
        logging.info("⏰ Настройка планировщика...")
        scheduler = AsyncIOScheduler()
        from handlers.notifications import setup_scheduler
        setup_scheduler(bot)
        logging.info("✅ Планировщик настроен")

        # Настройка команд
        await on_startup(bot)
        
        # Финальное сообщение
        logging.info("🚀 Бот успешно запущен и готов к работе!")
        logging.info("📱 Начинается polling обновлений...")
        
        print("=" * 70)
        print(f"🟢 СИСТЕМА ЗАПУЩЕНА | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Запуск polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logging.error(f"💥 Критическая ошибка запуска: {e}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("🔴 ПОЛУЧЕН СИГНАЛ ОСТАНОВКИ")
        print("⏹️  Бот остановлен пользователем")
        print("=" * 70)
    except Exception as e:
        logging.error(f"💥 Необработанная ошибка: {e}")
        print("\n" + "=" * 70)
        print("🔴 КРИТИЧЕСКАЯ ОШИБКА")
        print(f"💥 {e}")
        print("=" * 70)
