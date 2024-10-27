from aiogram.client import bot
from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')


async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base): #Наполнения базы данных
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))
    description: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column()
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))

async def notify_programmers(message: str):
    programmer_chat_id = "your_programmer_chat_id"  # ID чата с программистами
    await bot.send_message(chat_id=programmer_chat_id, text=message)



async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Items:
    pass