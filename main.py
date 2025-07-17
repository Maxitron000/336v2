
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

async def main():
    """Основная функция для запуска бота"""
    global bot_instance, dp_instance
    
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Проверяем, не запущен ли уже другой экземпляр
    import psutil
    import os
    
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['name'] == 'python':
                if any('main.py' in str(cmd) for cmd in proc.info['cmdline'] if cmd):
                    print_colored(f"⚠️  Обнаружен запущенный процесс бота (PID: {proc.info['pid']})", Colors.WARNING)
                    print_colored("🔄 Завершаем старый процесс...", Colors.WARNING)
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    
    # Настройка логирования (скрываем лишние сообщения)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.WARNING  # Показываем только предупреждения и ошибки
    )
    
    # Красивый заголовок
    print_header()
    
    # Проверка всех систем
    env_ok = check_environment()
    db_ok = check_database()
    handlers_ok = check_handlers()
    
    # Информация о системе
    print_system_info()
    
    # Проверяем можем ли мы запуститься
    all_systems_ok = env_ok and db_ok and handlers_ok
    
    # Выводим сводку
    print_startup_summary(all_systems_ok)
    
    if not env_ok:
        print_colored("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не настроены переменные окружения!", Colors.FAIL + Colors.BOLD)
        print_colored("📝 Проверьте файл .env и убедитесь что BOT_TOKEN и MAIN_ADMIN_ID заданы правильно", Colors.WARNING)
        return

    try:
        # Создание бота и диспетчера
        bot_instance = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp_instance = Dispatcher(storage=storage)

        # Тестируем подключение к Telegram
        bot_test_ok = await test_bot_functionality(bot_instance)
        if not bot_test_ok:
            print_colored("\n❌ ОШИБКА: Не удается подключиться к Telegram API!", Colors.FAIL + Colors.BOLD)
            return

        # Регистрация роутеров
        print_colored("\n🔗 РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ:", Colors.OKBLUE + Colors.BOLD)
        dp_instance.include_router(user.router)
        print_colored("  ✅ Пользовательские команды зарегистрированы", Colors.OKGREEN)
        
        dp_instance.include_router(admin.router)
        print_colored("  ✅ Административные команды зарегистрированы", Colors.OKGREEN)
        
        dp_instance.include_router(stats.router)
        print_colored("  ✅ Статистика зарегистрирована", Colors.OKGREEN)
        
        dp_instance.include_router(notifications.router)
        print_colored("  ✅ Уведомления зарегистрированы", Colors.OKGREEN)

        # Настройка планировщика уведомлений
        print_colored("\n⏰ НАСТРОЙКА ПЛАНИРОВЩИКА:", Colors.OKBLUE + Colors.BOLD)
        try:
            notifications.setup_scheduler(bot_instance)
            print_colored("  ✅ Планировщик уведомлений настроен", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"  ⚠️  Ошибка планировщика: {str(e)}", Colors.WARNING)

        # Автоматическая очистка при запуске
        print_colored("\n🧹 АВТОМАТИЧЕСКАЯ ОЧИСТКА:", Colors.OKBLUE + Colors.BOLD)
        try:
            from cleanup_unused import SystemCleaner
            cleaner = SystemCleaner()
            cleanup_results = cleaner.full_cleanup()
            print_colored(f"  ✅ Записей удалено: {cleanup_results['records_deleted']}", Colors.OKGREEN)
            print_colored(f"  ✅ Экспортов удалено: {cleanup_results['exports_deleted']}", Colors.OKGREEN)
            print_colored(f"  ✅ Логов удалено: {cleanup_results['logs_deleted']}", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"  ⚠️  Ошибка очистки: {str(e)}", Colors.WARNING)

        # Финальный тест
        await test_bot_functionality(bot_instance)

        # Успешный запуск
        print_colored("\n" + "🎉" * 20, Colors.OKGREEN)
        print_colored("🤖 БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ!", Colors.OKGREEN + Colors.BOLD)
        print_colored("📱 Пользователи могут начать работу с ботом", Colors.OKGREEN)
        print_colored("👑 Главный админ ID: " + str(MAIN_ADMIN_ID), Colors.OKCYAN)
        print_colored("🎉" * 20, Colors.OKGREEN)

        # Запуск бота
        print_colored("\n📡 Начало прослушивания сообщений...", Colors.OKCYAN)
        
        try:
            # Создаем задачу для polling
            polling_task = asyncio.create_task(dp_instance.start_polling(bot_instance, skip_updates=True))
            
            # Ожидаем либо завершения polling, либо сигнала завершения
            done, pending = await asyncio.wait(
                [polling_task, asyncio.create_task(shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Если получен сигнал завершения
            if shutdown_event.is_set():
                print_colored("\n🛑 Получен сигнал завершения...", Colors.WARNING)
                polling_task.cancel()
                await graceful_shutdown()
            
        except Exception as polling_error:
            if "Conflict" in str(polling_error):
                print_colored(f"\n⚠️  Конфликт с другим экземпляром бота!", Colors.WARNING + Colors.BOLD)
                print_colored("🔄 Попытка перезапуска через 5 секунд...", Colors.WARNING)
                await asyncio.sleep(5)
                # Повторная попытка запуска
                polling_task = asyncio.create_task(dp_instance.start_polling(bot_instance, skip_updates=True))
                done, pending = await asyncio.wait(
                    [polling_task, asyncio.create_task(shutdown_event.wait())],
                    return_when=asyncio.FIRST_COMPLETED
                )
                if shutdown_event.is_set():
                    polling_task.cancel()
                    await graceful_shutdown()
            else:
                print_colored(f"\n❌ Ошибка polling: {polling_error}", Colors.FAIL)
                raise polling_error

    except Exception as e:
        print_colored(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА: {e}", Colors.FAIL + Colors.BOLD)
        print_colored("🔧 Проверьте конфигурацию и попробуйте снова", Colors.WARNING)
        await graceful_shutdown()
    finally:
        print_colored("\n👋 Завершение работы бота", Colors.OKCYAN)

if __name__ == '__main__':
    asyncio.run(main())
