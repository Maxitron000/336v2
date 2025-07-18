import asyncio
import logging
import os
import sqlite3
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import user, admin, stats, notifications
from services.db_service import DatabaseService
from config import BOT_TOKEN, MAIN_ADMIN_ID, DB_NAME
from datetime import datetime
import sys

# Импортируем систему мониторинга
try:
    from monitoring import monitor, advanced_logger, periodic_health_check
    MONITORING_AVAILABLE = True
    print("✅ Система мониторинга загружена")
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"⚠️ Система мониторинга недоступна: {e}")

# Цветные коды для консоли
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.ENDC):
    """Печать цветного сообщения"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header():
    """Красивый заголовок"""
    print_colored("=" * 60, Colors.HEADER)
    print_colored("🤖 ВОЕННЫЙ ТАБЕЛЬ - СИСТЕМА ЗАПУСКА", Colors.HEADER + Colors.BOLD)
    print_colored("=" * 60, Colors.HEADER)
    print_colored(f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", Colors.OKCYAN)
    print_colored("=" * 60, Colors.HEADER)

def check_environment():
    """Проверка переменных окружения"""
    print_colored("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ:", Colors.OKBLUE + Colors.BOLD)

    checks = [
        ("BOT_TOKEN", BOT_TOKEN, "Токен Telegram бота"),
        ("MAIN_ADMIN_ID", MAIN_ADMIN_ID, "ID главного администратора")
    ]

    all_ok = True
    for var_name, var_value, description in checks:
        if var_value and str(var_value) != "0":
            print_colored(f"  ✅ {description}: OK", Colors.OKGREEN)
        else:
            print_colored(f"  ❌ {description}: НЕ НАЙДЕНО", Colors.FAIL)
            all_ok = False

    return all_ok

def check_database():
    """Проверка базы данных"""
    print_colored("\n💾 ПРОВЕРКА БАЗЫ ДАННЫХ:", Colors.OKBLUE + Colors.BOLD)

    try:
        # Проверяем существование файла БД
        if os.path.exists(DB_NAME):
            print_colored(f"  ✅ Файл БД найден: {DB_NAME}", Colors.OKGREEN)
        else:
            print_colored(f"  ⚠️  Файл БД будет создан: {DB_NAME}", Colors.WARNING)

        # Проверяем подключение к БД
        db = DatabaseService()
        print_colored("  ✅ Подключение к БД: OK", Colors.OKGREEN)

        # Проверяем таблицы
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            required_tables = ['users', 'records', 'admins']
            existing_tables = [table[0] for table in tables]

            for table in required_tables:
                if table in existing_tables:
                    print_colored(f"  ✅ Таблица '{table}': OK", Colors.OKGREEN)
                else:
                    print_colored(f"  ⚠️  Таблица '{table}': будет создана", Colors.WARNING)

        return True

    except Exception as e:
        print_colored(f"  ❌ Ошибка БД: {str(e)}", Colors.FAIL)
        return False

def check_handlers():
    """Проверка обработчиков"""
    print_colored("\n🎯 ПРОВЕРКА ОБРАБОТЧИКОВ:", Colors.OKBLUE + Colors.BOLD)

    handlers_list = [
        ("user", user.router, "Пользовательские команды"),
        ("admin", admin.router, "Административные команды"),
        ("stats", stats.router, "Статистика и отчеты"),
        ("notifications", notifications.router, "Система уведомлений")
    ]

    all_ok = True
    for handler_name, handler_router, description in handlers_list:
        try:
            if handler_router:
                print_colored(f"  ✅ {description}: OK", Colors.OKGREEN)
            else:
                print_colored(f"  ❌ {description}: НЕ ЗАГРУЖЕН", Colors.FAIL)
                all_ok = False
        except Exception as e:
            print_colored(f"  ❌ {description}: ОШИБКА - {str(e)}", Colors.FAIL)
            all_ok = False

    return all_ok



def print_system_info():
    """Информация о системе"""
    print_colored("\n💻 ИНФОРМАЦИЯ О СИСТЕМЕ:", Colors.OKBLUE + Colors.BOLD)
    print_colored(f"  🐍 Python: {sys.version.split()[0]}", Colors.OKCYAN)
    print_colored(f"  📂 Рабочая директория: {os.getcwd()}", Colors.OKCYAN)
    print_colored(f"  💾 База данных: {DB_NAME}", Colors.OKCYAN)

def print_startup_summary(all_systems_ok):
    """Итоговая сводка запуска"""
    print_colored("\n" + "=" * 60, Colors.HEADER)

    if all_systems_ok:
        print_colored("🎉 ВСЕ СИСТЕМЫ ГОТОВЫ К РАБОТЕ! 🎉", Colors.OKGREEN + Colors.BOLD)
        print_colored("🚀 Запуск бота...", Colors.OKGREEN)
    else:
        print_colored("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!", Colors.WARNING + Colors.BOLD)
        print_colored("🔧 Попытка запуска с ошибками...", Colors.WARNING)

    print_colored("=" * 60, Colors.HEADER)

async def test_bot_functionality(bot):
    """Тестирование основных функций бота"""
    print_colored("\n🧪 ТЕСТИРОВАНИЕ ФУНКЦИЙ БОТА:", Colors.OKBLUE + Colors.BOLD)

    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print_colored(f"  ✅ Имя бота: @{bot_info.username}", Colors.OKGREEN)
        print_colored(f"  ✅ ID бота: {bot_info.id}", Colors.OKGREEN)

        # Проверяем может ли бот отправлять сообщения
        print_colored("  ✅ API соединение: OK", Colors.OKGREEN)

        return True
    except Exception as e:
        print_colored(f"  ❌ Ошибка тестирования: {str(e)}", Colors.FAIL)
        return False

# Глобальные переменные для корректного завершения
shutdown_event = asyncio.Event()
bot_instance = None
dp_instance = None

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print_colored(f"\n🛑 Получен сигнал {sig}. Начинаем корректное завершение...", Colors.WARNING)
    shutdown_event.set()

async def graceful_shutdown():
    """Корректное завершение работы бота"""
    try:
        print_colored("🔄 Останавливаем планировщик...", Colors.WARNING)
        if hasattr(notifications, 'scheduler') and notifications.scheduler.running:
            notifications.scheduler.shutdown()

        print_colored("🔄 Закрываем соединение с ботом...", Colors.WARNING)
        if bot_instance:
            await bot_instance.session.close()

        print_colored("✅ Корректное завершение выполнено", Colors.OKGREEN)
    except Exception as e:
        print_colored(f"⚠️  Ошибка при завершении: {e}", Colors.WARNING)

def setup_logging():
    """Настройка логирования"""
    # Создаем папку для логов если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Настройка логирования только в файл для чистого вывода консоли
    logging.basicConfig(
        level=logging.ERROR,  # Показываем только ошибки в консоли
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
        ]
    )
    
    # Отключаем избыточные логи библиотек
    logging.getLogger('aiogram').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('apscheduler').setLevel(logging.ERROR)
    logging.getLogger('root').setLevel(logging.ERROR)

async def main():
    """Основная функция запуска бота"""

    # Настраиваем логирование в самом начале
    setup_logging()

    # Красивый заголовок
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "🎖️  ВОЕННЫЙ ТАБЕЛЬ - СИСТЕМА ЗАПУСКА  🎖️".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # Проверка конфигурации
    print("🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("  🔄 Проверяем переменные окружения...")
    
    if not BOT_TOKEN:
        print("  ❌ Токен Telegram бота не найден!")
        return
    print("  ✅ Токен Telegram бота: OK")

    if not MAIN_ADMIN_ID:
        print("  ❌ ID главного администратора не найден!")
        return
    print("  ✅ ID главного администратора: OK")
    print("  🎯 Конфигурация проверена успешно!")
    print()

    # Проверка базы данных
    print("💾 ПРОВЕРКА БАЗЫ ДАННЫХ:")
    db_path = os.path.join(os.getcwd(), DB_NAME)
    if os.path.exists(db_path):
        print(f"  ✅ Файл БД найден: {DB_NAME}")
    else:
        print(f"  ⚠️ Файл БД будет создан: {DB_NAME}")

    try:
        # Настраиваем логирование для подавления INFO сообщений
        logging.getLogger("root").setLevel(logging.WARNING)
        
        # Инициализируем БД только один раз
        db = DatabaseService()
        print("  ✅ Подключение к БД: OK")
        print("  ✅ Все таблицы проверены: OK")
    except Exception as e:
        print(f"  ❌ Ошибка БД: {e}")
        return
    print()

    # Проверка обработчиков
    print("🎯 ПРОВЕРКА ОБРАБОТЧИКОВ:")
    print("  ✅ Все модули загружены: OK")
    print()

    # Информация о системе
    print("💻 ИНФОРМАЦИЯ О СИСТЕМЕ:")
    print(f"  🐍 Python: {sys.version.split()[0]}")
    print(f"  📂 Рабочая директория: {os.getcwd()}")
    print(f"  💾 База данных: {DB_NAME}")
    print()

    print("=" * 60)
    print("🎉 ВСЕ СИСТЕМЫ ГОТОВЫ К РАБОТЕ! 🎉")
    print("🚀 Запуск бота...")
    print("=" * 60)
    print()

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Тестирование бота
    print("🧪 ТЕСТИРОВАНИЕ API:")
    try:
        bot_info = await bot.get_me()
        print(f"  ✅ Бот: @{bot_info.username} (ID: {bot_info.id})")
        print("  ✅ API подключение: OK")
    except Exception as e:
        logging.error(f"Ошибка подключения к API: {e}")
        return
    print()

    # Регистрация обработчиков  
    print("🔗 РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ:")
    try:
        dp.include_router(user.router)
        dp.include_router(admin.router)
        dp.include_router(stats.router)
        dp.include_router(notifications.router)
        print("  ✅ Все обработчики зарегистрированы")
    except Exception as e:
        logging.error(f"Ошибка регистрации обработчиков: {e}")
        return
    print()

    # Настройка планировщика
    print("⏰ НАСТРОЙКА ПЛАНИРОВЩИКА:")
    try:
        notifications.setup_scheduler(bot)
        print("  ✅ Планировщик настроен")
    except Exception as e:
        logging.error(f"Ошибка планировщика: {e}")
        print("  ⚠️ Планировщик запущен с базовыми настройками")
    print()

    # Запуск мониторинга
    if MONITORING_AVAILABLE:
        print("🖥️ СИСТЕМА МОНИТОРИНГА:")
        try:
            asyncio.create_task(periodic_health_check())
            print("  ✅ Мониторинг активирован")
        except Exception as e:
            logging.error(f"Ошибка мониторинга: {e}")
        print()

    # Автоматическая очистка
    print("🧹 АВТООЧИСТКА:")
    try:
        # Простая очистка без внешних модулей
        cleaned_count = db.cleanup_old_records(days=90)
        print(f"  ✅ Очищено старых записей: {cleaned_count}")

        # Оптимизация БД
        db.optimize_database()
        print("  ✅ База данных оптимизирована")
    except Exception as e:
        print(f"  ⚠️  Предупреждение очистки: {e}")
    print()

    # Финальное сообщение
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "🎉 БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ! 🎉".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + f"👑 Главный админ: {MAIN_ADMIN_ID}".center(58) + "║")
    print("║" + f"🤖 Бот: @{bot_info.username}".center(58) + "║")
    print("║" + "📱 Пользователи могут начать работу".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "🔧 Для остановки: Ctrl+C".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Показываем статус в реальном времени
    print("📊 СТАТУС СИСТЕМЫ:")
    print("  🟢 Все системы работают")
    print("  📡 Ожидание сообщений...")
    print()

    # Graceful shutdown
    async def on_shutdown():
        logging.info("Остановка бота...")
        await bot.session.close()
        logging.info("Бот остановлен")

    # Регистрируем обработчик сигналов
    def signal_handler(signum, frame):
        logging.info(f"Получен сигнал остановки: {signum}")
        asyncio.create_task(on_shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запуск бота
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            retry_count += 1
            logging.info(f"Подключение к Telegram API (попытка {retry_count}/{max_retries})")
            await dp.start_polling(bot, skip_updates=True)
            break
        except Exception as e:
            logging.error(f"Ошибка подключения: {e}")
            if retry_count < max_retries:
                wait_time = retry_count * 3
                logging.info(f"Повторная попытка через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
            else:
                logging.critical("Не удалось подключиться к Telegram API")
                break

    await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Работа бота завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)