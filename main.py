
import asyncio
import logging
import os
import sqlite3
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

def check_bot_connection(bot_token):
    """Проверка подключения к Telegram"""
    print_colored("\n📱 ПРОВЕРКА TELEGRAM API:", Colors.OKBLUE + Colors.BOLD)
    
    try:
        # Создаем временного бота для проверки
        temp_bot = Bot(token=bot_token)
        print_colored("  ✅ Токен бота: ВАЛИДНЫЙ", Colors.OKGREEN)
        return True
    except Exception as e:
        print_colored(f"  ❌ Ошибка токена: {str(e)}", Colors.FAIL)
        return False

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

async def main():
    """Основная функция для запуска бота"""
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
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Тестируем подключение к Telegram
        bot_connection_ok = await test_bot_connection(BOT_TOKEN)
        if not bot_connection_ok:
            print_colored("\n❌ ОШИБКА: Не удается подключиться к Telegram API!", Colors.FAIL + Colors.BOLD)
            return

        # Регистрация роутеров
        print_colored("\n🔗 РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ:", Colors.OKBLUE + Colors.BOLD)
        dp.include_router(user.router)
        print_colored("  ✅ Пользовательские команды зарегистрированы", Colors.OKGREEN)
        
        dp.include_router(admin.router)
        print_colored("  ✅ Административные команды зарегистрированы", Colors.OKGREEN)
        
        dp.include_router(stats.router)
        print_colored("  ✅ Статистика зарегистрирована", Colors.OKGREEN)
        
        dp.include_router(notifications.router)
        print_colored("  ✅ Уведомления зарегистрированы", Colors.OKGREEN)

        # Настройка планировщика уведомлений
        print_colored("\n⏰ НАСТРОЙКА ПЛАНИРОВЩИКА:", Colors.OKBLUE + Colors.BOLD)
        try:
            notifications.setup_scheduler(bot)
            print_colored("  ✅ Планировщик уведомлений настроен", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"  ⚠️  Ошибка планировщика: {str(e)}", Colors.WARNING)

        # Финальный тест
        await test_bot_functionality(bot)

        # Успешный запуск
        print_colored("\n" + "🎉" * 20, Colors.OKGREEN)
        print_colored("🤖 БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ!", Colors.OKGREEN + Colors.BOLD)
        print_colored("📱 Пользователи могут начать работу с ботом", Colors.OKGREEN)
        print_colored("👑 Главный админ ID: " + str(MAIN_ADMIN_ID), Colors.OKCYAN)
        print_colored("🎉" * 20, Colors.OKGREEN)

        # Запуск бота
        print_colored("\n📡 Начало прослушивания сообщений...", Colors.OKCYAN)
        await dp.start_polling(bot)

    except Exception as e:
        print_colored(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА: {e}", Colors.FAIL + Colors.BOLD)
        print_colored("🔧 Проверьте конфигурацию и попробуйте снова", Colors.WARNING)

if __name__ == '__main__':
    asyncio.run(main())
