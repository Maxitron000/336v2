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
```

I am unable to perform requested edit because the provided code doesn't contain `action_emoji` variable.
Since I cannot execute the changes directly on the given code, I will make changes in the `cmd_stats` function to replace the emojis. This may require assuming where the relevant logic resides, but I will aim for the most logical placement based on the context provided. I will also adjust emojis on present and absent stats

```python
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
🟢 Присутствуют: {stats['present']}
🔴 Отсутствуют: {stats['absent']}

**📍 Отсутствующие:**
"""

        if stats['absent_list']:
            for person in stats['absent_list']:
                # Предполагаем, что здесь нужно использовать action_emoji
                action_emoji = "🔴" if person['action'] == "убыл" else "🟢" # Defaulting to present if not "убыл"
                stats_text += f"• {person['name']} ({person['location']}) {action_emoji}\n" #Adding emoji to the absent list

        else:
            stats_text += "Все на месте! ✅"

        await message.answer(stats_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}")
```

```
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
🟢 Присутствуют: {stats['present']}
🔴 Отсутствуют: {stats['absent']}

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