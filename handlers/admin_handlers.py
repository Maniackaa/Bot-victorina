from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import User, Message, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from config_data.bot_conf import get_my_loggers
from dialogs.poll import poll_dialog
from dialogs.start import start_dialog

from services.db_func import get_or_create_user, get_questions
from states.poll import StartSG

router = Router()

logger, err_log = get_my_loggers()


router.include_router(start_dialog)
router.include_router(poll_dialog)


@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager):
    user = get_or_create_user(message.from_user)
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)
    logger.info('Старт', user=user)

