import asyncio
import datetime
from typing import Sequence

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer, LargeBinary, BLOB, select, ARRAY, func, delete
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from config_data.bot_conf import config, get_my_loggers, tz, BASE_DIR

logger, err_log = get_my_loggers()

# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
db_path = BASE_DIR / 'base.sqlite'
db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def set(self, key, value):
        _session = Session(expire_on_commit=False)
        with _session:
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            logger.debug(f'Изменено значение {key} на {value}')
            return self


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=0)

    def __repr__(self):
        return f'{self.id}. {self.username or "-"} {self.tg_id}'


class Victorine(Base):
    __tablename__ = 'victorines'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    questions: Mapped[list['Question']] = relationship(back_populates='victorine',  lazy='selectin')

    def __repr__(self):
        return f'{self.__class__.__name__}({self.id}. {self.name}))'

    def count(self):
        return len(self.questions)

    def check_answers(self, answer_list: list[int]) -> list[bool]:
        """Возвращает список ответов"""
        if len(answer_list) != self.count():
            raise ValueError('Длина списка не соответсвует количеству вопросов')
        logger.debug(f'check_answers {answer_list}')
        result = []
        for index, question in enumerate(self.questions):
            answer_num = answer_list[index]
            is_correct = question.check_answer(answer_num)
            result.append(is_correct)
        return result

    def get_score(self, answer_list: list) -> int:
        return sum(self.check_answers(answer_list))


class Question(Base):
    """Вопрос. Нумерация ответов с 1"""
    __tablename__ = 'questions'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    victorine_id: Mapped[int] = mapped_column(ForeignKey('victorines.id', ondelete='CASCADE'))
    victorine: Mapped[Victorine] = relationship(back_populates="questions", lazy='selectin')
    question: Mapped[str] = mapped_column(String(1000), nullable=True, unique=True)
    answer1: Mapped[str] = mapped_column(String(100), nullable=False)
    answer2: Mapped[str] = mapped_column(String(100), nullable=False)
    answer3: Mapped[str] = mapped_column(String(100), nullable=True)
    answer4: Mapped[str] = mapped_column(String(100), nullable=True)
    answer5: Mapped[str] = mapped_column(String(100), nullable=True)
    correct_answer: Mapped[int] = mapped_column(Integer(), default=1)

    def get_answers(self):
        """Возвращает список из ответов"""
        _answers = []
        for index in range(1, 6):
            name = f'answer{index}'
            if hasattr(self, name):
                answer = getattr(self, name)
                if answer:
                    _answers.append(answer)
        return _answers

    def get_correct_answer(self) -> str:
        return getattr(self, f'answer{self.correct_answer}')

    def check_answer(self, answer_num) -> bool:
        """Проверяет ответ"""
        return self.correct_answer == int(answer_num)

    def __getitem__(self, item):
        """[1] вернет 1й вопрос"""
        try:
            item = int(item)
            name = f'answer{item}'
            if hasattr(self, name):
                return getattr(self, name)
        except ValueError:
            return None

    def __repr__(self):
        return f'{self.__class__.__name__}({self.id}. {self.question}))'


start_poll = [
    ['Сколько колечек у ауди', 'Три', 'Четыре', 'Пять', '', '', 2],
    ['Как звали мальчика из дерева? ', 'Партино', 'Буратино', None, None, None, 2],
    ['Какое имя у кота из Простоквашино?', 'Барбоскин', 'Картошка', 'Аноним', 'мальвина', 'Матроскин', 1],
]


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)


session = Session(expire_on_commit=False)

with session:
    session.execute(delete(Question))
    session.commit()
    session.execute(delete(Victorine))
    session.commit()
    new_victorina = Victorine(name='testvict')
    session.add(new_victorina)
    for item_menu in start_poll:
        try:
            q = Question(
                victorine=new_victorina,
                question=item_menu[0],
                answer1=item_menu[1],
                answer2=item_menu[2],
                answer3=item_menu[3],
                answer4=item_menu[4],
                answer5=item_menu[5],
                correct_answer=item_menu[6]
                        )
            # print(q)
            session.add(q)
            session.commit()
        except Exception as err:
            print(err)

with session:
    victorins = session.execute(select(Victorine)).scalars().all()
    my_victorine: Victorine = victorins[0]
    print(my_victorine)
    for question in my_victorine.questions:
        print(question)

# 2 2 1
answers = [1, 2, 3]
result = my_victorine.check_answers(answers)
print(result)
assert result == [False, True, False]
score = my_victorine.get_score(answers)
print(score)
assert score == 1
count = my_victorine.count()
assert count == 3
q1: Question = my_victorine.questions[0]
correct_result_q1 = q1.check_answer(2)
print(correct_result_q1)
assert correct_result_q1 is True
correct_result_q1 = q1.check_answer('2')
print(correct_result_q1)
assert correct_result_q1 is True
incorrect_result_q1 = q1.check_answer(1)
print(incorrect_result_q1)
assert incorrect_result_q1 is False

