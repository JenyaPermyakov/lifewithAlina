from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from zoneinfo import ZoneInfo

Base = declarative_base()

ALMATY_TZ = ZoneInfo("Asia/Almaty")


class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    sleep_time = Column(String)
    wake_time = Column(String)
    duration = Column(Integer)
    sleep_type = Column(String, default="night")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ALMATY_TZ)
    )


class UserReminder(Base):
    __tablename__ = "user_reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    reminder_time = Column(String, nullable=False)
    is_enabled = Column(Integer, default=1)
    last_sent_date = Column(String)
