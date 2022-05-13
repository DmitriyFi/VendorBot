import asyncio
import logging

from aiogram import Bot, Dispatcher

from handlers import admin, client
from config import load_config
from services.default_commands import set_default_commands
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from middlewares.config import ConfigMiddleware

from models.database import db_start

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, admin_ids: list[int]):
    await set_default_commands(bot=bot)


async def on_startup_database(name: list[str]):
    logging.info(f"Connection to SQLite DB successful")
    await db_start(name=name)


def register_global_middlewares(dp: Dispatcher, config):
    dp.message.outer_middleware(ConfigMiddleware(config))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d\n#%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    dp.include_router(admin.router)
    dp.include_router(client.router)

    register_global_middlewares(dp, config)

    await on_startup(bot, config.tg_bot.admin_ids)
    await on_startup_database(config.db.database)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Бот был выключен!')
