from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.db_service import DatabaseService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time
import logging
import json
import random
import os
import asyncio

router = Router()
db = DatabaseService()
scheduler = AsyncIOScheduler()

# Креативные тексты для уведомлений
CREATIVE_TEXTS = {
    'morning': [
        "🌅 Доброе утро, защитники! Время отметиться в табеле!",
        "☀️ Новый день - новые подвиги! Не забудьте про табель!",
        "🎖️ Военная дисциплина начинается с табеля. Отметьтесь!",
        "🚀 Готовы к новому дню службы? Отметка в табеле обязательна!",
        "⭐ Звезды погасли, но ваша служба продолжается! Табель ждет!"
    ],
    'evening': [
        "🌙 День службы завершается. Проверьте свой статус в табеле!",
        "🌆 Время подводить итоги дня. Табель в порядке?",
        "🎯 Миссия дня выполнена? Убедитесь, что табель тоже!",
        "🏠 Конец дня - время проверить отметки в табеле!",
        "📋 Дисциплина 24/7! Последняя проверка табеля на сегодня."
    ],
    'reminder': [
        "⏰ Напоминание: табель требует вашего внимания!",
        "🔔 Не забывайте отмечаться при убытии и прибытии!",
        "📱 Быстрое напоминание: проверьте свой статус в табеле!",
        "🎖️ Военная точность включает и табель!",
        "⚡ Секундное дело - отметиться в табеле!"
    ],
    'weekly': [
        "📊 Еженедельный отчет готов! Проверьте статистику.",
        "📈 Неделя службы завершена. Анализируем показатели!",
        "🏆 Итоги недели: кто был самым дисциплинированным?",
        "📋 Еженедельная сводка активности готова к просмотру!",
        "🎯 Неделя за неделей - строим дисциплину вместе!"
    ]
}

# Настройки уведомлений по умолчанию
DEFAULT_SETTINGS = {
    'morning_reminder': True,
    'evening_reminder': True,
    'weekly_report': True,
    'activity_notifications': True,
    'quiet_mode': False,
    'quiet_start': '22:00',
    'quiet_end': '06:00',
    'morning_time': '08:00',
    'evening_time': '18:00',
    'weekly_day': 'monday',
    'weekly_time': '10:00'
}

def load_notification_settings():
    """Загрузить настройки уведомлений"""
    try:
        if os.path.exists('notifications.json'):
            with open('notifications.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return DEFAULT_SETTINGS
    except Exception as e:
        logging.error(f"Ошибка загрузки настроек уведомлений: {e}")
        return DEFAULT_SETTINGS

def save_notification_settings(settings):
    """Сохранить настройки уведомлений"""
    try:
        with open('notifications.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения настроек уведомлений: {e}")
        return False

def get_random_text(category):
    """Получить случайный текст для уведомления"""
    texts = CREATIVE_TEXTS.get(category, CREATIVE_TEXTS['reminder'])
    return random.choice(texts)

def is_quiet_time():
    """Проверить, является ли текущее время тихим часом"""
    settings = load_notification_settings()

    if not settings.get('quiet_mode', False):
        return False

    try:
        now = datetime.now().time()
        quiet_start = datetime.strptime(settings['quiet_start'], '%H:%M').time()
        quiet_end = datetime.strptime(settings['quiet_end'], '%H:%M').time()

        if quiet_start <= quiet_end:
            return quiet_start <= now <= quiet_end
        else:  # Через полночь
            return now >= quiet_start or now <= quiet_end
    except Exception as e:
        logging.error(f"Ошибка проверки тихого времени: {e}")
        return False

async def send_notification_to_admins(bot: Bot, message: str, parse_mode: str = None):
    """Отправить уведомление всем админам"""
    try:
        admins = db.get_all_admins()
        sent_count = 0

        for admin in admins:
            try:
                await bot.send_message(
                    admin['id'], 
                    message, 
                    parse_mode=parse_mode
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления админу {admin['id']}: {e}")

        logging.info(f"Уведомление отправлено {sent_count} администраторам")
        return sent_count

    except Exception as e:
        logging.error(f"Ошибка отправки уведомлений админам: {e}")
        return 0

async def send_morning_reminder(bot: Bot):
    """Утреннее напоминание"""
    if is_quiet_time():
        return

    try:
        text = get_random_text('morning')
        await send_notification_to_admins(bot, text)
        logging.info("Отправлено утреннее напоминание")
    except Exception as e:
        logging.error(f"Ошибка утреннего напоминания: {e}")

async def send_evening_reminder(bot: Bot):
    """Вечернее напоминание"""
    if is_quiet_time():
        return

    try:
        # Получаем статистику дня
        records_today = db.get_records_today()
        status = db.get_current_status()

        text = get_random_text('evening')
        text += f"\n\n📊 **Статистика дня:**\n"
        text += f"• Записей сегодня: {len(records_today)}\n"
        text += f"• В части: {status['present']}\n"
        text += f"• Вне части: {status['absent']}"

        await send_notification_to_admins(bot, text, parse_mode="Markdown")
        logging.info("Отправлено вечернее напоминание")
    except Exception as e:
        logging.error(f"Ошибка вечернего напоминания: {e}")

async def send_weekly_report(bot: Bot):
    """Еженедельный отчет"""
    if is_quiet_time():
        return

    try:
        # Статистика за неделю
        records_week = db.get_all_records(days=7)
        users = db.get_all_users()

        # Топ активных пользователей
        user_activity = {}
        for record in records_week:
            name = record['full_name']
            user_activity[name] = user_activity.get(name, 0) + 1

        top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]

        text = get_random_text('weekly')
        text += f"\n\n📊 **Еженедельная сводка:**\n"
        text += f"• Всего записей: {len(records_week)}\n"
        text += f"• Активных пользователей: {len(user_activity)}\n"
        text += f"• Всего зарегистрировано: {len(users)}\n\n"

        if top_users:
            text += f"🏆 **ТОП активности:**\n"
            for i, (name, count) in enumerate(top_users, 1):
                text += f"{i}. {name}: {count} записей\n"

        # Создаем Excel отчет
        filename = db.export_to_excel(days=7)

        await send_notification_to_admins(bot, text, parse_mode="Markdown")

        # Отправляем файл главному админу
        if filename:
            try:
                from config import MAIN_ADMIN_ID
                from aiogram.types import FSInputFile

                document = FSInputFile(filename)
                await bot.send_document(
                    MAIN_ADMIN_ID,
                    document,
                    caption="📊 Еженедельный отчет в Excel"
                )

                # Удаляем временный файл
                os.remove(filename)
            except Exception as e:
                logging.error(f"Ошибка отправки Excel файла: {e}")

        logging.info("Отправлен еженедельный отчет")
    except Exception as e:
        logging.error(f"Ошибка еженедельного отчета: {e}")

async def cleanup_old_records():
    """Очистка старых записей"""
    try:
        deleted_count = db.cleanup_old_records(days=180)  # 6 месяцев

        if deleted_count > 0:
            message = f"🧹 **Автоматическая очистка**\n\n"
            message += f"Удалено старых записей: {deleted_count}\n"
            message += f"Записи старше 180 дней были удалены для оптимизации."

            from config import MAIN_ADMIN_ID
            try:
                # Уведомляем только главного админа
                bot = Bot.get_current()
                await bot.send_message(MAIN_ADMIN_ID, message, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка уведомления об очистке: {e}")

        logging.info(f"Очищено старых записей: {deleted_count}")
    except Exception as e:
        logging.error(f"Ошибка очистки записей: {e}")

def setup_scheduler(bot: Bot = None):
    """Настройка планировщика задач"""
    try:
        settings = load_notification_settings()

        # Убираем старые задачи
        scheduler.remove_all_jobs()

        if settings.get('morning_reminder', True):
            morning_time = settings.get('morning_time', '08:00').split(':')
            scheduler.add_job(
                lambda: asyncio.create_task(send_morning_reminder(bot)) if bot else None,
                'cron',
                hour=int(morning_time[0]),
                minute=int(morning_time[1]),
                id='morning_reminder'
            )
            logging.info(f"✅ Утреннее напоминание настроено на {settings.get('morning_time', '08:00')}")

        if settings.get('evening_reminder', True):
            evening_time = settings.get('evening_time', '20:00').split(':')
            scheduler.add_job(
                lambda: asyncio.create_task(send_evening_reminder(bot)) if bot else None,
                'cron',
                hour=int(evening_time[0]),
                minute=int(evening_time[1]),
                id='evening_reminder'
            )
            logging.info(f"✅ Вечернее напоминание настроено на {settings.get('evening_time', '20:00')}")

        if settings.get('weekly_reports', True):
            weekly_day = settings.get('weekly_day', 0)  # 0 = понедельник
            weekly_hour = settings.get('weekly_hour', 9)
            scheduler.add_job(
                lambda: asyncio.create_task(send_weekly_report(bot)) if bot else None,
                'cron',
                day_of_week=weekly_day,
                hour=weekly_hour,
                id='weekly_report'
            )
            logging.info(f"✅ Еженедельный отчет настроен на день {weekly_day}, час {weekly_hour}")

        if not scheduler.running:
            scheduler.start()
            logging.info("✅ Планировщик запущен")

        logging.info("✅ Планировщик настроен успешно")

    except Exception as e:
        logging.error(f"Ошибка настройки планировщика: {e}")
        import traceback
        logging.error(f"Трассировка: {traceback.format_exc()}")

        # Пытаемся настроить базовые задачи с дефолтными настройками
        try:
            scheduler.remove_all_jobs()

            # Добавляем базовые задачи с дефолтными настройками
            scheduler.add_job(
                lambda: asyncio.create_task(send_morning_reminder(bot)) if bot else None,
                'cron',
                hour=8,
                minute=0,
                id='morning_reminder'
            )

            scheduler.add_job(
                lambda: asyncio.create_task(send_evening_reminder(bot)) if bot else None,
                'cron',
                hour=20,
                minute=0,
                id='evening_reminder'
            )

            if not scheduler.running:
                scheduler.start()

            logging.info("✅ Планировщик настроен с дефолтными параметрами")
        except Exception as e2:
            logging.error(f"Ошибка базовой настройки планировщика: {e2}")

@router.callback_query(lambda c: c.data and c.data.startswith('notification_'))
async def handle_notification_settings(callback: CallbackQuery):
    """Обработка настроек уведомлений"""
    try:
        action = callback.data.replace('notification_', '')
        settings = load_notification_settings()

        if action == 'toggle_morning':
            settings['morning_reminder'] = not settings.get('morning_reminder', True)
            status = "включены" if settings['morning_reminder'] else "отключены"
            await callback.answer(f"Утренние уведомления {status}")

        elif action == 'toggle_evening':
            settings['evening_reminder'] = not settings.get('evening_reminder', True)
            status = "включены" if settings['evening_reminder'] else "отключены"
            await callback.answer(f"Вечерние уведомления {status}")

        elif action == 'toggle_weekly':
            settings['weekly_report'] = not settings.get('weekly_report', True)
            status = "включены" if settings['weekly_report'] else "отключены"
            await callback.answer(f"Еженедельные отчеты {status}")

        elif action == 'toggle_quiet':
            settings['quiet_mode'] = not settings.get('quiet_mode', False)
            status = "включен" if settings['quiet_mode'] else "отключен"
            await callback.answer(f"Режим тишины {status}")

        # Сохраняем настройки
        save_notification_settings(settings)

        # Перенастраиваем планировщик
        bot = callback.bot
        setup_scheduler(bot)

    except Exception as e:
        logging.error(f"Ошибка настройки уведомлений: {e}")
        await callback.answer("Ошибка изменения настроек")