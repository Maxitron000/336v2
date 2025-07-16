# handlers/stats.py
from aiogram import Router, types
from aiogram.filters import Command
from services.db_service import DBService
from utils.localization import get_text

router = Router()

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = await DBService.get_statistics()
    await message.answer(f"Статистика: {stats}")

@router.message(Command("export"))
async def cmd_export(message: types.Message):
    file_path = await DBService.export_to_excel()
    await message.answer_document(types.FSInputFile(file_path))

@router.message(Command("all_journal"))
async def cmd_all_journal(message: types.Message):
    records = await DBService.get_all_records(days=30)
    if not records:
        await message.answer("Нет записей за последние 30 дней.")
        return
    text = "\n".join([f"{r['timestamp']}: {r['action']} — {r['location']} (user_id={r['user_id']})" for r in records[:20]])
    await message.answer(f"Журнал за 30 дней (первые 20):\n{text}")