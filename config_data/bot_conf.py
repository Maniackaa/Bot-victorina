import logging
import os
from dataclasses import dataclass
import pytz
from pathlib import Path

import structlog as structlog
from dotenv import load_dotenv
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, CallsiteParameter
from structlog.typing import WrappedLogger, EventDict

BASE_DIR = Path(__file__).resolve().parent.parent


"""
format = "%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
"""

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            # 'format': "%(asctime)s - [%(levelname)8s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
            'format': "%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
        },
        'rotating_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
        'errors_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "errors_bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
    },
    'loggers': {
        'bot_logger': {
            'handlers': ['stream_handler', 'rotating_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
        'errors_logger': {
            'handlers': ['stream_handler', 'errors_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


@dataclass
class PostgresConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class RedisConfig:
    REDIS_DB_NUM: str  # Название базы данных
    REDIS_HOST: str  # URL-адрес базы данных
    REDIS_PORT: str  # URL-адрес базы данных
    REDIS_PASSWORD: str


@dataclass
class TgBot:
    USE_REDIS: bool
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list  # Список id администраторов бота
    base_dir = BASE_DIR
    TIMEZONE: pytz.timezone
    GROUP_ID: str
    TABLE_1: str
    TABLE_2: str
    YOOTOKEN: str


@dataclass
class Logic:
    pass


@dataclass
class Config:
    tg_bot: TgBot
    db: PostgresConfig
    logic: Logic
    redis_db: RedisConfig


def load_config(path=None) -> Config:
    return Config(tg_bot=TgBot(token=os.getenv('BOT_TOKEN'),
                               admin_ids=[x for x in (os.getenv('ADMIN_IDS').split(',')) if x],
                               TIMEZONE=pytz.timezone(os.getenv('TIMEZONE')),
                               GROUP_ID=os.getenv('GROUP_ID'),
                               TABLE_1=os.getenv('TABLE_1'),
                               TABLE_2=os.getenv('TABLE_2'),
                               YOOTOKEN=os.getenv('YOOTOKEN'),
                               USE_REDIS=os.getenv('USE_REDIS').lower() == 'true',
                               ),
                  db=PostgresConfig(database=os.getenv('POSTGRES_DB'),
                                    db_host=os.getenv('DB_HOST'),
                                    db_port=os.getenv('DB_PORT'),
                                    db_user=os.getenv('POSTGRES_USER'),
                                    db_password=os.getenv('POSTGRES_PASSWORD'),
                                    ),
                  redis_db=RedisConfig(
                      REDIS_DB_NUM=os.getenv('REDIS_DB_NUM'),
                      REDIS_HOST=os.getenv('REDIS_HOST'),
                      REDIS_PORT=os.getenv('REDIS_PORT'),
                      REDIS_PASSWORD=os.getenv('REDIS_PASSWORD'),
                  ),
                  logic=Logic(),
                  )

load_dotenv()

config = load_config()
print(config)
tz = config.tg_bot.TIMEZONE
# print(conf.tg_bot.admin_ids)


# def get_my_loggers():
#     import logging.config
#     logging.config.dictConfig(LOGGING_CONFIG)
#
#     def get_renderer():
#         if True:
#             return ConsoleRenderer()
#         return JSONRenderer()
#
#     def get_factory():
#         if True:
#             return structlog.PrintLoggerFactory()
#         return structlog.WriteLoggerFactory(file=Path("app").with_suffix(".log").open("wt"))
#
#     structlog.configure(
#         processors=[
#             structlog.contextvars.merge_contextvars,
#             structlog.processors.add_log_level,
#             structlog.processors.StackInfoRenderer(),
#             structlog.dev.set_exc_info,
#             structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
#             structlog.dev.ConsoleRenderer(colors=True),
#
#
#         ],
#         wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
#         context_class=dict,
#         logger_factory=structlog.PrintLoggerFactory(),
#         cache_logger_on_first_use=False
#     )
#     logger = structlog.get_logger()
#     # logger: structlog.stdlib.BoundLogger = structlog.get_logger()
#     # return logging.getLogger('bot_logger'), logging.getLogger('errors_logger')
#     return logger, logger


def get_my_loggers():
    class LogJump:
        def __init__(
            self,
            full_path: bool = False,
        ) -> None:
            self.full_path = full_path

        def __call__(
            self, logger: WrappedLogger, name: str, event_dict: EventDict
        ) -> EventDict:
            if self.full_path:
                file_part = "\n" + event_dict.pop("pathname")
            else:
                file_part = event_dict.pop("filename")
            event_dict["location"] = f'"{file_part}:{event_dict.pop("lineno")}"'

            return event_dict

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.CallsiteParameterAdder(
                [
                    # add either pathname or filename and then set full_path to True or False in LogJump below
                    # structlog.processors.CallsiteParameter.PATHNAME,
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ],
            ),
            LogJump(full_path=False),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    logger = structlog.stdlib.get_logger()
    return logger, logger
