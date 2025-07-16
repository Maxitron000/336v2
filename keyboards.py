from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import LOCATIONS, ADMIN_PERMISSIONS

def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🚶 Убыл", callback_data="action_leave")],
        [InlineKeyboardButton("🏠 Прибыл", callback_data="action_arrive")],
        [InlineKeyboardButton("📋 Журнал", callback_data="show_journal")]
    ]
    
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Админка", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_location_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора локации"""
    keyboard = []
    
    # Создаем кнопки для каждой локации
    for location in LOCATIONS:
        keyboard.append([
            InlineKeyboardButton(
                location, 
                callback_data=f"location_{action}_{location}"
            )
        ])
    
    # Кнопка возврата
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_journal_keyboard(expanded: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура журнала"""
    if expanded:
        keyboard = [
            [InlineKeyboardButton("📋 Свернуть", callback_data="journal_collapse")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📋 Развернуть", callback_data="journal_expand")]
        ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_keyboard(is_main_admin: bool = False) -> InlineKeyboardMarkup:
    """Панель администратора - Уровень 1"""
    keyboard = [
        [InlineKeyboardButton("📊 Быстрая сводка", callback_data="admin_summary")],
        [InlineKeyboardButton("👥 Управление л/с", callback_data="admin_personnel")],
        [InlineKeyboardButton("📖 Журнал событий", callback_data="admin_journal")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")]
    ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Управление админами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton("➖ Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_settings")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_personnel_management_keyboard() -> InlineKeyboardMarkup:
    """Управление личным составом - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton("✏️ Сменить ФИО бойца", callback_data="personnel_edit_name")],
        [InlineKeyboardButton("➕ Добавить нового бойца", callback_data="personnel_add")],
        [InlineKeyboardButton("❌ Удалить бойца", callback_data="personnel_remove")]
    ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_journal_management_keyboard() -> InlineKeyboardMarkup:
    """Журнал событий - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton("📥 Экспорт журнала", callback_data="journal_export")],
        [InlineKeyboardButton("📊 Статистика", callback_data="journal_stats")],
        [InlineKeyboardButton("📋 Все записи", callback_data="journal_records")]
    ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(is_main_admin: bool = False) -> InlineKeyboardMarkup:
    """Настройки - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications")],
        [InlineKeyboardButton("⚙️ Общие настройки", callback_data="settings_general")]
    ]
    
    if is_main_admin:
        keyboard.append([InlineKeyboardButton("👑 Управление админами", callback_data="admin_manage")])
        keyboard.append([InlineKeyboardButton("⚠️ Опасная зона", callback_data="settings_danger_zone")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_danger_zone_keyboard() -> InlineKeyboardMarkup:
    """Опасная зона - Уровень 3"""
    keyboard = [
        [InlineKeyboardButton("🚨 Отметить всех прибывшими", callback_data="danger_mark_all_arrived")],
        [InlineKeyboardButton("🗑️ Очистить все данные", callback_data="danger_clear_all_data")],
        [InlineKeyboardButton("🔄 Сбросить настройки", callback_data="danger_reset_settings")]
    ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_settings")])
    
    return InlineKeyboardMarkup(keyboard)

def get_notifications_settings_keyboard() -> InlineKeyboardMarkup:
    """Настройки уведомлений"""
    keyboard = [
        [InlineKeyboardButton("🔔 Включить уведомления", callback_data="notif_enable")],
        [InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notif_disable")],
        [InlineKeyboardButton("⏰ Настройка времени", callback_data="notif_time")],
        [InlineKeyboardButton("👥 Выбор получателей", callback_data="notif_recipients")],
        [InlineKeyboardButton("🔇 Режим тишины", callback_data="notif_silent")]
    ]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_settings")])
    
    return InlineKeyboardMarkup(keyboard)

def get_permissions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора прав для админа"""
    keyboard = []
    
    for perm_key, perm_name in ADMIN_PERMISSIONS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"☐ {perm_name}", 
                callback_data=f"perm_{user_id}_{perm_key}_off"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{user_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="admin_manage")])
    
    return InlineKeyboardMarkup(keyboard)

def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)