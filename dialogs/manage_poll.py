import random
import string
from contextlib import suppress
from pathlib import Path

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import User, Message, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Column, Button, Select, Radio, ManagedRadio
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format, Const, List

from config_data.bot_conf import get_my_loggers, BASE_DIR
from database.db import Question, Victorine
from services.db_func import get_questions, get_all_victorines, get_victorine_from_id, \
    get_question_from_id, delete_question, create_question, get_or_create_victorine
from states.poll import PollManageSG, StartSG

logger, err_log = get_my_loggers()
router = Router()


async def manage_poll_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'manage_poll_getter start',  dialog_data=data)
    # Кортежи для select
    victorine_items = []
    victorine: Victorine = data.get('victorine')
    question_items = []
    photo_is_present = None
    photo = None
    if victorine:
        victorine = get_victorine_from_id(victorine.id)
        photo = victorine.image
        if victorine.image:
            img_path = BASE_DIR / victorine.image

            photo_is_present = img_path.exists()
        for question in victorine.questions:
            question_items.append((f'{question.id} {question.question}', question.id))
    for victorine_item in get_all_victorines():
        victorine_items.append((victorine_item.name, victorine_item.id))

    result = {'username': event_from_user.username, 'q_count': get_questions(), 'victorine_items': victorine_items,
            'victorine': victorine, 'photo_is_present': photo_is_present, 'photo': photo,
            'question_items': question_items
            }
    logger.debug(f'manage_poll_getter result:', **result)
    return result


#  Обработка выбора викторины
async def victorine_selected_click(callback: CallbackQuery, widget: Select,
                            dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    logger.debug(f'victorine_selected_click', callback=callback.data, dialog_data=data, item_id=item_id)
    victorine: Victorine = get_victorine_from_id(item_id)
    dialog_manager.dialog_data.update(victorine=victorine)
    await dialog_manager.switch_to(state=PollManageSG.victorine_edit)


async def question_selected_click(callback: CallbackQuery, widget: Select,
                            dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    logger.debug(f'question_selected_click', callback=callback.data, dialog_data=data, item_id=item_id)
    # Кортежи для select
    question = get_question_from_id(item_id)
    data.update(question=question)
    # Предварительное нажатие правтльного ответа
    # radio: ManagedRadio = dialog_manager.find('correct_answer_radio')
    await dialog_manager.switch_to(PollManageSG.question_edit)
    # return {'question_items': question_items}


async def delete_question_click(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'delete_question_click', callback=callback.data, dialog_data=data)
    q = data.get('question')
    delete_question(q.id)
    await dialog_manager.switch_to(PollManageSG.victorine_edit)
    await callback.answer('Удален')


async def manage_question_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'manage_question_getter',  dialog_data=data)
    question: Question = data.get('question')
    question = get_question_from_id(question.id)
    data.update(question=question)
    answer_list = [answer for answer in question.get_answers()]
    answer_list_tuple = [(answer, num) for num, answer in enumerate(question.get_answers(), 1)]
    # Предварительное нажатие правтльного ответа
    radio: ManagedRadio = dialog_manager.find('correct_answer_radio')
    correct_num = question.correct_answer
    is_checked = radio.get_checked()
    # if not is_checked:
    await radio.set_checked(correct_num)

    result = {'question': question, 'answer_list': answer_list, 'answer_list_tuple': answer_list_tuple,
              'not_full': question.is_not_full(), 'not_empty': answer_list}
    logger.debug(f'manage_question_getter result:', **result)
    return result


async def switch_to_victorine_edit(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'switch_to_victorine_edit', callback=callback.data, dialog_data=data)
    await dialog_manager.switch_to(PollManageSG.victorine_edit)


async def switch_to_victorine_select(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'switch_to_victorine_select', callback=callback.data, dialog_data=data)
    await dialog_manager.start(state=PollManageSG.start, mode=StartMode.NORMAL)


async def add_answer_click(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'add_answer_click', callback=callback.data, dialog_data=data)
    await dialog_manager.switch_to(PollManageSG.answer_add)


async def to_del_answer_click(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    logger.debug(f'to_del_answer_click', callback=callback.data, dialog_data=data)
    await dialog_manager.switch_to(PollManageSG.answer_del)


async def correct_answer_click(callback: CallbackQuery, radio: ManagedRadio,  dialog_manager: DialogManager, *args, **kwargs):
    logger.debug('correct_answer_click')
    data = dialog_manager.dialog_data
    print(f'radio widget checked: {radio.get_checked()}')
    finded_r = dialog_manager.find('correct_answer_radio')
    print('finded_r', finded_r.get_checked())
    logger.debug(f'correct_answer_click end', callback=callback.data, dialog_data=data, radio=radio.get_checked())


async def correct_answer_changed(callback: CallbackQuery, radio: ManagedRadio,  dialog_manager: DialogManager, *args, **kwargs):
    logger.debug('correct_answer_changed')
    data = dialog_manager.dialog_data
    question: Question = data.get('question')
    question.set('correct_answer', int(radio.get_checked()))


# Добавление нового ответа в вопрос
async def add_new_answer(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'add_new_answer', text=text, dialog_data=data)
    question: Question = data.get('question')
    try:
        question.add_answer(text)
        await message.answer('Добавлено')
    except AttributeError as err:
        await message.answer(text=f'{err}')
    await dialog_manager.back()


async def delete_selected_answer_click(callback: CallbackQuery, select: Select,  dialog_manager: DialogManager, item_id, *args, **kwargs):
    logger.debug('delete_selected_answer_click')
    data = dialog_manager.dialog_data
    print(select.text)
    print(item_id)
    question: Question = data.get('question')
    if question.get_answer_count() < 3:
        await callback.answer('Минимум 2 вопроса')
        await dialog_manager.switch_to(PollManageSG.question_edit)
        return

    question.delete_answer_from_question(item_id)
    logger.debug(f'correct_answer_click end', callback=callback.data, dialog_data=data)


async def add_question_to_victorine_click(callback: CallbackQuery, button: Button,  dialog_manager: DialogManager):
    # Добавление нового вопроса
    logger.debug('add_question_to_victorine')
    await dialog_manager.switch_to(PollManageSG.add_question_name)


# Добавление нового ответа в вопрос
async def create_new_question(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'create_new_question', text=text, dialog_data=data)
    data.update(question_text=text)
    await dialog_manager.next()


async def create_answer1(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'create_answer1', text=text, dialog_data=data)
    data.update(answer1=text)
    await dialog_manager.next()


async def create_answer2(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'create_answer1', text=text, dialog_data=data)
    answer2=text
    data.update(answer2=answer2)
    victorine = data.get('victorine')
    question_text = data.get('question_text')
    answer1 = data.get('answer1')
    try:
        new_question = create_question(victorine.id, question_text, answer1, answer2)
        await message.answer(f'Новый вопрос создан:\n{new_question}\n\nНе забудьте указать правильный ответ')
        data.update(question=new_question)
        await dialog_manager.switch_to(PollManageSG.question_edit)

    except Exception as err:
        await message.answer(f'Произошла ошибка: {err}')
        logger.error(err)


async def close_second_dialog(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    logger.debug('close_second_dialog')
    await dialog_manager.start(state=StartSG.start)


async def victorine_new_name(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'victorine_new_name', text=text, dialog_data=data)
    victorine = data.get('victorine')
    try:
        victorine.set('name', text.strip())
        await message.answer('Имя изменено')
        await dialog_manager.switch_to(PollManageSG.victorine_edit)
    except Exception as err:
        await message.answer(f'Ошибка: {err}')


async def victorine_new_description(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'victorine_new_description', text=text, dialog_data=data)
    victorine = data.get('victorine')
    try:
        victorine.set('description', text.strip())
        await message.answer('Описание изменено')
        await dialog_manager.switch_to(PollManageSG.victorine_edit)
    except Exception as err:
        await message.answer(f'Ошибка: {err}')


async def send_image(message: Message, widget: MessageInput, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'send_image', dialog_data=data)
    victorine = data.get('victorine')
    file = message.photo[-1]
    temp = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
    img_path = Path('media') / f'victorine_{victorine.id}_{temp}.jpg'
    print(img_path)
    await message.bot.download(file, destination=img_path)
    if victorine.image:
        with suppress(FileNotFoundError):
            old_path = BASE_DIR / Path(victorine.image)
            if not 'no_image.jpg' in old_path.as_posix():
                old_path.unlink()
    victorine.set('image', img_path.as_posix())
    await dialog_manager.switch_to(PollManageSG.victorine_edit)


async def input_name(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'input_name', text=text, dialog_data=data)
    data.update(new_name=text.strip())
    await dialog_manager.next()


async def input_description(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'input_description', text=text, dialog_data=data)
    data.update(description=text.strip())
    await dialog_manager.next()


# async def input_duration(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
#     try:
#         data = dialog_manager.dialog_data
#         logger.debug(f'input_duration', text=text, dialog_data=data)
#         duration = int(text)
#         data.update(duration=duration)
#         await dialog_manager.next()
#     except Exception as err:
#         logger.error(err)


def duration_check(text: str):
    try:
        duration = int(text)
        return text
    except Exception as err:
        raise ValueError


async def error_duration_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Вы ввели некорректое число. Попробуйте еще раз'
    )

async def create_new_victorine(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'create_new_victorine', text=text, dialog_data=data)
    name = data.get('new_name')
    duration_hour = int(text)
    description = data.get('description')
    new_victorine = await get_or_create_victorine(name, description, duration_hour)
    await message.answer(f'Викторина <b>{new_victorine.name}</b> создана')
    await dialog_manager.next()
    await dialog_manager.switch_to(PollManageSG.start)



async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


async def to_question_edit(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(PollManageSG.question_edit)


async def to_victorine_create(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(PollManageSG.create_victorine_new_name)


async def to_victorine_rename(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(PollManageSG.victorine_rename)


async def to_victorine_change_description(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(PollManageSG.victorine_edit_description)


async def to_add_image(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(PollManageSG.add_image)

manage_poll_dialog = Dialog(
    Window(
        Const(text='Управление викторинами'),
        Format(text='{q_count}'),
        Column(
            Select(
                Format('{item[0]}'),
                id='victorine',
                item_id_getter=lambda x: x[1],
                items='victorine_items',
                on_click=victorine_selected_click)
        ),
        Button(text=Const('Добавить викторину'),
               id='new_victorine',
               on_click=to_victorine_create),
        Button(text=Const('Главное меню'),
               id='go_to_start',
               on_click=close_second_dialog),
        state=PollManageSG.start,
        getter=manage_poll_getter,
    ),

    Window(
        Format(text='Введите имя викторины'),
        TextInput(
            id='new_victorine_name',
            on_success=input_name,
        ),
        state=PollManageSG.create_victorine_new_name,
        getter=manage_poll_getter,
    ),

    Window(
        Format(text='Введите описание викторины'),
        TextInput(
            id='new_victorine_description',
            on_success=input_description,
            on_error=error_duration_handler,
        ),
        state=PollManageSG.victorine_description,
        getter=manage_poll_getter,
    ),

    Window(
        Format(text='Введите продолжительность викторины в часах'),
        TextInput(
            id='new_victorine_create',
            type_factory=duration_check,
            on_success=create_new_victorine,
            on_error=error_duration_handler,
        ),
        state=PollManageSG.create_victorine,
        getter=manage_poll_getter,
    ),


    Window(
        StaticMedia(
            path=Format('{photo}'),
            type=ContentType.PHOTO,
            when='photo_is_present'
        ),
        Format(text='Управление викториной <b>"{victorine.name}</b>"\n'),
        Format(text='\n{victorine.description}\n'),
        Format(text='{victorine}'),
        Column(
            Select(
                Format('{item[0]}'),
                id='answer',
                item_id_getter=lambda x: x[1],
                items='question_items',
                on_click=question_selected_click,
            ),
        ),
        Button(text=Const('Изменить описание викторины'),
               id='victorine_change_description',
               on_click=to_victorine_change_description),
        Button(text=Const('Переименовать викторину'),
               id='victorine_rename',
               on_click=to_victorine_rename),
        Button(text=Const('Изменить изображение'),
               id='image_add',
               on_click=to_add_image),
        Button(text=Const('Добавить вопрос в викторину'),
               id='add_question',
               on_click=add_question_to_victorine_click),
        Button(text=Const('Назад'),
               id='victorine_select',
               on_click=switch_to_victorine_select),
        state=PollManageSG.victorine_edit,
        getter=manage_poll_getter,
    ),
    Window(
        Const(text='Пришлите изображение'),
        MessageInput(
            func=send_image,
            content_types=[ContentType.PHOTO]
        ),
        state=PollManageSG.add_image,
        getter=manage_poll_getter,
    ),
    Window(
        Format(text='Введите новое имя викторины {victorine.name}'),
        TextInput(
            id='new_name',
            on_success=victorine_new_name,
        ),
        state=PollManageSG.victorine_rename,
        getter=manage_poll_getter,
    ),
    Window(
        Format(text='Введите новое описание викторины {victorine.name}'),
        TextInput(
            id='new_description',
            on_success=victorine_new_description,
        ),
        state=PollManageSG.victorine_edit_description,
        getter=manage_poll_getter,
    ),
    Window(
        Format(text='Редактирование вопроса викторины\n'),
        Format(text='{question}'),
        List(field=Format('{item}'),
             items='answer_list'),
        Column(
            Radio(
                checked_text=Format('[✔️] {item[0]}'),
                unchecked_text=Format('[  ] {item[0]}'),
                id='correct_answer_radio',
                item_id_getter=lambda x: x[1],
                items="answer_list_tuple",
                on_click=correct_answer_click,
                on_state_changed=correct_answer_changed,
            ),
        ),
        Button(text=Const('Добавить вариант ответа'),
               id='add_answer',
               on_click=add_answer_click,
               when='not_full'),
        Button(text=Const('Удалить вариант ответа'),
               id='del_answer',
               on_click=to_del_answer_click,
               when='not_empty'),
        Button(text=Const('Удалить весь вопрос'),
               id='delete_question',
               on_click=delete_question_click),
        Button(text=Const('Назад'),
               id='victorine_edit',
               on_click=switch_to_victorine_edit),
        state=PollManageSG.question_edit,
        getter=manage_question_getter,
    ),
    Window(
        Const(text='Введите текст ответа'),
        TextInput(
            id='answer_input',
            on_success=add_new_answer,
        ),
        state=PollManageSG.answer_add,
    ),
    Window(
        Const(text='Выберите ответ для удаления'),
        List(field=Format('{item}'),
             items='answer_list'),
        Column(
            Select(
                Format('{item[0]}'),
                id='answer_to_delete',
                item_id_getter=lambda x: x[1],
                items='answer_list_tuple',
                on_click=delete_selected_answer_click,
            ),
        ),
        Button(text=Const('Назад'),
               id='go_back',
               on_click=to_question_edit,
               ),
        state=PollManageSG.answer_del,
        getter=manage_question_getter,
    ),
    Window(
        Const(text='Введите новый вопрос'),
        TextInput(
            id='new_qestion_add',
            on_success=create_new_question,
        ),
        state=PollManageSG.add_question_name,
    ),
    Window(
        Const(text='Введите первый варинат ответа'),
        TextInput(
            id='answer1_add',
            on_success=create_answer1,
        ),
        state=PollManageSG.add_answer1,
    ),
    Window(
        Const(text='Введите  второй вариант ответа'),
        TextInput(
            id='answer2_add',
            on_success=create_answer2,
        ),
        state=PollManageSG.add_answer2,
    ),
)


# async def manage_victorine_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
#     data = dialog_manager.dialog_data
#     logger.info(f'manage_victorine_getter dialog_data: {data}')
#     return {'username': event_from_user.username, 'q_count': get_questions(),}
#
# manage_victorine_dialog = Dialog(
#     Window(
#         Format(text='Управление викториной {victorine.name}'),
#         state=PollManageSG.victorine_edit,
#         getter=manage_victorine_getter,
#     )
# )
#
