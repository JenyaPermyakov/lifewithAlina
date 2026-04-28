from aiogram.fsm.state import State, StatesGroup


class SleepState(StatesGroup):
    sleep_date = State()
    sleep_type = State()
    sleep_time = State()
    wake_time = State()
    duplicate_confirm = State()


class ReminderState(StatesGroup):
    reminder_time = State()
