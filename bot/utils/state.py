from aiogram.fsm.state import StatesGroup, State

class RequestState(StatesGroup):
    email = State()
    number = State()

class SignUp(StatesGroup):
    get_name = State()
    get_surname = State()
    get_email = State()
    get_number = State()

class AdminState(StatesGroup):
    admin = State()
    wait_username_add = State()
    wait_username_del = State()


class ScheduleAdd(StatesGroup):
    lesson_number = State()
    subject = State()
    time_start = State()
    time_end = State()
    classroom = State()
    teacher = State()