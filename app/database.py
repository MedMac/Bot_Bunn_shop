import sqlite3
import datetime
from datetime import datetime, timedelta

DB_Base = "my_database.db"

# Подключение к базе данных
def connect_db():
    conn = sqlite3.connect(DB_Base)
    return conn

# Создание таблиц
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        price REAL,
                        in_stock BOOLEAN,
                        quantity INTEGER)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER DEFAULT 1,
                        order_date TEXT)''')

    # Таблица для пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER UNIQUE,
                            first_name TEXT,
                            last_name TEXT,
                            registration_date DATETIME
                        )''')

    conn.commit()
    conn.close()

# Получение каталога товаров
def db_get_catalog():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, in_stock, quantity FROM products WHERE in_stock = 1")
    products = cursor.fetchall()
    conn.close()
    return products

# Добавление заказа
def db_add_order(user_id, product_id):
    conn = connect_db()
    cursor = conn.cursor()
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO orders (user_id, product_id, order_date) VALUES (?, ?, ?)",
                   (user_id, product_id, order_date))
    conn.commit()
    conn.close()

# Получение заказов пользователя
def db_get_orders(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT products.name, orders.quantity, products.price
                      FROM orders 
                      JOIN products ON orders.product_id = products.id
                      WHERE orders.user_id = ?''', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return [{"name": order[0], "quantity": order[1], "price": order[2]} for order in orders]


# Регистрация нового пользователя
def db_register_user(user_id, first_name, last_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, first_name, last_name) VALUES (?, ?, ?)", (user_id, first_name, last_name))
    conn.commit()
    conn.close()

# Проверка, зарегистрирован ли пользователь
def db_is_user_registered(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def add_user_to_db(telegram_id, first_name, last_name, registration_date):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (telegram_id, first_name, last_name, registration_date)
                      VALUES (?, ?, ?, ?)''', (telegram_id, first_name, last_name, registration_date))
    conn.commit()
    conn.close()

def check_user_in_db(telegram_id):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_all_products():
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    return products

def add_order(user_id, product_id, quantity):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?)',
                   (user_id, product_id, quantity, datetime.now()))
    conn.commit()
    conn.close()


def get_user_orders(user_id):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT orders.id, products.name, orders.quantity, products.price
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ? AND orders.status = 'в корзине'
    ''', (user_id,))

    orders = cursor.fetchall()
    conn.close()
    return orders


def delete_order(order_id):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()

def update_order_status(user_id, status="подтвержден"):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET status = ?
        WHERE user_id = ? AND status = 'в корзине'
    ''', (status, user_id))
    conn.commit()
    conn.close()




def get_user_expenses(user_id):
    conn = sqlite3.connect(DB_Base)
    cursor = conn.cursor()

    # Дата сегодня
    today = datetime.now()

    # Время одной недели назад
    week_ago = today - timedelta(weeks=1)

    # Время одного месяца назад
    month_ago = today - timedelta(days=30)

    # Запросы для разных периодов
    cursor.execute('''
        SELECT SUM(products.price * orders.quantity)
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ? AND orders.order_date >= ?
    ''', (user_id, week_ago))
    week_total = cursor.fetchone()[0] or 0

    cursor.execute('''
        SELECT SUM(products.price * orders.quantity)
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ? AND orders.order_date >= ?
    ''', (user_id, month_ago))
    month_total = cursor.fetchone()[0] or 0

    cursor.execute('''
        SELECT SUM(products.price * orders.quantity)
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ?
    ''', (user_id,))
    total = cursor.fetchone()[0] or 0

    conn.close()
    return week_total, month_total, total


def get_all_user_ids():
    # Соединяемся с базой данных
    conn = sqlite3.connect(DB_Base)  # Замените на ваш файл БД
    cursor = conn.cursor()

    try:
        # Выполняем запрос для получения всех ID пользователей
        cursor.execute("SELECT telegram_id FROM users")  # Замените на имя вашей таблицы
        user_ids = [row[0] for row in cursor.fetchall()]  # Извлекаем все ID из результата
    except Exception as e:
        print(f"Ошибка при получении ID пользователей: {e}")
        user_ids = []
    finally:
        # Закрываем соединение
        cursor.close()
        conn.close()

    return user_ids