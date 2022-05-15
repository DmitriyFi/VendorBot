from aiogram import Router
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from magic_filter import F

from filters.admin import AdminFilter
from filters.chat_type import ChatTypeFilter
from keyboards.inline import ModerateCallbackFactory, moderator_keyboard, moderator_confirm_cancel_keyboard
from misc.states import NewItem
from models.database import fill_store, get_order, get_store2, delete_item, get_order_processed, has_already_ordered

router = Router()
router.message.filter(AdminFilter())


@router.message(ChatTypeFilter(chat_type=['private']), Command(commands=['start'], state='*'))
async def admin_cmd_start(message: Message):
    name = message.from_user.full_name
    await message.answer(f'Привет, {name}!\n'
                         f'Чтобы активировать панель модерации нажми /moder\n'
                         f'Для проверки активных заказов нажми /order')


@router.message(ChatTypeFilter(chat_type=['private']), Command(commands=['moder'], state='*'))
async def admin_cmd_start(message: Message):
    await message.answer('[INFO] Панель модерации активна:\n\n',
                         reply_markup=moderator_keyboard())


@router.callback_query(lambda x: x.data and x.data.startswith('del:'))
async def admin_delete_item(callback: CallbackQuery):
    await delete_item(callback.data.replace('del:', ''))
    await callback.answer(text=f'{callback.data.replace("del:", "")} удалена.', show_alert=True)


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'delete'))
async def callbacks_admin_delete(callback: CallbackQuery):
    data = await get_store2()
    for item_data in data:
        item_id, item_photo, item_name, item_description, item_price = \
            item_data[0], item_data[1], item_data[2], item_data[3], item_data[4]

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text='Wanna delete it!',
                    callback_data=f'del:' + str(item_name)
                )]
            ]
        )
        await callback.message.answer_photo(photo=item_photo,
                                            caption=f'Name: {item_name}\n'
                                                    f'Description: {item_description}\n'
                                                    f'Price: {item_price}', reply_markup=markup)


# Выход из машины состояний
@router.message(Command(commands=['cancel']), state=NewItem)
async def cancel_moderation(message: Message, state: FSMContext):
    await message.answer('[INFO] Вы отменили создание товара')
    await state.clear()


# Ловим callback и запускаем машину состояний
@router.callback_query(ModerateCallbackFactory.filter(F.action == 'upload'))
async def admin_adds_new(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('[INFO] Пришлите фотографию товара (не документ)\nили нажмите -> /cancel')
    await state.set_state(NewItem.photo)


@router.message(F.photo, state=NewItem.photo)
async def admin_adds_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)

    await message.answer_photo(
        photo=photo,
        caption='Вас устраивает фото?\n\n'
                'выйти без изменений /cancel',
        reply_markup=moderator_confirm_cancel_keyboard())


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'change'), state=NewItem.photo)
async def photo_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('[INFO] Пришлите фотографию товара (не документ)\nили нажмите -> /cancel')
    await state.set_state(NewItem.photo)


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'confirm'), state=NewItem.photo)
async def photo_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('✔ Фотография товара обновлена!\n\n[INFO] Придумайте название товара\n'
                                  'или нажмите -> /cancel')
    await state.set_state(NewItem.name)


@router.message(F.text, state=NewItem.name)
async def admin_adds_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.reply('Вы считаете это название подходящим?\n\n'
                        'выйти без изменений /cancel',
                        reply_markup=moderator_confirm_cancel_keyboard())


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'change'), state=NewItem.name)
async def name_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('[INFO] Придумайте название товара\nили нажмите -> /cancel')
    await state.set_state(NewItem.name)


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'confirm'), state=NewItem.name)
async def name_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('✔ Фотография товара обновлена!\n'
                                  '✔ Название товара обновлено!\n\n[INFO] Опишите Ваш товар\n'
                                  'или нажмите -> /cancel')
    await state.set_state(NewItem.description)


@router.message(F.text, state=NewItem.description)
async def admin_adds_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.reply('Такое описание точно подходит?\n\n'
                        'выйти без изменений /cancel',
                        reply_markup=moderator_confirm_cancel_keyboard())


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'change'), state=NewItem.description)
async def description_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('[INFO] Опишите Ваш товар\nили нажмите -> /cancel')
    await state.set_state(NewItem.description)


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'confirm'), state=NewItem.description)
async def description_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('✔ Фотография товара обновлена!\n'
                                  '✔ Название товара обновлено!\n'
                                  '✔ Описание товара обновлено!\n\n[INFO] Сколько это стоит???\n'
                                  'выход без изменений -> /cancel')
    await state.set_state(NewItem.price)


@router.message(state=NewItem.price)
async def admin_adds_price(message: Message, state: FSMContext):
    price = message.text
    await state.update_data(price=price)
    await message.reply('Не продешевили?\n\n'
                        'выйти без изменений /cancel',
                        reply_markup=moderator_confirm_cancel_keyboard())


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'change'), state=NewItem.price)
async def price_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('[INFO] Сколько это стоит???\nвыход без изменений -> /cancel')
    await state.set_state(NewItem.price)


@router.callback_query(ModerateCallbackFactory.filter(F.action == 'confirm'), state=NewItem.price)
async def price_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('✔ Фотография товара обновлена!\n'
                                  '✔ Название товара обновлено!\n'
                                  '✔ Описание товара обновлено!\n'
                                  '✔ Цена товара обновлена!\n\n[INFO] Загрузка в БД завершена!')

    # Небольшой пользовательский отчет
    data = await state.get_data()
    photo, name, description, price = data.get('photo'), data.get('name'), data.get('description'), data.get('price')
    await callback.message.answer(f'Вот, что было загружено:\n'
                                  f'[PHOTO] {photo}\n'
                                  f'[NAME ] {name}\n'
                                  f'[DISC ] {description}\n'
                                  f'[PRICE] {price}')
    await fill_store(data)
    # Очищаем машину состояний
    await state.clear()


@router.callback_query(lambda x: x.data and x.data.startswith('get:'))
async def admin_delete_item(callback: CallbackQuery):
    await get_order_processed(callback.data.replace('get:', ''))
    await callback.answer(text=f'Все заказы от этого пользователя обработаны.', show_alert=True)


@router.message(ChatTypeFilter(chat_type=['private']), Command(commands=['order']))
async def admin_gets_order(message: Message):
    await get_order(message)

    if not await has_already_ordered():
        await message.answer('Новых заказов пока нет.')
    else:
        await message.answer('Обратите внимание, что при нажатии на кнопку "Process" обработаются сразу все заказы '
                             'от одного и того же пользователя')
