
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.db_service import DatabaseService
from config import MAIN_ADMIN_ID

router = Router()
db = DatabaseService()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - показать статистику"""
    # Проверяем права доступа
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ У вас нет прав для просмотра статистики.")
        return
    
    try:
        stats = db.get_current_status()
        
        stats_text = f"""📊 **Текущая статистика**

👥 Всего личного состава: {stats['total']}
✅ Присутствуют: {stats['present']}
❌ Отсутствуют: {stats['absent']}

**📍 Отсутствующие:**
"""
        
        if stats['absent_list']:
            for person in stats['absent_list']:
                stats_text += f"• {person['name']} ({person['location']})\n"
        else:
            stats_text += "Все на месте! ✅"
        
        await message.answer(stats_text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}")
