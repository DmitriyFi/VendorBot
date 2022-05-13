from typing import Optional
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ModerateCallbackFactory(CallbackData, prefix='moderate'):
    action: str


class BuyerCallbackFactory(CallbackData, prefix='buy'):
    action: str
    id: Optional[str]


def moderator_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Загрузить товар', callback_data=ModerateCallbackFactory(action='upload')
      )
    builder.button(
        text='Удалить товар', callback_data=ModerateCallbackFactory(action='delete')
    )
    builder.adjust(2)
    return builder.as_markup()


def moderator_confirm_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Подтвердить', callback_data=ModerateCallbackFactory(action='confirm')
    )
    builder.button(
        text='Ввести заново', callback_data=ModerateCallbackFactory(action='change')
    )
    builder.adjust(1)
    return builder.as_markup()


def _buy(photo):
    num = photo
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Wanna buy it!', callback_data=BuyerCallbackFactory(id=num)
    )
    builder.adjust(1)
    return builder.as_markup()
