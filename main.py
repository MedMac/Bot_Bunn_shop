import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Для управления состояниями
from aiogram.types import BotCommand
from config import TOKEN
from app.handlers import register_handlers
from app.database import create_tables

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="🪄Запустить бота🎉"),
        BotCommand(command="/catalog", description="📖Каталог товаров📖"),
        BotCommand(command="/myorder", description="🫸Мой заказ🫷"),
        BotCommand(command="/admin", description="⚙️Админка⚙️"),
        BotCommand(command="/stat", description="📊Статистика⏳")
    ]
    await bot.set_my_commands(commands)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # Добавляем FSM хранилище

    # Регистрируем обработчики
    register_handlers(dp)

    # Устанавливаем команды для бота
    await set_commands(bot)

    create_tables()

    try:
        # Запуск поллинга
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
