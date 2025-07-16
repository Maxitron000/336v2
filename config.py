import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', 0))  # ID главного админа

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
    "📝 Другое"
]

# Права админов
ADMIN_PERMISSIONS = {
    'view_all_records': 'Просмотр всех записей',
    'export_data': 'Экспорт данных',
    'manage_admins': 'Управление админами',
    'view_statistics': 'Просмотр статистики'
}

# Настройки базы данных
DB_NAME = 'military_tracker.db'

# Настройки экспорта
EXPORT_FILENAME = 'military_records.xlsx'