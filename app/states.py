from aiogram.fsm.state import StatesGroup, State

class AddProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_stock = State()
    waiting_for_quantity = State()
    waiting_for_new_stock = State()
    waiting_for_availability = State()
    waiting_for_stock_and_price = State()

# FSM для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_notification_text = State()

class OrderState(StatesGroup):
    waiting_for_quantity = State()

class NotificationStates(StatesGroup):
    waiting_for_notification_text = State()