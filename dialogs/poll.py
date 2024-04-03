from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.types import User, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Column, Select
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format, Const

from config_data.bot_conf import get_my_loggers
from database.db import Question, Victorine
from dialogs.launch_victorine import stop_victorine
from services.db_func import get_victorine, get_or_create_user, is_first_poll, save_result
from services.google_func import write_to_table, load_free_coupons
from states.poll import PollSG

logger, err_log = get_my_loggers()
router = Router()


#  Обработка нажатия кнопки ответа
async def poll_button_click(callback: CallbackQuery, widget: Select,
                            dialog_manager: DialogManager, item_id: str):
    logger.debug(f'poll_button_click', callback=callback.data, item_id=item_id)
    data = dialog_manager.dialog_data
    q_num = data.get('q_num')
    victorine = data['victorine']
    all_questions = victorine.questions
    if q_num >= victorine.count():
        # Обработка результатов
        await callback.message.delete_reply_markup()
        await callback.message.answer('Производится обработка результатов')

        await dialog_manager.next()
    answers_num = data.get('answers_num', [])
    answers_num.append(item_id)
    data.update(answers_num=answers_num)
    current_question: Question = all_questions[q_num - 1]
    curent_answer = current_question[int(item_id)]
    logger.debug(f'Сохранен ответ на вопрос № {q_num}: {all_questions[q_num - 1].question}.'
                 f' Ответ:({item_id}) {curent_answer}')


# Подготовка данных окна вопроса
async def get_topics_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    data = dialog_manager.dialog_data
    logger.info(f'get_topics_getter dialog_data: {data}')
    q_num = data.get('q_num', 0)
    if q_num == 0:
        # Подготовка опроса
        victorine = get_victorine()
        questions = victorine.questions
        data.update(victorine=victorine, questions=questions)
        logger.info('Опрос начался', victorine=victorine, questions=questions)
    victorine = data['victorine']
    all_questions = victorine.questions
    current_question: Question = all_questions[q_num]
    logger.info(f"{q_num + 1}й вопрос: {current_question.question}")
    # Кортежи для select
    answers_items = []
    for num, answer_text in enumerate(current_question.get_answers(), 1):
        answers_items.append((answer_text, num))
    data.update(q_num=q_num + 1)
    logger.debug(f'answers_items: {answers_items}')
    question_data = {
        'your_question': current_question.question,
        'answers_items': answers_items,
        'q_num': q_num + 1,
        'count': victorine.count(),
        'photo': victorine.image
        }
    return question_data


def get_answer_text(question, answer_text, answer_num):
    result_text = f'''
Вопрос:\n{question.question}.\nВаш ответ: {answer_text}.\n{"<b>Верно</b>"
if question.check_answer(answer_num) else f"<b>Не верно!</b> Правильный ответ: {question.get_correct_answer_text()}"}\n\n'''
    return result_text


# Обработка результатов
async def result_getter(dialog_manager: DialogManager, event_update, event_from_user: User, bot: Bot, **kwargs):
    data = dialog_manager.dialog_data
    logger.info(f'result_getter dialog_data: {data}')
    victorine: Victorine = data.get('victorine')
    all_questions = victorine.questions
    answers_num = data.get('answers_num')
    window_text = ''

    for i, answer_num in enumerate(answers_num):
        question = all_questions[i]
        answer_text = question[answer_num]
        window_text += get_answer_text(question, answer_text, answer_num)
        logger.debug(f'{question}, {answer_text} {answer_num} {answer_text}'
                     f' {"Верно" if question.check_answer(answer_num) else f"Не верно!"}')
    score = victorine.get_score(answers_num)
    window_text += f'Вы набрали {score} баллов!'
    user = get_or_create_user(event_from_user)
    # Если первый раз
    if is_first_poll(get_or_create_user(event_from_user), victorine.name):
        # await bot.send_message(chat_id=event_from_user.id, text='Первая')
        coupons = await load_free_coupons(victorine.name)

        for coupon in coupons:
            if coupon.score <= score:
                await bot.send_message(chat_id=event_from_user.id,
                                       text=f'Вы выиграли купон на скидку {coupon.discont}%! <code>{coupon.code}</code>')
                if len(coupons) <= 1:
                    await stop_victorine(bot, victorine)
                await write_to_table(rows=[[f'Выиграл {event_from_user.username or event_from_user.id}']],
                                     start_row=coupon.id + 1, delta_col=5, sheets_num=2)
                break

    else:
        await bot.send_message(chat_id=event_from_user.id, text='Вы уже учавствовали в этой викторине.')
    result = save_result(user, victorine, window_text)
    await write_to_table([[user.username or user.id, victorine.name, score, window_text]], sheets_num=1, insert_rows=1)
    logger.info(f'Результаты опроса: {data}')
    return {'result_text': window_text}


poll_dialog = Dialog(
    Window(
        StaticMedia(
            path=Format('{photo}'),
            type=ContentType.PHOTO,
            when='photo'
        ),
        Format(text='Вопрос № {q_num}/{count}.'),
        Format(text='{your_question}'),
        Column(
            Select(
                Format('{item[0]}'),
                id='answer',
                item_id_getter=lambda x: x[1],
                items='answers_items',
                on_click=poll_button_click)
        ),
        state=PollSG.poll,
        getter=get_topics_getter,
    ),
    Window(
        Const(text='Результаты опроса'),
        Format(text='{result_text}'),
        state=PollSG.finish,
        getter=result_getter,
    ),
)