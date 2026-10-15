import asyncio
import logging
import os
import subprocess

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message

from config import BOT_TOKEN, ADMIN_ID
from scheduler import start_scheduler
from handlers import start, admin, admin_panel, support, subscription, channel
from database import is_subscription_required
from handlers.subscription import user_is_subscribed, send_subscription_gate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def run_migrations():
    try:
        logging.info("🔄 Применение миграций Alembic...")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True, text=True, cwd=project_dir
        )
        if result.returncode != 0:
            logging.error(f"❌ Миграция упала: {result.stderr}")
            raise RuntimeError("Не удалось применить миграции")
        logging.info("✅ Миграции применены")
    except FileNotFoundError:
        logging.error("❌ Команда 'alembic' не найдена")
        raise


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        # /start не блокируем
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Админа не блокируем
        if user.id == ADMIN_ID:
            return await handler(event, data)

        if not is_subscription_required():
            return await handler(event, data)

        bot = data["bot"]
        ok, missing = await user_is_subscribed(bot, user.id)
        if ok:
            return await handler(event, data)

        await send_subscription_gate(event, bot, missing, is_edit=False)
        return None


async def main():
    run_migrations()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(support.router)
    dp.include_router(admin_panel.router)
    dp.include_router(admin.router)
    dp.include_router(channel.router)

    start_scheduler(bot)

    logging.info("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())