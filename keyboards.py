from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOCATIONS, ADMIN_PERMISSIONS

def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🚶 Убыл", callback_data="action_leave")],
        [InlineKeyboardButton(text="🏠 Прибыл", callback_data="action_arrive")],
        [InlineKeyboardButton(text="📋 Журнал", callback_data="show_journal")]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="⚙️ Админка", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_location_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора локации"""
    keyboard = []

    # Создаем кнопки для каждой локации в 2 столбца
    for i in range(0, len(LOCATIONS), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=LOCATIONS[i], 
            callback_data=f"location_{action}_{LOCATIONS[i]}"
        ))
        if i + 1 < len(LOCATIONS):
            row.append(InlineKeyboardButton(
                text=LOCATIONS[i + 1], 
                callback_data=f"location_{action}_{LOCATIONS[i + 1]}"
            ))
        keyboard.append(row)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_keyboard(expanded: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура журнала"""
    if expanded:
        keyboard = [
            [InlineKeyboardButton(text="📋 Свернуть", callback_data="journal_collapse")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="📋 Развернуть", callback_data="journal_expand")]
        ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_panel_keyboard(is_main_admin: bool = False) -> InlineKeyboardMarkup:
    """Панель администратора - Уровень 1"""
    keyboard = [
        [InlineKeyboardButton(text="📊 Быстрая сводка", callback_data="admin_summary")],
        [InlineKeyboardButton(text="👥 Управление л/с", callback_data="admin_personnel")],
        [InlineKeyboardButton(text="📖 Журнал событий", callback_data="admin_journal")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
    ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Управление админами"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_settings")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_management_keyboard() -> InlineKeyboardMarkup:
    """Управление личным составом - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Сменить ФИО бойца", callback_data="personnel_edit_name")],
        [InlineKeyboardButton(text="➕ Добавить нового бойца", callback_data="personnel_add")],
        [InlineKeyboardButton(text="❌ Удалить бойца", callback_data="personnel_remove")]
    ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_management_keyboard() -> InlineKeyboardMarkup:
    """Журнал событий - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton(text="📥 Экспорт журнала", callback_data="journal_export")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="journal_stats")],
        [InlineKeyboardButton(text="📋 Все записи", callback_data="journal_records")]
    ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_keyboard(is_main_admin: bool = False) -> InlineKeyboardMarkup:
    """Настройки - Уровень 2"""
    keyboard = [
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
        [InlineKeyboardButton(text="⚙️ Общие настройки", callback_data="settings_general")]
    ]

    if is_main_admin:
        keyboard.append([InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage")])
        keyboard.append([InlineKeyboardButton(text="⚠️ Опасная зона", callback_data="settings_danger_zone")])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_danger_zone_keyboard() -> InlineKeyboardMarkup:
    """Опасная зона - Уровень 3"""
    keyboard = [
        [InlineKeyboardButton(text="🚨 Отметить всех прибывшими", callback_data="danger_mark_all_arrived")],
        [InlineKeyboardButton(text="🗑️ Очистить все данные", callback_data="danger_clear_all_data")],
        [InlineKeyboardButton(text="🔄 Сбросить настройки", callback_data="danger_reset_settings")]
    ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_settings")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notifications_settings_keyboard() -> InlineKeyboardMarkup:
    """Настройки уведомлений"""
    keyboard = [
        [InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notif_enable")],
        [InlineKeyboardButton(text="🔕 Отключить уведомления", callback_data="notif_disable")],
        [InlineKeyboardButton(text="⏰ Настройка времени", callback_data="notif_time")],
        [InlineKeyboardButton(text="👥 Выбор получателей", callback_data="notif_recipients")],
        [InlineKeyboardButton(text="🔇 Режим тишины", callback_data="notif_silent")]
    ]

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_settings")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_permissions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора прав для админа"""
    keyboard = []

    for perm_key, perm_name in ADMIN_PERMISSIONS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"☐ {perm_name}",
                callback_data=f"perm_{user_id}_{perm_key}_off"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{user_id}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_manage")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_general_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура общих настроек пользователя"""
    keyboard = [
        [InlineKeyboardButton(text="🌐 Язык", callback_data="general_set_language")],
        [InlineKeyboardButton(text="🕒 Часовой пояс", callback_data="general_set_timezone")],
        [InlineKeyboardButton(text="⏳ Формат времени", callback_data="general_set_timeformat")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOCATIONS

def get_main_menu_keyboard(is_admin=False):
    """Главное меню с кнопками и текущим временем"""
    import pytz
    from datetime import datetime

    # Калининградское время
    kld_tz = pytz.timezone('Europe/Kaliningrad')
    current_time = datetime.now(kld_tz).strftime('%H:%M:%S')

    keyboard = [
        [
            InlineKeyboardButton(f"✅ Прибыл", callback_data="action_arrive"),
            InlineKeyboardButton(f"❌ Убыл", callback_data="action_leave")
        ],
        [
            InlineKeyboardButton("📋 Мой журнал", callback_data="show_journal"),
            InlineKeyboardButton("👤 Профиль", callback_data="profile")
        ],
        [
            InlineKeyboardButton(f"🕐 {current_time} (Калининград)", callback_data="refresh_time")
        ]
    ]

    if is_admin:
        keyboard.append([
            InlineKeyboardButton("🛡️ Админ-панель", callback_data="admin_panel")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_main_keyboard(is_main_admin=False):
    """Главная админ-панель"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Быстрая сводка", callback_data="admin_summary")
        ],
        [
            InlineKeyboardButton(text="👥 Личный состав", callback_data="admin_personnel"),
            InlineKeyboardButton(text="📖 Журнал", callback_data="admin_journal")
        ]
    ]

    if is_main_admin:
        keyboard.extend([
            [
                InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton(text="🗑️ Опасная зона", callback_data="admin_danger")
            ]
        ])

    keyboard.append([
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_keyboard():
    """Меню управления личным составом"""
    keyboard = [
        [
            InlineKeyboardButton(text="👥 Список л/с", callback_data="personnel_list"),
            InlineKeyboardButton(text="📊 Статус всех", callback_data="personnel_status")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить бойца", callback_data="personnel_delete")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_status_keyboard():
    """Меню статуса личного состава"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Все", callback_data="status_all")
        ],
        [
            InlineKeyboardButton(text="🏠 На месте", callback_data="status_present"),
            InlineKeyboardButton(text="🚶 Убыли", callback_data="status_absent")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="personnel_status")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_manage_keyboard():
    """Меню управления администраторами"""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_keyboard():
    """Меню журнала"""
    keyboard = [
        [
            InlineKeyboardButton(text="📖 Просмотр", callback_data="journal_view"),
            InlineKeyboardButton(text="📤 Экспорт", callback_data="journal_export")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard(callback_data="main_menu"):
    """Кнопка назад"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)