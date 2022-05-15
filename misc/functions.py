import asyncio
from contextlib import suppress
import itertools
import operator
from aiogram import types


async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress():
        await message.delete()
