from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from database.db import async_session
from keyboards.main_menu import main_keyboard
from services.reminders import disable_reminder, upsert_reminder
from states.sleep_states import ReminderState
from utils.time_utils import normalize_time

router = Router()

reminder_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="22:30"), KeyboardButton(text="23:00")],
        [KeyboardButton(text="Выключить напоминание")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@router.message(F.text == "Напоминание")
async def start_reminder_setup(message: Message, state: FSMContext):
    await message.answer(
        "Во сколько напоминать каждый день?\n"
        "Можно выбрать кнопку или написать время: 22:30, 2230, 23",
        reply_markup=reminder_keyboard,
    )
    await state.set_state(ReminderState.reminder_time)


@router.message(ReminderState.reminder_time)
async def set_reminder_time(message: Message, state: FSMContext):
    text = (message.text or "").strip().lower()
    user_id = message.from_user.id

    if text == "назад":
        await state.clear()
        await message.answer("Ок, вернулись в меню.", reply_markup=main_keyboard)
        return

    if text == "выключить напоминание":
        async with async_session() as session:
            disabled = await disable_reminder(session, user_id)

        await state.clear()

        if disabled:
            await message.answer("Напоминание выключено.", reply_markup=main_keyboard)
        else:
            await message.answer("Напоминание еще не было включено.", reply_markup=main_keyboard)
        return

    reminder_time = normalize_time(text)

    if reminder_time is None:
        await message.answer("Не понял время. Напиши, например: 22:30, 2230 или 23")
        return

    async with async_session() as session:
        await upsert_reminder(session, user_id, reminder_time)

    await state.clear()
    await message.answer(
        f"Готово. Буду напоминать каждый день в {reminder_time}.",
        reply_markup=main_keyboard,
    )
