from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.database import check_user_in_db, connect_db, add_user_to_db, get_all_products, get_user_orders,delete_order,\
update_order_status, get_user_expenses, add_order,get_all_user_ids
from app.keyboards import get_product_keyboard, admin_menu, get_orders_keyboard, yes_no_keyboard
from app.states import AddProductState, RegistrationStates, OrderState, NotificationStates
from datetime import datetime

router = Router()

def register_handlers(dp):
    dp.include_router(router)


#========Стартовая страница========

@router.message(F.text == "/start")
async def start_registration(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not check_user_in_db(user_id):
        await message.answer("Привет! Давай зарегистрируемся. Введи своё имя:")
        await state.set_state(RegistrationStates.waiting_for_first_name)
    else:
        await message.answer("Используйте меню для оформления заказов.")
        try:
            for msg_id in range(message.message_id, message.message_id - 20, -1):  # Удаляем последние 20 сообщений
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print("Не удалось удалить сообщение:", e)  # В случае, если удаление невозможно

            # Приветственное сообщение
        await message.answer("⬇️")


@router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Отлично! Теперь введите вашу фамилию:")
    await state.set_state(RegistrationStates.waiting_for_last_name)


@router.message(RegistrationStates.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    first_name = data['first_name']
    last_name = message.text
    telegram_id = message.from_user.id
    registration_date = datetime.now()

    add_user_to_db(telegram_id, first_name, last_name, registration_date)

    await message.answer(f"Регистрация завершена! Добро пожаловать, {first_name} {last_name}.")
    await state.clear()

#========Каталог=======

@router.message(F.text == "/catalog")
async def show_catalog(message: types.Message):
    products = get_all_products()

    if not products:
        await message.answer("Каталог пуст.")
        return

    keyboard = get_product_keyboard(products)
    await message.answer("Выберите товар:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("product_"))
async def ask_quantity(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = int(callback_query.data.split("_")[1])
    await state.update_data(product_id=product_id)
    await callback_query.message.delete()
    await callback_query.message.answer("Укажите количество:")
    await state.set_state(OrderState.waiting_for_quantity)


@router.message(OrderState.waiting_for_quantity)  # Обработчик количества с конкретным состоянием
async def process_quantity(message: types.Message, state: FSMContext):
    quantity_input = message.text.strip()

    try:
        quantity = int(quantity_input)

        if 1 <= quantity <= 5:
            # Получаем данные о выбранном товаре из состояния
            data = await state.get_data()
            product_id = data.get("product_id")
            user_id = message.from_user.id

            # Добавляем товар в корзину (заказ) в базе данных
            add_order(user_id, product_id, quantity)  # Обратите внимание на эту функцию

            await message.answer(f"Вы добавили {quantity} шт. товара в корзину.")

            # Очищаем текущее состояние после добавления
            await state.clear()
        else:
            await message.answer("Вы можете заказать только от 1 до 5 штук товара.")

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число от 1 до 5.")


#=======Мои заказы=======
@router.message(F.text == "/myorder")
async def show_my_orders(message: types.Message):
    user_id = message.from_user.id
    orders = get_user_orders(user_id)

    total_price = sum(order[2] * order[3] for order in orders)  # order[2] - quantity, order[3] - price

    # Создание клавиатуры с кнопками заказов
    keyboard = get_orders_keyboard(orders)
    await message.answer(f"Заказ на {total_price} руб:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("delete_order_"))
async def handle_delete_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[2])
    delete_order(order_id)


    await callback_query.answer("Заказ удалён.")

    # Обновляем список заказов
    user_id = callback_query.from_user.id
    orders = get_user_orders(user_id)

    if orders:
        keyboard = get_orders_keyboard(orders)
        await callback_query.message.edit_text("Ваши заказы", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("У вас нет заказов.")


@router.callback_query(F.data == "confirm_order")
async def handle_confirm_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    orders = get_user_orders(user_id)

    if not orders:
        await callback_query.answer("У вас нет заказов для утверждения.")
        return

    # Формируем сообщение для администратора
    order_details = "\n".join(
        [f"{order[1]} — {order[2]} шт за {order[2] * order[3]} руб." for order in orders]
    )
    message_to_admin = f"Новый заказ от пользователя {callback_query.from_user.full_name}:\n\n{order_details}"

    # Отправка сообщения администратору
    ADMIN_CHAT_ID = 1946671407

    await callback_query.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_to_admin)

    # Обновление статуса заказов на "подтвержден"
    update_order_status(user_id)

    await callback_query.answer("Заказ отправлен администратору.")
    await callback_query.message.edit_text("Ваш заказ утверждён и отправлен.")


#=======FOR ADMIN=======

# Проверка роли администратора (можно расширить эту логику)
async def is_admin(user_id):
    # Например, список админов
    admin_ids = [1946671407]  # Заменить на реальные ID администраторов
    return user_id in admin_ids


# Команда /admin для вызова админского меню
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if await is_admin(message.from_user.id):
        await message.answer("Добро пожаловать в админ-панель.", reply_markup=admin_menu())
    else:
        await message.answer("У вас нет доступа к админ-панели.")


@router.message(lambda message: message.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара:")
    await state.set_state(AddProductState.waiting_for_name)  # Устанавливаем состояние ожидания

@router.message(AddProductState.waiting_for_name)
async def process_product_name(message: types.Message, state: FSMContext):
    product_name = message.text
    await state.update_data(product_name=product_name)  # Сохраняем название товара

    await message.answer("Введите цену товара:")
    await state.set_state(AddProductState.waiting_for_price)  # Переходим к следующему состоянию

@router.message(AddProductState.waiting_for_price)
async def process_product_price(message: types.Message, state: FSMContext):
    product_price = message.text
    await state.update_data(product_price=product_price)  # Сохраняем цену товара

    await message.answer("Товар в наличии? ", reply_markup=yes_no_keyboard())
    await state.set_state(AddProductState.waiting_for_availability)  # Переходим к следующему состоянию

@router.message(AddProductState.waiting_for_availability)
async def process_product_availability(message: types.Message, state: FSMContext):
    if message.text in ["Да", "Нет"]:
        availability = message.text == "Да"
        product_data = await state.get_data()

        # Извлекаем данные о товаре
        product_name = product_data['product_name']
        product_price = product_data['product_price']

        # Добавляем товар в базу данных
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price, in_stock) VALUES (?, ?, ?)",
                       (product_name, product_price, availability))
        conn.commit()
        conn.close()

        await message.answer("Товар успешно добавлен!", reply_markup=admin_menu())
        await state.clear()  # Сбрасываем состояние после завершения
    else:
        await message.answer("Пожалуйста, выберите 'Да' или 'Нет'.")

# Обработчик для кнопки "Назад"
@router.message(lambda message: message.text == "Назад")
async def back_to_admin_menu(message: types.Message):
    await message.answer("Вы вернулись в админ-панель.", reply_markup=admin_menu())
#=======Уведомления админа=======
@router.message(F.text == "Отправить уведомление всем")
async def send_notification_to_all(message: types.Message, state: FSMContext):
    await message.answer("Введите текст уведомления, которое вы хотите отправить всем пользователям:")
    await state.set_state(NotificationStates.waiting_for_notification_text)

@router.message(NotificationStates.waiting_for_notification_text)
async def process_notification_text(message: types.Message, state: FSMContext):
    notification_text = message.text.strip()

    # Получите список всех зарегистрированных пользователей
    user_ids = get_all_user_ids()  # Функция, которая возвращает список ID всех пользователей

    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, notification_text)
        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

    await message.answer("Уведомление отправлено всем пользователям.")
    await state.clear()  # Завершаем состояние


# Показать все товары
@router.message(lambda message: message.text == "Показать товары")
async def show_products(message: types.Message):
    if await is_admin(message.from_user.id):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, in_stock, quantity FROM products")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "Выберите товар для обновления:\n\n"
            for id, name, price, in_stock, quantity in products:
                stock_status = "Да" if in_stock else "Нет"
                response += f"{id} - {name} (Цена: {price}₽, В наличии: {stock_status})\n"

            response += "\nВведите ID товара, чтобы обновить наличие или цену (нажмите 'Отмена', чтобы вернуться в меню)."
            await message.answer(response, reply_markup=admin_menu())
        else:
            await message.answer("Товаров нет в базе данных.")
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

# Обновление наличия и цены товара
@router.message(lambda message: message.text.isdigit())
async def update_product_details(message: types.Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        product_id = int(message.text)

        # Запрос текущих данных товара
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, in_stock, price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()

        if product:
            product_name, current_stock, current_price = product
            stock_status = "Да" if current_stock else "Нет"

            # Запрос нового наличия и цены
            new_stock_text = (f"Текущий статус: {'В наличии' if current_stock else 'Нет в наличии'}.\n"
                              f"Текущая цена: {current_price}₽.\n"
                              f"Выберите новый статус наличия (да/нет) и введите новую цену через пробел:\n"
                              f"Пример: 'Да 150' или 'Нет 0'.")

            await message.answer(new_stock_text)
            await state.update_data(product_id=product_id)
            await state.set_state(AddProductState.waiting_for_stock_and_price)
        else:
            await message.answer("Товар с таким ID не найден.")
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

# Обработка нового наличия товара и цены
@router.message(AddProductState.waiting_for_stock_and_price)
async def set_new_product_details(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    product_id = user_data['product_id']

    try:
        stock_input, price_input = message.text.split()
        in_stock = stock_input.lower() == "да"
        new_price = float(price_input)

        # Обновляем наличие товара и цену в базе данных
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET in_stock = ?, price = ? WHERE id = ?", (in_stock, new_price, product_id))
        conn.commit()
        conn.close()

        await message.answer("Статус наличия и цена товара успешно обновлены!", reply_markup=admin_menu())
        await state.clear()  # Сбрасываем состояние
    except ValueError:
        await message.answer("Неверный ввод. Пожалуйста, используйте формат: 'Да 150' или 'Нет 0'.")

#======Назад======
@router.message(lambda message: message.text == "Назад")
async def back_to_main_menu(message: types.Message):
    await message.answer("Вы вернулись в главное меню.", reply_markup=admin_menu())  # Меню админа или основное меню

#======Статистика======
@router.message(F.text == "/stat")
async def show_statistics(message: types.Message):
    user_id = message.from_user.id
    week_total, month_total, total = get_user_expenses(user_id)

    await message.answer(
        f"📊 Ваша статистика покупок:\n\n"
        f"За последнюю неделю: {week_total} руб.\n"
        f"За последний месяц: {month_total} руб.\n"
        f"Всего: {total} руб."
    )
