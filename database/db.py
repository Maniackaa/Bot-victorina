import dataclasses
import datetime

from sqlalchemy import create_engine, ForeignKey, String, DateTime, \
    Integer, select, delete, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from config_data.bot_conf import get_my_loggers, BASE_DIR

logger, err_log = get_my_loggers()

# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
db_path = BASE_DIR / 'base.sqlite'
db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


@dataclasses.dataclass
class Coupon:
    id: int
    code: str
    score: int
    discont: int
    vict_name: str
    status: str


class Base(DeclarativeBase):
    def set(self, key, value):
        _session = Session(expire_on_commit=False)
        with _session:
            if isinstance(value, str):
                value = value[:999]
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            logger.debug(f'Изменено значение {key} на {value}')
            return self


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(30), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=0)
    results: Mapped[list['Result']] = relationship(back_populates='user', lazy='selectin',
                                                   cascade='save-update, merge, delete',)

    def __repr__(self):
        return f'{self.id}. {self.username or "-"} {self.tg_id}'


class Victorine(Base):
    __tablename__ = 'victorines'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    questions: Mapped[list['Question']] = relationship(back_populates='victorine',  lazy='selectin')
    image_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True, default='media/no_image.jpg')
    is_active: Mapped[int] = mapped_column(Integer(), default=0)
    msg_id: Mapped[int] = mapped_column(Integer(), nullable=True)
    results: Mapped[list['Result']] = relationship(back_populates='victorine', lazy='selectin',
                                                   cascade='save-update, merge, delete',)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.id}. {self.name}))'

    def __str__(self):
        _questions = '\n\n'.join([str(q) for q in self.questions])
        # print(_questions)
        return (f'Викторина {self.name} ({self.count()}).\n'
                f'{_questions}'
                )

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
    question: Mapped[str] = mapped_column(String(1000), nullable=True)
    answer1: Mapped[str] = mapped_column(String(100), nullable=False)
    answer2: Mapped[str] = mapped_column(String(100), nullable=False)
    answer3: Mapped[str] = mapped_column(String(100), nullable=True)
    answer4: Mapped[str] = mapped_column(String(100), nullable=True)
    answer5: Mapped[str] = mapped_column(String(100), nullable=True)
    correct_answer: Mapped[int] = mapped_column(Integer(), default=1)
    MAX_ANSWER_COUNT = 5

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

    def get_correct_answer_text(self) -> str:
        _correct_answer_num = self.correct_answer
        # print(_correct_answer_num, type(_correct_answer_num))
        # print(self.correct_answer, type(self.correct_answer))
        if _correct_answer_num < 1:
            return ''
        return getattr(self, f'answer{_correct_answer_num}')

    def check_answer(self, answer_num) -> bool:
        """Проверяет ответ"""
        return self.correct_answer == int(answer_num)

    def get_answer_count(self):
        return len(self.get_answers())

    def add_answer(self, new_answer):
        answer_count = self.get_answer_count()
        logger.debug(f'add_answer {new_answer}. count: {answer_count}')
        if answer_count >= self.MAX_ANSWER_COUNT:
            raise AttributeError(f'В вопросе не может быть больше {self.MAX_ANSWER_COUNT} ответов')
        name = f'answer{answer_count + 1}'
        self.set(name, new_answer)
        logger.debug('Добавлено')

    def is_not_full(self):
        return self.get_answer_count() < self.MAX_ANSWER_COUNT

    def delete_answer_from_question(self, answer_num_to_del):
        """['В1, -, В3, В4]
        3 > 2
        4 > 3
        """
        answer_num_to_del = int(answer_num_to_del)
        logger.debug(f'delete_answer_from_question:', num=answer_num_to_del, type_num=type(answer_num_to_del))
        if self.correct_answer >= answer_num_to_del:
            self.correct_answer -= 1
            logger.debug(f'correct_answer изменен на {self.correct_answer}')
        if self.correct_answer < 1:
            self.correct_answer = 1
            logger.debug(f'correct_answer изменен на {self.correct_answer}')

        answer_count = self.get_answer_count()
        if answer_num_to_del == self.get_answer_count():
            # setattr(self, f'answer{answer_num_to_del}', None)
            self.set(f'answer{answer_num_to_del}', None)
        else:
            for index in range(answer_num_to_del, answer_count):
                # setattr(self, f'answer{index}',  getattr(self, f'answer{index + 1}'))
                self.set(f'answer{index}',  getattr(self, f'answer{index + 1}'))
            # setattr(self, f'answer{answer_count}', None)
            self.set(f'answer{answer_count}', None)

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

    def __str__(self):
        return f'{self.id}. {self.question} ({self.get_correct_answer_text()})'


class Result(Base):
    __tablename__ = 'results'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    victorine_id: Mapped[int] = mapped_column(ForeignKey('victorines.id', ondelete='CASCADE'))
    victorine: Mapped[Victorine] = relationship(back_populates="results", lazy='selectin')
    victorine_name: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    user: Mapped[User] = relationship(back_populates="results", lazy='selectin')
    result_text: Mapped[str] = mapped_column(Text(), nullable=True)


start_poll = [
    ['Сколько колечек у ауди', 'Три', 'Четыре', 'Пять', '', '', 2],
    ['Как звали мальчика из дерева? ', 'Партино', 'Буратино', None, None, None, 2],
    ['Какое имя у кота из Простоквашино?', 'Барбоскин', 'Картошка', 'Аноним', 'мальвина', 'Матроскин', 5],
]


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)


session = Session(expire_on_commit=False)

# with session:
#     all_victorina = session.execute(delete(Victorine))
#     session.commit()

with session:
    old_victorina = session.execute(select(Victorine).where(Victorine.name == 'testvict')).scalars().first()
    print(old_victorina)
    if old_victorina:
        old_questions = old_victorina.questions
        print(old_questions)
        for q in old_questions:
            session.delete(q)
        session.commit()
        session.delete(old_victorina)
    session.commit()

with session:
    new_victorina = Victorine(name='testvict', image='media/no_image.jpg', description='Описание викторины')
    session.add(new_victorina)
    session.commit()
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
                correct_answer=item_menu[6],
                        )
            session.add(q)
            session.commit()
        except Exception as err:
            print(err)

with session:
    victorine = session.execute(select(Victorine).where(Victorine.name == 'testvict')).scalar()
    my_victorine: Victorine = victorine
    print(my_victorine)

if my_victorine:
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
    print(q1)
    correct_result_q1 = q1.check_answer(2)
    print(correct_result_q1)
    assert correct_result_q1 is True
    correct_result_q1 = q1.check_answer('2')
    print(correct_result_q1)
    assert correct_result_q1 is True
    incorrect_result_q1 = q1.check_answer(1)
    print(incorrect_result_q1)
    assert incorrect_result_q1 is False
    assert q1.correct_answer == 2
    assert q1.get_correct_answer_text() == 'Четыре'


    assert q1.get_answer_count() == 3
    q1.add_answer('444')
    assert q1.get_answers()[-1] == '444'
    assert q1.get_answer_count() == 4
    q1: Question = my_victorine.questions[0]
    q1.add_answer('555')
    assert q1.get_answers()[-1] == '555'
    assert q1.get_answer_count() == 5
    try:
        q1.add_answer('666')
    except AttributeError as err:
        assert err.args[-1] == 'В вопросе не может быть больше 5 ответов'

    print(q1)
    print(q1.get_answers())
    print(q1.correct_answer)

    q1.delete_answer_from_question(2)
    assert q1.get_answer_count() == 4
    assert q1.answer5 is None
    print(q1.get_answers())
    print(q1.correct_answer)


with session:
    u = select(User)
    user = session.execute(u).scalar()
    print(user)
    if not user:
        user = User(tg_id=123456)
        session.add(user)
        session.commit()
        print(user)
    # user_q = select(User)
    # user = session.execute(user_q).scalar()
    text = 'dsflvgcqlejfgvlq egrflivcquhy lieufhv lqeiughyfrv leh frvliquhe vqer \nsldufvghlqeiwgrfvlqegvcoqeir\nqeoruvghqlevghlqegvh\nqeoiuvrghqeoivghoqiegvrh'
    result = Result(victorine=my_victorine,
                    user=user,
                    result_text=text,
                    victorine_name=my_victorine.name)
    session.add(result)
    session.commit()
    print(result)



