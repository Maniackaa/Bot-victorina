from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import User, Message, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Column, Multiselect, Button, Select
from aiogram_dialog.widgets.text import Format, Const

from config_data.bot_conf import get_my_loggers
from services.db_func import get_or_create_user, get_questions
from states.poll import StartSG, PollSG

logger, err_log = get_my_loggers()
router = Router()


async def start_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    return {'username': event_from_user.username, 'q_count': len(get_questions())}


async def button_start_poll(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.info(f'callback.data: {callback.data}')
    dialog_manager.dialog_data.update(questions=get_questions())
    await dialog_manager.start(state=PollSG.poll, mode=StartMode.RESET_STACK)
    dialog_manager.dialog_data.update(questions=get_questions())
    logger.info(f'button_start_poll end {dialog_manager.dialog_data}')

start_dialog = Dialog(
    Window(
        Const(text='Начальное меню'),
        Format(text='Всего вопросов в базе: {q_count}'),
        Button(text=Const('Начать опрос'),
               id='start_poll',
               on_click=button_start_poll),
        state=StartSG.start,
        getter=start_getter,
    ),
)



