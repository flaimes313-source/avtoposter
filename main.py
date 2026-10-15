import asyncio
import logging
import subprocess
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from scheduler import start_scheduler
from handlers import admin, channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def run_migrations():
    """Применяет миграции Alembic при старте бота."""
    try:
        logging.info("🔄 Применение миграций Alembic...")
        project_dir = os.path.dirname(os.path.abspath(__file__))

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=project_dir
        )

        if result.stdout:
            logging.info(f"alembic stdout:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"alembic stderr:\n{result.stderr}")

        if result.returncode != 0:
            logging.error(f"❌ Миграция завершилась с кодом {result.returncode}")
            raise RuntimeError("Не удалось применить миграции")

        logging.info("✅ Миграции применены")
    except FileNotFoundError:
        logging.error("❌ Команда 'alembic' не найдена. Проверьте, что пакет установлен.")
        raise
    except Exception as e:
        logging.error(f"❌ Ошибка миграции: {e}")
        raise


async def main():
    # 1. Применяем миграции (создаём/обновляем таблицы в PostgreSQL)
    run_migrations()

    # 2. Запускаем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(channel.router)

    start_scheduler(bot)

    logging.info("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())