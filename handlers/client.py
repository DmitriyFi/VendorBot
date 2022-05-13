import asyncio

from aiogram import Router, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Command, Text

from filters.chat_type import ChatTypeFilter
from misc.functions import delete_message
from keyboards.reply import main_menu_keyboard, more_items_keyboard
from models.database import get_store, choose_item, fill_data_order, fill_shipping
from misc.states import Purchase, Shipping

from pytz import timezone

router = Router()


@router.message(ChatTypeFilter(chat_type=['group', 'supergroup']), Command(commands=['start']))
async def cmd_start_in_group(message: Message):
    msg = await message.reply("Conversation with bot only via pm. Message him:\nhttps://t.me/JudasIscaribot\n\n"
                              "[Warning] This message will be self-deleted within 15 seconds",
                              disable_web_page_preview=True)
    await asyncio.sleep(14)
    await message.delete()
    asyncio.create_task(delete_message(msg, sleep_time=1))


@router.message(Command(commands=['start']))
async def cmd_start_in_private(message: Message):
    await message.answer("To see the list of our items - hit the Stuff button", reply_markup=main_menu_keyboard)


@router.message(Command(commands=['help']))
async def cmd_help(message: Message):
    await message.answer('If you have faced any technical issues with the bot, please mail us with a tag bot_issues:\n'
                         '\U00002709 fisenko.business@mail.ru')


@router.message(Text(text='Stuff'))
async def cmd_stuff(message: Message, state: FSMContext):
    await state.set_state(Purchase.order_id)
    await get_store(message)


# Выход из машины состояний
@router.message(Command(commands=['cancel']), state=Purchase or Shipping)
async def cancel_purchase(message: Message, state: FSMContext):
    await message.answer('[INFO] Покупка отменена')
    await state.clear()


# Ловим выбор пользователя и запускаем машину состояний
@router.callback_query(lambda x: x.data and x.data.startswith('buy:'))
async def select_item(callback: CallbackQuery, state: FSMContext):
    customer_id = callback.message.chat.id
    await state.update_data(order_id=customer_id)
    await state.set_state(Purchase.product_id)

    choice = await choose_item(callback.data.replace('buy:', ''))
    item_id, item_photo, item_name = choice[0], choice[1], choice[2]
    await state.update_data(item_id=item_id)
    await callback.message.answer_photo(photo=item_photo,
                                        caption=f'Какое количество товара "{item_name}" Вам необходимо?\n'
                                                f'выйти без изменений /cancel')
    await state.set_state(Purchase.count)


@router.message(state=Purchase.count)
async def ask_quantity_items(message: Message, state: FSMContext):
    print(message.text)
    try:
        if isinstance(int(message.text), int) and int(message.text) > 0:
            item_count = int(message.text)
            await state.update_data(count=item_count)
            await message.answer('Еще что-нибудь?"\nили нажмите -> /cancel', reply_markup=more_items_keyboard)

            data = await state.get_data()
            await fill_data_order(data=data)
            await state.set_state(Purchase.order_id)
        else:
            await message.answer('Введите целое положительное число\nили нажмите -> /cancel')
            await state.set_state(Purchase.count)
    except Exception as ex:
        print(ex)
        data = await state.get_data()
        await fill_data_order(data=data)
        await state.set_state(Purchase.order_id)


@router.message(Text(text='Нет'), state=Purchase.order_id)
async def no_more_items(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Введите Ваше ФИО\nили нажмите -> /cancel')
    await state.set_state(Shipping.id)


@router.message(Text(text='Да'), state=Purchase.order_id)
async def more_items(message: Message, state: FSMContext):
    await state.set_state(Purchase.product_id)
    await get_store(message)


@router.message(F.text, state=Shipping.id)
async def ask_customers_name(message: Message, state: FSMContext):
    customer_id = message.chat.id
    await state.update_data(id=customer_id)
    await state.set_state(Shipping.name)

    customer_name = message.text
    await state.update_data(name=customer_name)
    await message.answer('Введите Ваш номер телефона\nили нажмите -> /cancel')
    await state.set_state(Shipping.phone)


@router.message(F.text, state=Shipping.phone)
async def ask_customers_phone(message: Message, state: FSMContext):
    customer_phone = message.text
    await state.update_data(phone=customer_phone)
    await message.answer('Введите Ваш адрес доставки\nили нажмите -> /cancel')
    await state.set_state(Shipping.address)


@router.message(F.text, state=Shipping.address)
async def ask_customers_address(message: Message, state: FSMContext):
    customer_address = message.text
    await state.update_data(address=customer_address)
    await state.set_state(Shipping.order_date)

    date = message.date
    msk = timezone('Europe/Moscow')
    order_date_msk = date.astimezone(msk).strftime('%d.%m.%Y %H:%M')
    await state.update_data(order_date=order_date_msk)

    await message.answer('Ваша заявка отправлена на модерацию. Большое спасибо за заказ!\n'
                         'Наши модераторы свяжутся с Вами для уточнения деталей заказа и пришлют реквизиты для оплаты.')
    data = await state.get_data()
    await fill_shipping(data)

    # Очищаем машину состояний
    await state.clear()
