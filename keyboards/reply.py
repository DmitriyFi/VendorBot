from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        # [
        #     KeyboardButton(text='Schedule'),
        #     KeyboardButton(text='Location'),
        # ],
        [
            KeyboardButton(text='Stuff')
        ]
    ]
)


moderation_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text='Upload'),
            KeyboardButton(text='Delete'),
        ]
    ]
)


more_items_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text='Да'),
            KeyboardButton(text='Нет'),
        ]
    ]
)
