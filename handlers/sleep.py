from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from keyboards.main_menu import main_keyboard
from states.sleep_states import SleepState
from utils.time_utils import (
    calculate_sleep_duration,
    format_date,
    format_minutes,
    get_sleep_period_label,
    normalize_time,
    parse_sleep_date,
    sleep_date_to_datetime,
)

from database.db import async_session
from database.models import SleepRecord
from services.analytics import get_duplicate_sleep_record

router = Router()

date_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сегодня"), KeyboardButton(text="Вчера")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

sleep_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ночной"), KeyboardButton(text="Дневной")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

duplicate_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сохранить все равно")],
        [KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

SLEEP_TYPES = {
    "ночной": "night",
    "дневной": "nap",
}

SLEEP_TYPE_LABELS = {
    "night": "ночной",
    "nap": "дневной",
}


# 🚀 Шаг 1: старт сценария
@router.message(F.text == "Добавить сон")
async def start_sleep(message: Message, state: FSMContext):
    await message.answer(
        "📅 За какую дату записать сон? Обычно это дата пробуждения.\n"
        "Выбери кнопку или напиши дату в формате 28.04",
        reply_markup=date_keyboard,
    )
    await state.set_state(SleepState.sleep_date)


# 🚀 Шаг 2: ввод даты сна
@router.message(SleepState.sleep_date, F.text == "Назад")
async def back_from_sleep_date(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, вернулись в меню.", reply_markup=main_keyboard)


@router.message(SleepState.sleep_date)
async def get_sleep_date(message: Message, state: FSMContext):
    sleep_date = parse_sleep_date(message.text or "")

    if sleep_date is None:
        await message.answer(
            "❌ Не понял дату.\n"
            "Напиши: сегодня, вчера или дату в формате 28.04"
        )
        return

    await state.update_data(
        sleep_date=format_date(sleep_date),
        sleep_date_iso=sleep_date.isoformat(),
    )
    await message.answer(
        f"Сон за {format_date(sleep_date)}.\n"
        "Какой это сон?",
        reply_markup=sleep_type_keyboard,
    )
    await state.set_state(SleepState.sleep_type)


# 🚀 Шаг 3: ввод типа сна
@router.message(SleepState.sleep_type, F.text == "Назад")
async def back_from_sleep_type(message: Message, state: FSMContext):
    await message.answer(
        "📅 За какую дату записать сон? Обычно это дата пробуждения.\n"
        "Выбери кнопку или напиши дату в формате 28.04",
        reply_markup=date_keyboard,
    )
    await state.set_state(SleepState.sleep_date)


@router.message(SleepState.sleep_type)
async def get_sleep_type(message: Message, state: FSMContext):
    sleep_type = SLEEP_TYPES.get((message.text or "").strip().lower())

    if sleep_type is None:
        await message.answer("Выбери тип сна: Ночной или Дневной")
        return

    data = await state.get_data()

    await state.update_data(sleep_type=sleep_type)
    await message.answer(
        f"🕒 {SLEEP_TYPE_LABELS[sleep_type].capitalize()} сон за {data.get('sleep_date')}.\n"
        "Во сколько ты лег? Можно написать 23:30, 23.30 или 2330\n"
        "Если ошибся, напиши Назад",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(SleepState.sleep_time)


# 🚀 Шаг 4: ввод времени сна
@router.message(SleepState.sleep_time, F.text == "Назад")
async def back_from_sleep_time(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.answer(
        f"Сон за {data.get('sleep_date')}.\n"
        "Какой это сон?",
        reply_markup=sleep_type_keyboard,
    )
    await state.set_state(SleepState.sleep_type)


@router.message(SleepState.sleep_time)
async def get_sleep_time(message: Message, state: FSMContext):
    sleep_time = normalize_time(message.text or "")

    if sleep_time is None:
        await message.answer(
            "❌ Неверный формат времени.\n"
            "Можно написать 23:30, 23.30, 2330 или 7"
        )
        return

    await state.update_data(sleep_time=sleep_time)
    await message.answer(
        "⏰ Во сколько проснулся? Например 07:30, 7.30 или 730\n"
        "Если ошибся, напиши Назад"
    )
    await state.set_state(SleepState.wake_time)


async def save_sleep_record(message: Message, data: dict):
    sleep_date = parse_sleep_date(data.get("sleep_date") or "")
    sleep_type = data.get("sleep_type") or "night"
    sleep_time = data.get("sleep_time")
    wake_time = data.get("wake_time")
    total_minutes = data.get("total_minutes")

    async with async_session() as session:
        record = SleepRecord(
            user_id=message.from_user.id,
            sleep_time=sleep_time,
            wake_time=wake_time,
            duration=total_minutes,
            sleep_type=sleep_type,
            created_at=sleep_date_to_datetime(sleep_date),
        )
        session.add(record)
        await session.commit()

    text = (
        f"📅 Сон за {format_date(sleep_date)}\n"
        f"Тип: {SLEEP_TYPE_LABELS.get(sleep_type, 'сон')}\n"
        f"🌙 Период: {get_sleep_period_label(sleep_date, sleep_time, wake_time)}\n"
        f"🛌 Ты спал: {format_minutes(total_minutes)}\n"
        f"⏰ {sleep_time} → {wake_time}\n\n"
    )

    if total_minutes < 7 * 60 and sleep_type == "night":
        deficit = (8 * 60) - total_minutes
        text += (
            f"⚠️ Недосып: ~{format_minutes(deficit)}\n"
            "Рекомендуется дневной сон 30–90 мин"
        )
    elif 7 * 60 <= total_minutes <= 9 * 60 and sleep_type == "night":
        text += "✅ Отличный сон!"
    elif sleep_type == "nap":
        text += "Дневной сон учтен отдельно в списке записей."
    else:
        text += "😴 Ты спал довольно долго"

    await message.answer(text, reply_markup=main_keyboard)


# 🚀 Шаг 5: финал — расчет + сохранение
@router.message(SleepState.wake_time, F.text == "Назад")
async def back_from_wake_time(message: Message, state: FSMContext):
    await message.answer(
        "🕒 Во сколько ты лег? Можно написать 23:30, 23.30 или 2330\n"
        "Если ошибся, напиши Назад"
    )
    await state.set_state(SleepState.sleep_time)


@router.message(SleepState.wake_time)
async def get_wake_time(message: Message, state: FSMContext):
    data = await state.get_data()

    sleep_date = parse_sleep_date(data.get("sleep_date") or "")
    sleep_type = data.get("sleep_type") or "night"
    sleep_time = data.get("sleep_time")
    wake_time = normalize_time(message.text or "")

    # 📊 считаем сон
    duration = calculate_sleep_duration(sleep_time, wake_time)

    if duration is None:
        await message.answer(
            "❌ Неверный формат времени.\nПопробуй снова (например 07:30)"
        )
        return

    total_seconds = duration.total_seconds()
    total_minutes = int(total_seconds // 60)

    created_at = sleep_date_to_datetime(sleep_date)

    async with async_session() as session:
        duplicate = await get_duplicate_sleep_record(
            session,
            user_id=message.from_user.id,
            created_at=created_at,
            sleep_time=sleep_time,
            wake_time=wake_time,
            sleep_type=sleep_type,
        )

    pending_record = {
        "sleep_date": format_date(sleep_date),
        "sleep_type": sleep_type,
        "sleep_time": sleep_time,
        "wake_time": wake_time,
        "total_minutes": total_minutes,
    }

    if duplicate:
        await state.update_data(**pending_record)
        await message.answer(
            "Похоже, такая запись уже есть:\n"
            f"{format_date(sleep_date)} | "
            f"{SLEEP_TYPE_LABELS.get(sleep_type, 'сон')} | "
            f"{sleep_time}-{wake_time}\n\n"
            "Сохранить дубль?",
            reply_markup=duplicate_keyboard,
        )
        await state.set_state(SleepState.duplicate_confirm)
        return

    await save_sleep_record(message, pending_record)
    await state.clear()


@router.message(SleepState.duplicate_confirm)
async def confirm_duplicate(message: Message, state: FSMContext):
    answer = (message.text or "").strip().lower()

    if answer == "назад":
        await message.answer(
            "⏰ Во сколько проснулся? Например 07:30, 7.30 или 730\n"
            "Если ошибся, напиши Назад"
        )
        await state.set_state(SleepState.wake_time)
        return

    if answer == "отмена":
        await state.clear()
        await message.answer("Ок, не стал сохранять дубль.", reply_markup=main_keyboard)
        return

    if answer != "сохранить все равно":
        await message.answer("Выбери: Сохранить все равно или Отмена")
        return

    data = await state.get_data()
    await save_sleep_record(message, data)
    await state.clear()
