from aiogram.dispatcher.fsm.state import StatesGroup, State


class NewItem(StatesGroup):
    id = State()
    photo = State()
    name = State()
    description = State()
    price = State()


class Shipping(StatesGroup):
    id = State()
    name = State()
    phone = State()
    address = State()
    order_date = State()


class Purchase(StatesGroup):
    order_id = State()
    product_id = State()
    count = State()
