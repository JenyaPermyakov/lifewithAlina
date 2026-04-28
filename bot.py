import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import text

from dotenv import load_dotenv

from keyboards.main_menu import main_keyboard
from handlers import common, reminders, sleep
from database.db import engine
from database.models import Base
from handlers import stats
from services.reminders import send_due_reminders

# 📌 Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN must be set in .env")


# 📌 Создаем бота и dispatcher с FSM
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 📌 Подключаем роутеры
dp.include_router(common.router)
dp.include_router(sleep.router)
dp.include_router(stats.router)
dp.include_router(reminders.router)


# 📌 Создание таблиц
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE sleep_records "
                "ADD COLUMN IF NOT EXISTS sleep_type VARCHAR DEFAULT 'night'"
            )
        )
        await conn.execute(
            text(
                "UPDATE sleep_records "
                "SET sleep_type = 'night' "
                "WHERE sleep_type IS NULL"
            )
        )


async def reminder_loop():
    while True:
        try:
            await send_due_reminders(bot)
        except Exception:
            logging.exception("Failed to send reminders")

        await asyncio.sleep(60)


# 📌 /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет!\n\nВыбери действие:",
        reply_markup=main_keyboard
    )


# 📌 Запуск
async def main():
    logging.basicConfig(level=logging.INFO)

    await create_tables()  # 🔥 ВАЖНО
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
