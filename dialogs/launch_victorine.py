import datetime

from aiogram import Router
from aiogram.types import User, CallbackQuery, FSInputFile
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Column, Button, Select
from aiogram_dialog.widgets.text import Format, Const

from config_data.bot_conf import get_my_loggers, config, BASE_DIR
from database.db import Victorine
from dialogs.manage_poll import go_back
from keyboards.keyboards import begin_kb
from services.db_func import get_all_victorines, get_victorine_from_id
from states.poll import LaunchVictorineSG

logger, err_log = get_my_loggers()
router = Router()


#  Обработка нажатия кнопки запуска/останова викторин
async def control_button_click(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    logger.debug(f'control_button_click', callback=callback.data, item_id=item_id)
    victorine = get_victorine_from_id(item_id)
    data.update(victorine=victorine)
    await dialog_manager.next()


async def get_launch_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    data = dialog_manager.dialog_data
    logger.info(f'get_topics_getter dialog_data: {data}')
    # Кортежи для select
    victorine_items = []
    is_active = False
    victorine: Victorine = data.get('victorine')
    if victorine:
        victorine = get_victorine_from_id(victorine.id)
        is_active = victorine.is_active
        #     for question in victorine.questions:
    #         question_items.append((f'{question.id} {question.question}', question.id))
    all_victorines = get_all_victorines()
    for victorine_item in all_victorines:
        sym = '✳️' if victorine_item.is_active else ''
        victorine_items.append((f'{victorine_item.name} {sym}', victorine_item.id))

    actives = sum([v.is_active for v in all_victorines])
    # Можно стартануть если нет запущенных
    start_ready = actives == 0

    result = {
        # 'username': event_from_user.username,
        # 'q_count': get_questions(),
        'victorine_items': victorine_items,
        'victorine': victorine,
        'start_ready': start_ready,
        'is_active': is_active
        # 'photo': victorine.image if victorine else '',
        # 'question_items': question_items
            }
    logger.debug(f'manage_poll_getter result:', **result)
    return result


async def launch_victorine_click(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    """Запуск викторины
    Активная только одна. Запуск только если остальные выключены.

    """
    data = dialog_manager.dialog_data
    logger.debug(f'launch_victorine_click', callback=callback.data, dialog_data=data)
    victorine = data.get('victorine')
    logger.debug(f'{config.tg_bot.GROUP_ID}')
    img_path = victorine.image
    if img_path:
        try:
            old_msg_id = victorine.msg_id
            await callback.bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=old_msg_id, reply_markup=None)
        except Exception as err:
            logger.error(err)
        image = FSInputFile(BASE_DIR / img_path)
        text = victorine.description
        msg = await callback.bot.send_photo(chat_id=config.tg_bot.GROUP_ID, photo=image, caption=text, reply_markup=begin_kb)
        victorine.set('is_active', 1)
        victorine.set('victorine_stop_time', datetime.datetime.now() + datetime.timedelta(victorine.duration_hour))
        victorine.set('msg_id', msg.message_id)
    else:
        await callback.message.answer('Нет изображения в викторине')


async def stop_victorine(bot, victorine):
    try:
        victorine.set('is_active', 0)
        msg_id = victorine.msg_id
        if msg_id:
            await bot.edit_message_reply_markup(chat_id=config.tg_bot.GROUP_ID, message_id=msg_id,
                                                reply_markup=None)
    except Exception as err:
        logger.error(err)


async def stop_victorine_click(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'stop_victorine_click', callback=callback.data, dialog_data=data)
    victorine = data.get('victorine')
    await stop_victorine(callback.bot, victorine)
    await callback.message.answer('Викторина остановлена')


async def done(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()

launch_stop_victorine_dialog = Dialog(
    Window(
        Const(text='Запуск и останов викторин'),
        Format(text=''),
        Column(
            Select(
                Format('{item[0]}'),
                id='answer',
                item_id_getter=lambda x: x[1],
                items='victorine_items',
                on_click=control_button_click)
        ),
        Button(text=Const('Назад'),
               id='done',
               on_click=done),
        state=LaunchVictorineSG.select,
        getter=get_launch_getter,
    ),
    Window(
        Const(text='Текущая викторина'),
        Format(text='{victorine.name}'),
        Const(text='✳', when='is_active'),
        Button(text=Const('Запустить викторину'),
               id='launch',
               on_click=launch_victorine_click,
               when='start_ready'
               ),
        Button(text=Const('Остановить викторину'),
               id='stop',
               on_click=stop_victorine_click,
               when='is_active'
               ),
        Button(text=Const('Назад'),
               id='back',
               on_click=go_back),
        state=LaunchVictorineSG.control,
        getter=get_launch_getter,
    ),
)