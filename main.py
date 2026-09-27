import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from scheduler import start_scheduler
from handlers import admin, channel

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    init_db()

    # Создание бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение роутеров
    dp.include_router(admin.router)
    dp.include_router(channel.router)

    # Запуск планировщика
    start_scheduler(bot)

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())