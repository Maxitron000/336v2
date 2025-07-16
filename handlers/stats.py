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