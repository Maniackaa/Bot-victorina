import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent

from config_data.bot_conf import config, get_my_loggers
from handlers import admin_handlers
from handlers.admin_handlers import on_unknown_intent
from keyboards.keyboards import begin_kb

logger, err_log = get_my_loggers()


async def set_commands(bot: Bot, settings):
    commands = [
        BotCommand(
            command="start",
            description="Start",
        ),
    ]

    admin_commands = commands.copy()
    admin_commands.append(
        BotCommand(
            command="admin",
            description="Admin panel",
        )
    )

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
    for admin_id in config.tg_bot.admin_ids:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(
                    chat_id=admin_id,
                ),
            )
        except Exception as err:
            logger.info(f'Админ id {admin_id}  ошибочен')


async def main():

    if config.tg_bot.USE_REDIS:
        storage = RedisStorage.from_url(
            url=f"redis://{config.redis_db.REDIS_HOST}",
            connection_kwargs={
                "db": 0,
            },
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token,  default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
    dp.errors.register(on_unknown_intent, ExceptionTypeFilter(UnknownIntent),)
    try:
        dp.include_router(admin_handlers.router)
        setup_dialogs(dp)
        await set_commands(bot, config)
        # await bot.get_updates(offset=-1)
        await bot.delete_webhook(drop_pending_updates=True)
        # await bot.send_message(chat_id=config.tg_bot.admin_ids[0], text='Бот запущен')

        await bot.send_message(chat_id=config.tg_bot.GROUP_ID, text='Бот запущен', reply_markup=begin_kb)
        await dp.start_polling(bot, config=config)
    finally:
        await dp.fsm.storage.close()
        await bot.session.close()


try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    logger.error("Bot stopped!")
