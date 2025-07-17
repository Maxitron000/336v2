def get_export_period_keyboard():
    """Клавиатура выбора периода экспорта"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Excel - Сегодня", callback_data="export_excel_today"),
            InlineKeyboardButton("📄 PDF - Сегодня", callback_data="export_pdf_today")
        ],
        [
            InlineKeyboardButton("📊 Excel - Вчера", callback_data="export_excel_yesterday"),
            InlineKeyboardButton("📄 PDF - Вчера", callback_data="export_pdf_yesterday")
        ],
        [
            InlineKeyboardButton("📊 Excel - Неделя", callback_data="export_excel_week"),
            InlineKeyboardButton("📄 PDF - Неделя", callback_data="export_pdf_week")
        ],
        [
            InlineKeyboardButton("📊 Excel - Месяц", callback_data="export_excel_month"),
            InlineKeyboardButton("📄 PDF - Месяц", callback_data="export_pdf_month")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_export_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)