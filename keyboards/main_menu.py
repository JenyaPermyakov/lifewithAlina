from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить сон")],
        [KeyboardButton(text="Статистика"), KeyboardButton(text="График")],
        [KeyboardButton(text="Последние записи")],
        [KeyboardButton(text="Удалить последнюю")],
        [KeyboardButton(text="Напоминание")],
    ],
    resize_keyboard=True
)
