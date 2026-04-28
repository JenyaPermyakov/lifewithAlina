from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import delete, select, func

from database.models import SleepRecord

ALMATY_TZ = ZoneInfo("Asia/Almaty")


@dataclass(frozen=True)
class SleepDaySummary:
    created_at: datetime
    duration: int
    records_count: int = 0


def get_period_bounds(days: int):
    today = datetime.now(ALMATY_TZ).date()
    start_date = today - timedelta(days=days - 1)
    end_date = today + timedelta(days=1)

    return (
        datetime.combine(start_date, time.min, tzinfo=ALMATY_TZ),
        datetime.combine(end_date, time.min, tzinfo=ALMATY_TZ),
    )


# 📅 за сегодня
async def get_today_sleep(session, user_id):
    start_of_day, end_of_day = get_period_bounds(1)

    stmt = select(
        func.sum(SleepRecord.duration),
        func.count(SleepRecord.id),
    ).where(
        SleepRecord.user_id == user_id,
        SleepRecord.created_at >= start_of_day,
        SleepRecord.created_at < end_of_day,
    )

    result = await session.execute(stmt)
    total, count = result.first()

    return total or 0, count or 0


# 📊 за период
async def get_period_stats(session, user_id, days: int):
    start_date, end_date = get_period_bounds(days)

    sleep_day = func.date(SleepRecord.created_at).label("sleep_day")

    daily_totals = (
        select(
            sleep_day,
            func.sum(SleepRecord.duration).label("duration"),
            func.count(SleepRecord.id).label("records_count"),
        )
        .where(
            SleepRecord.user_id == user_id,
            SleepRecord.created_at >= start_date,
            SleepRecord.created_at < end_date,
        )
        .group_by(sleep_day)
        .subquery()
    )

    stmt = select(
        func.avg(daily_totals.c.duration),
        func.sum(daily_totals.c.duration),
        func.count(daily_totals.c.sleep_day),
        func.sum(daily_totals.c.records_count),
    )

    result = await session.execute(stmt)
    avg, total, days_count, records_count = result.first()

    return avg or 0, total or 0, days_count or 0, records_count or 0


async def get_sleep_type_totals(session, user_id, days: int):
    start_date, end_date = get_period_bounds(days)

    stmt = (
        select(
            SleepRecord.sleep_type,
            func.sum(SleepRecord.duration),
            func.count(SleepRecord.id),
        )
        .where(
            SleepRecord.user_id == user_id,
            SleepRecord.created_at >= start_date,
            SleepRecord.created_at < end_date,
        )
        .group_by(SleepRecord.sleep_type)
    )

    result = await session.execute(stmt)
    totals = {}

    for sleep_type, duration, count in result.all():
        totals[sleep_type or "night"] = {
            "duration": duration or 0,
            "count": count or 0,
        }

    return totals


async def get_sleep_history(session, user_id, days=7):
    start_date, end_date = get_period_bounds(days)
    sleep_day = func.date(SleepRecord.created_at).label("sleep_day")

    stmt = (
        select(
            sleep_day,
            func.sum(SleepRecord.duration).label("duration"),
            func.count(SleepRecord.id).label("records_count"),
        )
        .where(
            SleepRecord.user_id == user_id,
            SleepRecord.created_at >= start_date,
            SleepRecord.created_at < end_date,
        )
        .group_by(sleep_day)
        .order_by(sleep_day)
    )

    result = await session.execute(stmt)
    records = []

    for sleep_day, duration, records_count in result.all():
        records.append(
            SleepDaySummary(
                created_at=datetime.combine(sleep_day, time.min, tzinfo=ALMATY_TZ),
                duration=int(duration or 0),
                records_count=int(records_count or 0),
            )
        )

    return records


async def get_recent_sleep_records(session, user_id, limit=5):
    stmt = (
        select(SleepRecord)
        .where(SleepRecord.user_id == user_id)
        .order_by(SleepRecord.created_at.desc(), SleepRecord.id.desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_duplicate_sleep_record(
    session,
    user_id,
    created_at,
    sleep_time,
    wake_time,
    sleep_type,
):
    stmt = (
        select(SleepRecord)
        .where(
            SleepRecord.user_id == user_id,
            SleepRecord.created_at == created_at,
            SleepRecord.sleep_time == sleep_time,
            SleepRecord.wake_time == wake_time,
            SleepRecord.sleep_type == sleep_type,
        )
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_last_sleep_record(session, user_id):
    records = await get_recent_sleep_records(session, user_id, limit=1)

    if not records:
        return None

    record = records[0]

    stmt = delete(SleepRecord).where(
        SleepRecord.id == record.id,
        SleepRecord.user_id == user_id,
    )
    await session.execute(stmt)
    await session.commit()

    return record
