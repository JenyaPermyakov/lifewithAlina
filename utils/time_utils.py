import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

ALMATY_TZ = ZoneInfo("Asia/Almaty")


def parse_time(time_str: str):
    """
    Преобразует ввод времени в datetime: '23:30', '23.30', '2330', '7:30', '7'.
    """
    if not time_str:
        return None

    text = time_str.strip().lower()
    hours = None
    minutes = None

    if re.fullmatch(r"\d{1,2}", text):
        hours = int(text)
        minutes = 0
    elif re.fullmatch(r"\d{3,4}", text):
        hours = int(text[:-2])
        minutes = int(text[-2:])
    else:
        match = re.fullmatch(r"(\d{1,2})[:.\s](\d{1,2})", text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))

    if hours is None or minutes is None:
        return None

    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        return None

    return datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M")


def normalize_time(time_str: str) -> str | None:
    parsed_time = parse_time(time_str)

    if parsed_time is None:
        return None

    return parsed_time.strftime("%H:%M")


def parse_sleep_date(date_str: str):
    if not date_str:
        return None

    today = datetime.now(ALMATY_TZ).date()
    text = date_str.strip().lower()

    aliases = {
        "сегодня": today,
        "today": today,
        "вчера": today - timedelta(days=1),
        "yesterday": today - timedelta(days=1),
        "позавчера": today - timedelta(days=2),
    }

    if text in aliases:
        return aliases[text]

    for date_format in ("%d.%m.%Y", "%d.%m.%y", "%d.%m"):
        try:
            parsed_date = datetime.strptime(text, date_format).date()
        except ValueError:
            continue

        if date_format == "%d.%m":
            parsed_date = parsed_date.replace(year=today.year)

        if parsed_date <= today:
            return parsed_date

        return None

    return None


def sleep_date_to_datetime(sleep_date):
    return datetime.combine(sleep_date, time(hour=12), tzinfo=ALMATY_TZ)


def format_date(sleep_date) -> str:
    return sleep_date.strftime("%d.%m.%Y")


def format_short_date(sleep_date) -> str:
    return sleep_date.strftime("%d.%m")


def get_sleep_period_label(sleep_date, sleep_time_str: str, wake_time_str: str) -> str:
    sleep_time = parse_time(sleep_time_str)
    wake_time = parse_time(wake_time_str)

    if not sleep_time or not wake_time:
        return format_date(sleep_date)

    start_date = sleep_date

    if wake_time <= sleep_time:
        start_date = sleep_date - timedelta(days=1)

    if start_date == sleep_date:
        return format_short_date(sleep_date)

    return f"{format_short_date(start_date)} → {format_short_date(sleep_date)}"


def format_minutes(total_minutes: int | float) -> str:
    total_minutes = int(total_minutes)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if minutes == 0:
        return f"{hours} ч"

    return f"{hours} ч {minutes} мин"


def calculate_sleep_duration(sleep_time_str: str, wake_time_str: str):
    sleep_time = parse_time(sleep_time_str)
    wake_time = parse_time(wake_time_str)

    if not sleep_time or not wake_time:
        return None

    sleep_dt = sleep_time
    wake_dt = wake_time

    # если проснулся на следующий день
    if wake_dt <= sleep_dt:
        wake_dt += timedelta(days=1)

    duration = wake_dt - sleep_dt

    return duration
