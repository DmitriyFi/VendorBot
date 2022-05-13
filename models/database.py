import sqlite3 as sq
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


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
        'price TEXT NOT NULL,'
        'PRIMARY KEY("id" AUTOINCREMENT));'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS orders'
        '(id INTEGER NOT NULL, '
        'user_name TEXT NOT NULL, '
        'phone TEXT, '
        'address TEXT NOT NULL, '
        'order_date TEXT NOT NULL,'
        'PRIMARY KEY("id"));'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS order_products'
        '(order_id INTEGER NOT NULL, '
        'product_id INTEGER NOT NULL, '
        'count INTEGER NOT NULL, '
        'PRIMARY KEY("order_id","product_id"),'
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
    for item_data in cur.execute(
            '''SELECT orders.order_date, orders.id, orders.user_name, orders.phone, orders.address, products.name, 
            products.photo, products.price, order_products."count" FROM orders
            INNER JOIN order_products ON order_products.order_id = orders.id
            INNER JOIN products ON product_id = products.id'''
    ).fetchall():
        order_date = item_data[0]
        tg_id = item_data[1]
        customer_name = item_data[2]
        customer_phone = item_data[3]
        customer_address = item_data[4]
        product_name = item_data[5]
        product_photo = item_data[6]
        product_price = item_data[7]
        count = item_data[8]

        await message.answer_photo(photo=product_photo,
                                   caption=f'{order_date} [msk]\n\n'
                                           f'<a href="tg://user?id={tg_id}">{customer_name}</a>\n'
                                           f'Контактный телефон: {customer_phone}\n'
                                           f'Адрес доставки: {customer_address}\n\n'
                                           f'Заказал:\n\n'
                                           f'"{product_name}" - {count} шт.\n'
                                           f'на общую стоимость {int(product_price) * count}')


async def delete_item(data):
    cur.execute('''DELETE FROM products WHERE name == ?''', (data,))
    base.commit()
