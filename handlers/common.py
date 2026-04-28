from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.main_menu import main_keyboard

router = Router()


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Что умею:\n"
        "/cancel - отменить текущий ввод\n"
        "Добавить сон - записать ночной или дневной сон\n"
        "Статистика - итоги за день, 7 и 30 дней\n"
        "График - график сна за 7 дней\n"
        "Последние записи - показать последние сны\n"
        "Удалить последнюю - удалить последнюю запись\n"
        "Напоминание - включить или выключить ежедневное напоминание",
        reply_markup=main_keyboard,
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, отменил текущий ввод.", reply_markup=main_keyboard)


@router.message(StateFilter(None), lambda message: message.text == "Назад")
async def back_without_state(message: Message):
    await message.answer("Ты уже в главном меню.", reply_markup=main_keyboard)
