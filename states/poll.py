from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()

class PollSG(StatesGroup):
    poll = State()
    finish = State()