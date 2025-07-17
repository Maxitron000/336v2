import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', 0))

# Проверка обязательных настроек
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not MAIN_ADMIN_ID:
    raise ValueError("MAIN_ADMIN_ID не найден в переменных окружения")

# Основные настройки
BOT_NAME = "Рота В - Электронный Табель"
UNIT_NAME = "Рота \"В\""

# Локации
LOCATIONS = [
    "🏥 Поликлиника",
    "⚓ ОБРМП", 
    "🌆 Калининград",
    "🛒 Магазин",
    "🍲 Столовая",
    "🏨 Госпиталь",
    "⚙️ Рабочка",
    "🩺 ВВК",
    "🏛️ МФЦ",
    "🚓 Патруль",
    "📝 Другое"  # Показывается только для убыли
]

# Настройки базы данных
DB_NAME = 'military_tracker.db'

# Настройки экспорта
EXPORT_FILENAME = 'military_records.xlsx'