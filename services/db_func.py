import asyncio
import datetime

from sqlalchemy import select, delete

from config_data.bot_conf import get_my_loggers
from database.db import Session, User, Question, Victorine

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
        user = session.execute(q).scalars().one_or_none()
        return user


def get_victorine(name) -> Victorine:
    session = Session(expire_on_commit=False)
    with session:
        q = select(Victorine).where(Victorine.name == name)
        result = session.execute(q).scalars().first()
        return result

def get_questions() -> list[Question]:
    session = Session(expire_on_commit=False)
    with session:
        q = select(Question)
        result = session.execute(q).scalars().all()
        return result

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


def delete_company(user_id, name):
    with Session(expire_on_commit=False) as session:
        q = delete(Company).where(Company.user_id == user_id, Company.name == name).returning(Company.id)
        result = session.execute(q).fetchall()
        session.commit()
        return result


def update_user(user: User, data: dict):
    try:
        logger.debug(f'Обновляем {user}: {data}')
        session = Session()
        with session:
            user: User = session.query(User).filter(User.id == user.id).first()
            for key, val in data.items():
                setattr(user, key, val)
            session.commit()
            logger.debug(f'Юзер обновлен {user}')
    except Exception as err:
        err_log.error(f'Ошибка обновления юзера {user}: {err}')


if __name__ == '__main__':
    delete_company(1, '23124124')
    pass
