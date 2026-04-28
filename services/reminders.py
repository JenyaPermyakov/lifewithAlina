from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select

from database.db import async_session
from database.models import UserReminder

ALMATY_TZ = ZoneInfo("Asia/Almaty")


async def upsert_reminder(session, user_id: int, reminder_time: str):
    stmt = select(UserReminder).where(UserReminder.user_id == user_id)
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    if reminder is None:
        reminder = UserReminder(
            user_id=user_id,
            reminder_time=reminder_time,
            is_enabled=1,
        )
        session.add(reminder)
    else:
        reminder.reminder_time = reminder_time
        reminder.is_enabled = 1

    await session.commit()
    return reminder


async def disable_reminder(session, user_id: int):
    stmt = select(UserReminder).where(UserReminder.user_id == user_id)
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    if reminder is None:
        return False

    reminder.is_enabled = 0
    await session.commit()
    return True


async def send_due_reminders(bot: Bot):
    now = datetime.now(ALMATY_TZ)
    current_time = now.strftime("%H:%M")
    today = now.date().isoformat()

    async with async_session() as session:
        stmt = select(UserReminder).where(
            UserReminder.is_enabled == 1,
            UserReminder.reminder_time == current_time,
        )
        result = await session.execute(stmt)
        reminders = result.scalars().all()

        for reminder in reminders:
            if reminder.last_sent_date == today:
                continue

            await bot.send_message(
                reminder.user_id,
                "Напоминание: пора записать сон или подготовиться ко сну.",
            )
            reminder.last_sent_date = today

        await session.commit()
