from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, ErrorEvent, ReplyKeyboardRemove
from aiogram_dialog import DialogManager, StartMode, ShowMode
from config_data.bot_conf import get_my_loggers
from dialogs.launch_victorine import launch_stop_victorine_dialog
from dialogs.manage_poll import manage_poll_dialog
from dialogs.poll import poll_dialog
from dialogs.start import start_dialog

from services.db_func import get_or_create_user
from states.poll import StartSG

router = Router()

logger, err_log = get_my_loggers()


router.include_router(start_dialog)
router.include_router(poll_dialog)
router.include_router(manage_poll_dialog)
router.include_router(launch_stop_victorine_dialog)


@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager, bot: Bot):
    print(bot, message.bot)
    user = get_or_create_user(message.from_user)
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)
    logger.info('Старт', user=user)


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    # Example of handling UnknownIntent Error and starting new dialog.
    logger.error("Restarting dialog: %s", event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass  # whatever
    elif event.update.message:
        await event.update.message.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
            reply_markup=ReplyKeyboardRemove(),
        )
    await dialog_manager.start(
        StartSG.start,
        mode=StartMode.NORMAL,
        show_mode=ShowMode.SEND,
    )