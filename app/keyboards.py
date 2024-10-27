from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types


# Клавиатура для отображения каталога товаров
def get_catalog_keyboard(products):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        button = InlineKeyboardButton(
            text=f"{product[1]} - {product[2]} руб.",
            callback_data=f"order_{product[0]}"
        )
        keyboard.add(button)
    return keyboard

# Клавиатура для подтверждения заказа
def get_order_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться в каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="Просмотреть мой заказ", callback_data="myorder")]
        ]
    )

#====Пример клавиатуры как должна быть====
def admin_menu():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Добавить товар"),
                types.KeyboardButton(text="Показать товары"),
                types.KeyboardButton(text="Отправить уведомление всем")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard
#====Пример клавиатуры как должна быть====

def back_button():
    return KeyboardButton(text="Назад")  # Функция для создания кнопки "Назад"

def yes_no_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Да"),
                KeyboardButton(text="Нет"),
            ],
            [
                KeyboardButton(text="Назад"),  # Кнопка "Назад" для возврата в предыдущее меню
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True  # Опционально, чтобы скрыть клавиатуру после нажатия
    )
    return keyboard

def get_product_keyboard(products):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{product[1]} — {product[2]} руб.",
                    callback_data=f"product_{product[0]}"
                )
            ]
            for product in products
        ]
    )
    return keyboard

def get_orders_keyboard(orders):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{order[1]} — {order[2]} шт за {order[2] * order[3]} руб.",
                    callback_data=f"delete_order_{order[0]}"
                )
            ]
            for order in orders
        ] + [
            [InlineKeyboardButton(text="Утвердить заказ", callback_data="confirm_order")]
        ]
    )
    return keyboard

