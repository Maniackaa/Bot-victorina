import asyncio
import datetime

from sqlalchemy import select, delete, RowMapping
from config_data.bot_conf import get_my_loggers
from database.db import Session, User, Question, Victorine, Result
from services.google_func import load_range_values

logger, err_log = get_my_loggers()


def check_user(id):
    """Возвращает найденных пользователей по tg_id"""
    # logger.debug(f'Ищем юзера {id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(id)).one_or_none()
        # logger.debug(f'Результат: {user}')
        return user


def get_user_from_id(pk) -> User:
    session = Session(expire_on_commit=False)
    with session:
        q = select(User).filter(User.id == pk)
        print(q)
        user = session.execute(q).scalars().one_or_none()
        return user


def get_or_create_user(user) -> User:
    """Из юзера ТГ возвращает сущестующего User ли создает его"""
    try:
        tg_id = user.id
        username = user.username
        # logger.debug(f'username {username}')
        old_user = check_user(tg_id)
        if old_user:
            # logger.debug('Пользователь есть в базе')
            return old_user
        logger.debug('Добавляем пользователя')
        with Session() as session:
            new_user = User(tg_id=tg_id,
                            username=username,
                            register_date=datetime.datetime.now()
                            )
            session.add(new_user)
            session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        err_log.error('Пользователь не создан', exc_info=True)


def get_victorine(name=None) -> Victorine:
    """Возвращает викторину по имени
    Если имени нет, то первую активную
    """
    session = Session(expire_on_commit=False)
    with session:
        if name:
            q = select(Victorine).where(Victorine.name == name)
        else:
            q = select(Victorine).where(Victorine.is_active)
        result = session.execute(q).scalars().first()
        return result


def get_victorine_from_id(pk) -> Victorine:
    session = Session(expire_on_commit=False)
    with session:
        q = select(Victorine).where(Victorine.id == pk)
        result = session.execute(q).scalars().one_or_none()
        return result


def get_question_from_id(pk) -> Question:
    session = Session(expire_on_commit=False)
    with session:
        q = select(Question).where(Question.id == pk)
        result = session.execute(q).scalars().one_or_none()
        return result


def get_all_victorines():
    session = Session(expire_on_commit=False)
    with session:
        q = select(Victorine)
        result = session.execute(q).scalars().all()
        return result


def get_questions() -> list[Question]:
    session = Session(expire_on_commit=False)
    with session:
        q = select(Victorine)
        result = session.execute(q).scalar()
        if result:
            return result.count()


async def get_or_create_victorine(name, description=None) -> RowMapping | Victorine:
    try:
        session = Session()
        with session:
            q = select(Victorine).where(Victorine.name == name)
            result = session.execute(q).scalars().one_or_none()
            logger.debug(f'result: {result}')
            if result:
                logger.debug(f'Викторина уже есть в базе: {result}')
                return result
            new_victorine = Victorine(name=name, description=description)
            session.add(new_victorine)
            session.commit()
            logger.debug(f'Витокрина создана: {new_victorine}')
            return new_victorine
    except Exception as err:
        logger.error(err)


def delete_victorine_questions(victorine: Victorine):
    try:
        session = Session()
        with session:
            q = delete(Question).where(Question.victorine == victorine)
            logger.debug(q)
            session.execute(q)
            session.commit()
    except Exception as err:
        logger.error(err)


def delete_question(pk):
    try:
        session = Session()
        with session:
            q = delete(Question).where(Question.id == pk)
            logger.debug(q)
            session.execute(q)
            session.commit()
    except Exception as err:
        logger.error(err)


def delete_instanse_from_id(Instance, pk):
    try:
        session = Session()
        with session:
            q = delete(Instance).where(Instance.id == pk)
            logger.debug(q)
            session.execute(q)
            session.commit()
    except Exception as err:
        logger.error(err)


def create_victorine(name, image=None):
    session = Session(expire_on_commit=False)
    with session:
        new_victorina = Victorine(name=name, image=image)
        session.add(new_victorina)
        session.commit()
        return new_victorina


def create_question(victorine_id, question_text, answer1, answer2, answer3=None, answer4=None, answer5=None):
    session = Session(expire_on_commit=False)
    with session:
        new_question = Question(
            victorine_id=victorine_id,
            question=question_text,
            correct_answer=1,
            answer1=answer1,
            answer2=answer2,
            answer3=answer3,
            answer4=answer4,
            answer5=answer5,
        )
        session.add(new_question)
        session.commit()
        return new_question


async def create_victorine_from_gtable():
    try:
        values = await load_range_values(diap='A:G')
        logger.debug(f'{values}')
        name = values[0][0]
        decription = values[0][1]
        # name = 'from_table'
        logger.debug(name)
        my_victorine = await get_or_create_victorine(name, decription)
        delete_victorine_questions(my_victorine)
        logger.debug(f'{my_victorine}')
        session = Session(expire_on_commit=False)
        with session:
            objects = []
            for row in values[2:]:
                print(row)
                question = Question(
                    victorine_id=my_victorine.id,
                    question=row[0],
                    correct_answer=row[1],
                    answer1=row[2],
                    answer2=row[3],
                    answer3=row[4],
                    answer4=row[5],
                    answer5=row[6],
                )
                objects.append(question)
            session.bulk_save_objects(objects)
            session.commit()
    except Exception as err:
        logger.error(err)


def is_first_poll(user, name):
    session = Session(expire_on_commit=False)
    with session:
        q = select(Result).where(Result.user == user, Result.victorine_name == name)
        replay_poll = session.execute(q).scalar()
        return False if replay_poll else True


def save_result(user: User, victorine: Victorine, text):
    session = Session(expire_on_commit=False)
    with session:
        result = Result(victorine_id=victorine.id,
                        user_id=user.id,
                        result_text=text,
                        victorine_name=victorine.name)
        session.add(result)
        session.commit()
        return result

async def main():
    # test_victorine = await get_or_create_victorine('test')
    # print(test_victorine)
    # await create_victorine_from_gtable()
    # all_victorines = get_all_victorines()
    # print(all_victorines)
    # victorine = all_victorines[0]
    # res = create_question(victorine.id, 'question_text', 'answer1', 'answer2')
    # print(res)
    # print('-----------')
    # v = get_victorine()
    # print(v)
    user = get_user_from_id(1)
    print(user)
    fp = is_first_poll(user, 'testv3ict')
    print(fp)


if __name__ == '__main__':
    asyncio.run(main())

