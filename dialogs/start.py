from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format, Const

from config_data.bot_conf import get_my_loggers, config
from dialogs.manage_poll import send_image
from services.db_func import get_questions, create_victorine_from_gtable, get_victorine, is_first_poll, \
    get_or_create_user
from states.poll import StartSG, PollSG, PollManageSG, LaunchVictorineSG

logger, err_log = get_my_loggers()


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        self.admins = config.tg_bot.admin_ids

    async def __call__(self, event_from_user: User) -> bool:
        logger.debug(f'Проверка на админа\n'
                     f'{event_from_user.id} in {self.admins}: {str(event_from_user.id) in self.admins}')
        return str(event_from_user.id) in self.admins


router = Router()


async def start_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    # print(kwargs.keys())
    # print(event_update)
    is_admin = await IsAdmin()(event_from_user)
    data = dialog_manager.dialog_data
    logger.debug('start_getter', dialog_data=data)
    active_victorine = get_victorine()
    if active_victorine:
        start_victorine_text = active_victorine.name
    else:
        start_victorine_text = 'активных викторин нет'
    return {'username': event_from_user.username, 'q_count': get_questions(), 'is_admin': is_admin,
            'start_victorine_text': start_victorine_text}


# Начать учавствовать в викторине
async def button_start_poll(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.info(f'button_start_poll', callback=callback.data, dialog_data=data,)
    dialog_manager.dialog_data.update(questions=get_questions())

    # Если есть викторина и еще не проходил то начинаем
    victorine = get_victorine()
    if victorine:
        if is_first_poll(get_or_create_user(callback.from_user), victorine.name):
            dialog_manager.dialog_data.update(questions=get_questions())
            await dialog_manager.start(state=PollSG.poll, mode=StartMode.NORMAL, show_mode=ShowMode.EDIT)
            logger.info(f'button_start_poll end {dialog_manager.dialog_data}')
        else:
            await callback.message.answer('Вы уже проходили эту викторину')

    else:
        await callback.message.answer('Активных викторин нет')


async def refresh_poll(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.info(f'callback.data: {callback.data}')
    await create_victorine_from_gtable()
    await callback.message.answer('Викторина обновлена')
    await dialog_manager.start(state=StartSG.start, mode=StartMode.NORMAL)


async def start_manage_poll_dialog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.info(f'start_manage_poll_dialog', callback=callback.data,  dialog_data=data,)
    await dialog_manager.start(state=PollManageSG.start)


async def launch_control_menu(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.info(f'start_manage_poll_dialog', callback=callback.data,  dialog_data=data,)
    await dialog_manager.start(state=LaunchVictorineSG.select, mode=StartMode.NORMAL)


async def no_text(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    print(type(widget))
    print(message.bot)
    photo = message.photo
    file = photo[-1]
    print(file)
    await message.bot.download(file, 'xxx.jpg')

    await message.answer(text='Вы ввели вообще не текст!')


start_dialog = Dialog(
    Window(
        Const(text='Начальное меню'),
        Format(text='Активная викторина: {start_victorine_text}'),
        MessageInput(
            func=no_text,
            content_types=[ContentType.PHOTO]
        ),
        Button(text=Const('Пройти викторину'),
               id='start_poll',
               on_click=button_start_poll),
        Button(text=Const('Обновить викторину'),
               id='refresh_poll',
               on_click=refresh_poll,
               when='is_admin'),
        Button(text=Const('Запуск/остановка викторин'),
               id='launch_control',
               on_click=launch_control_menu,
               when='is_admin'),
        Button(text=Const('Управление викторинами'),
               id='manage_poll',
               on_click=start_manage_poll_dialog,
               when='is_admin'),
        state=StartSG.start,
        getter=start_getter,
    ),
)



