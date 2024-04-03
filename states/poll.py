from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()


class PollSG(StatesGroup):
    poll = State()
    finish = State()


class PollManageSG(StatesGroup):
    start = State()
    create_victorine = State()
    create_victorine_new_name = State()
    victorine_duration = State()
    victorine_edit = State()
    question_edit = State()
    add_image = State()
    answer_add = State()
    answer_del = State()
    add_question_name = State()
    add_answer1 = State()
    add_answer2 = State()
    victorine_rename = State()
    victorine_description = State()
    victorine_edit_description = State()


class LaunchVictorineSG(StatesGroup):
    select = State()
    control = State()
    start_victorine = State()
    stop_victorine = State()
    finish = State()