import sqlite3 as sq
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
import collections


async def db_start(name):
    global base, cur
    base = sq.connect(name)
    cur = base.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS products'
        '(id INTEGER NOT NULL, '
        'photo TEXT NOT NULL , '
        'name TEXT NOT NULL , '
        'description TEXT NOT NULL, '
        'price TEXT NOT NULL, '
        'PRIMARY KEY("id" AUTOINCREMENT));'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS orders'
        '(id INTEGER NOT NULL, '
        'user_name TEXT NOT NULL, '
        'phone TEXT, '
        'address TEXT NOT NULL, '
        'order_date TEXT NOT NULL, '
        'PRIMARY KEY("id"));'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS order_products'
        '(order_id INTEGER NOT NULL, '
        'product_id INTEGER NOT NULL, '
        'count INTEGER NOT NULL, '
        'FOREIGN KEY (product_id) REFERENCES products (id),'
        'FOREIGN KEY (order_id) REFERENCES orders (id));'
    )
    base.commit()


async def fill_store(data):
    cur.execute('''INSERT INTO products (photo, name, description, price) VALUES (?, ?, ?, ?)''', tuple(data.values()))
    base.commit()


async def fill_data_order(data):
    cur.execute('''INSERT INTO order_products (order_id, product_id , count) VALUES (?, ?, ?)''',
                tuple(data.values()))
    base.commit()


async def fill_shipping(data):
    cur.execute('''INSERT INTO orders (id, user_name, phone, address, order_date) VALUES (?, ?, ?, ?, ?)''',
                tuple(data.values()))
    base.commit()


async def get_store(message):
    for item_data in cur.execute('''SELECT * FROM products''').fetchall():
        item_id, item_photo, item_name, item_description, item_price = \
            item_data[0], str(item_data[1]), item_data[2], item_data[3], item_data[4]

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text='Wanna buy it!',
                    callback_data='buy:' + str(item_id)
                )]
            ]
        )

        for _ordered_users in await has_already_ordered():
            new_user = message.chat.id
            if new_user in _ordered_users:
                await message.answer('Вы уже заказывали. Дождитесь пока Ваш предыдущий заказ обработают!')
                return

        await message.answer_photo(photo=item_photo,
                                   caption=f'Name: {item_name}\n'
                                           f'Description: {item_description}\n'
                                           f'Price: {item_price}\n', reply_markup=markup)


async def get_store2():
    return cur.execute('''SELECT * FROM products''').fetchall()


async def choose_item(data):
    for item_data in cur.execute('''SELECT * FROM products WHERE id == ?''', (data,)).fetchall():
        item_id = item_data[0]
        item_photo = str(item_data[1])
        item_name = item_data[2]

        return item_id, item_photo, item_name


async def get_order(message):
    data = cur.execute(
            '''SELECT orders.id, products.name, order_products."count" FROM orders
            INNER JOIN order_products ON order_products.order_id = orders.id
            INNER JOIN products ON product_id = products.id''').fetchall()

    output = dict()

    for user_id, product_name, product_count in data:
        if not output.get(user_id):
            output[user_id] = collections.defaultdict(int)
        output[user_id][product_name] += product_count

    for i in output:
        tg_id = i
        names = list(output.get(tg_id))
        amount = list(output.get(i).values())
        text = f'[INFO] Новый заказ от <a href="tg://user?id={tg_id}">пользователя</a>:\n' \
               f'{names}\n в количестве:\n{amount} соответственно'

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text='Details',
                    callback_data=f'get:' + str(tg_id)
                )]
            ]
        )

        await message.answer(text, reply_markup=markup)


async def delete_item(data):
    cur.execute('''DELETE FROM products WHERE name == ?''', (data,))
    base.commit()


async def get_order_processed(data):
    cur.execute('''DELETE FROM order_products WHERE order_id == ?''', (data,))
    cur.execute('''DELETE FROM orders WHERE id == ?''', (data,))
    base.commit()


async def get_details(data):
    return cur.execute('''SELECT orders.order_date, orders.id, orders.user_name, orders.phone, orders.address 
                       FROM orders INNER JOIN order_products ON order_products.order_id = orders.id
                                   INNER JOIN products ON product_id = products.id 
                                   WHERE orders.id == ? GROUP BY orders.id''', (data,)).fetchall()


async def has_already_ordered():
    users_are_waiting = cur.execute('''SELECT orders.id FROM orders''').fetchall()
    return users_are_waiting
