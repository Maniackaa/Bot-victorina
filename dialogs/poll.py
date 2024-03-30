from aiogram import Router
from aiogram.types import User, Message, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Column, Multiselect, Button, Select
from aiogram_dialog.widgets.text import Format, Const

from config_data.bot_conf import get_my_loggers
from database.db import Question, Victorine
from services.db_func import get_questions, get_victorine
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
        victorine = get_victorine('testvict')
        questions = victorine.questions
        data.update(victorine=victorine, questions=questions)
        logger.info('Опрос началcся', victorine=victorine, questions=questions)
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
        'answer1': current_question.answer1,
        'answer2': current_question.answer2,
        'answer3': current_question.answer3,
        'answer4': current_question.answer4,
        'answer5': current_question.answer5,
        'answers_items': answers_items
        }
    return question_data


# Обработка результатов
async def result_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    data = dialog_manager.dialog_data
    logger.info(f'result_getter dialog_data: {data}')
    victorine: Victorine = data.get('victorine')
    all_questions = victorine.questions
    answers_num = data.get('answers_num')
    result_text = ''
    for i, answer_num in enumerate(answers_num):
        question = all_questions[i]
        answer_text = question[answer_num]
        result_text += f'''
Вопрос:\n{question.question}.\nВаш ответ: {answer_text}.\n{"<b>Верно</b>"
if question.check_answer(answer_num) else f"<b>Не верно!</b> Правильный ответ: {question.get_correct_answer()}"}\n\n'''
        logger.debug(f'{question}, {answer_text} {answer_num} {answer_text}'
                     f' {"Верно" if question.check_answer(answer_num) else f"Не верно!"}')
    result_text += f'Вы набрали {victorine.get_score(answers_num)} баллов!'
    logger.info(f'Результаты опроса: {data}')
    return {'result_text': result_text}


poll_dialog = Dialog(
    Window(
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