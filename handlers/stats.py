import os
from contextlib import suppress

from aiogram import Router, F
from aiogram.types import FSInputFile
from aiogram.types import Message
from database.db import async_session
from services.analytics import (
    delete_last_sleep_record,
    get_period_stats,
    get_recent_sleep_records,
    get_sleep_history,
    get_sleep_type_totals,
    get_today_sleep,
)
from utils.plot import build_sleep_chart
from utils.time_utils import format_date, format_minutes, get_sleep_period_label

router = Router()

SLEEP_TYPE_LABELS = {
    "night": "ночной",
    "nap": "дневной",
}


def format_type_totals(type_totals: dict) -> str:
    lines = []

    for sleep_type in ("night", "nap"):
        data = type_totals.get(sleep_type)

        if not data or not data["count"]:
            continue

        lines.append(
            f"   {SLEEP_TYPE_LABELS[sleep_type]}: "
            f"{format_minutes(data['duration'])}, записей: {data['count']}"
        )

    return "\n".join(lines)


@router.message(F.text == "Статистика")
async def show_stats(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        today, today_count = await get_today_sleep(session, user_id)
        today_types = await get_sleep_type_totals(session, user_id, 1)
        week_avg, week_total, week_days, week_records = await get_period_stats(
            session,
            user_id,
            7,
        )
        week_types = await get_sleep_type_totals(session, user_id, 7)
        month_avg, month_total, month_days, month_records = await get_period_stats(
            session,
            user_id,
            30,
        )

    text = "📊 Твоя статистика сна:\n\n"

    if today_count:
        text += (
            f"📅 Сегодня: {format_minutes(today)} "
            f"(всего за день, записей: {today_count})\n\n"
        )
        type_text = format_type_totals(today_types)

        if type_text:
            text += f"{type_text}\n\n"
    else:
        text += "📅 Сегодня: нет записей\n\n"

    if week_days:
        text += (
            f"📅 7 дней: {format_minutes(week_avg)} в среднем за день\n"
            f"   Всего: {format_minutes(week_total)}, дней с данными: {week_days}, "
            f"записей: {week_records}\n"
        )
        type_text = format_type_totals(week_types)

        if type_text:
            text += f"{type_text}\n"

    if month_days:
        text += (
            f"📆 30 дней: {format_minutes(month_avg)} в среднем за день\n"
            f"   Всего: {format_minutes(month_total)}, дней с данными: {month_days}, "
            f"записей: {month_records}\n"
        )

    # 🧠 аналитика
    if week_days and week_avg < 7 * 60:
        deficit = 8 * 60 - week_avg
        text += f"\n⚠️ Средний недосып за день ~{format_minutes(deficit)}"
    elif not week_days:
        text += "Пока мало данных для недельной аналитики."

    await message.answer(text)


@router.message(F.text.lower() == "график")
async def send_chart(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        records = await get_sleep_history(session, user_id, 7)

    if not records:
        await message.answer("Нет данных для графика 😢")
        return

    file_path = build_sleep_chart(records)

    try:
        photo = FSInputFile(file_path)
        await message.answer_photo(photo)
    finally:
        with suppress(FileNotFoundError):
            os.remove(file_path)


@router.message(F.text == "Последние записи")
async def show_recent_records(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        records = await get_recent_sleep_records(session, user_id, limit=5)

    if not records:
        await message.answer("Пока нет записей сна.")
        return

    lines = ["Последние записи:"]

    for index, record in enumerate(records, start=1):
        sleep_date = record.created_at.date()
        sleep_type = SLEEP_TYPE_LABELS.get(record.sleep_type or "night", "сон")
        period = get_sleep_period_label(
            sleep_date,
            record.sleep_time,
            record.wake_time,
        )
        lines.append(
            f"{index}. {format_date(sleep_date)} | {sleep_type} | "
            f"{record.sleep_time}-{record.wake_time} | "
            f"{format_minutes(record.duration)} | {period}"
        )

    await message.answer("\n".join(lines))


@router.message(F.text == "Удалить последнюю")
async def delete_last_record(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        record = await delete_last_sleep_record(session, user_id)

    if not record:
        await message.answer("Удалять пока нечего: записей нет.")
        return

    sleep_date = record.created_at.date()
    sleep_type = SLEEP_TYPE_LABELS.get(record.sleep_type or "night", "сон")

    await message.answer(
        "Удалил последнюю запись:\n"
        f"{format_date(sleep_date)} | {sleep_type} | "
        f"{record.sleep_time}-{record.wake_time} | "
        f"{format_minutes(record.duration)}"
    )
