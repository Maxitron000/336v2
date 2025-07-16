# handlers/user.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from utils.localization import get_text
from utils.validators import validate_full_name
from services.db_service import DBService

router = Router()

class RegisterStates(StatesGroup):
    waiting_for_full_name = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(get_text("welcome", message.from_user.language_code))
    await message.answer(get_text("enter_full_name", message.from_user.language_code))
    await state.set_state(RegisterStates.waiting_for_full_name)

@router.message(RegisterStates.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if not validate_full_name(message.text):
        await message.answer(get_text("invalid_full_name", message.from_user.language_code))
        return
    await DBService.add_user(message.from_user.id, message.from_user.username, message.text)
    await message.answer(get_text("success", message.from_user.language_code))
    await state.clear()

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user = await DBService.get_user(message.from_user.id)
    if user:
        await message.answer(f"{get_text('profile', message.from_user.language_code)}\n{user['full_name']}")
    else:
        await message.answer(get_text("error", message.from_user.language_code))