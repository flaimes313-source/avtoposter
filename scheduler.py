import json
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_pending_posts, mark_sent

logger = logging.getLogger(__name__)

# Планировщик работает в UTC
scheduler = AsyncIOScheduler(timezone="UTC")


async def check_scheduled_posts(bot):
    logger.info("⏰ Проверка запланированных постов...")
    posts = get_pending_posts()
    logger.info(f"Найдено постов для отправки: {len(posts)}")

    for post in posts:
        post_id, channel_id, media_type, media_file_id, text, links_json, emojis_json = post
        logger.info(f"→ Отправка поста #{post_id} в канал {channel_id} (тип: {media_type})")

        links = json.loads(links_json) if links_json else []
        emojis = json.loads(emojis_json) if emojis_json else []

        full_text = (text or "")
        if emojis:
            full_text += "\n\n" + " ".join(emojis)
        if links:
            full_text += "\n\n" + "\n".join(links)

        try:
            if media_type == "photo" and media_file_id:
                await bot.send_photo(chat_id=channel_id, photo=media_file_id, caption=full_text)
            elif media_type == "animation" and media_file_id:
                await bot.send_animation(chat_id=channel_id, animation=media_file_id, caption=full_text)
            else:
                await bot.send_message(chat_id=channel_id, text=full_text)

            mark_sent(post_id)
            logger.info(f"✅ Пост #{post_id} успешно отправлен в {channel_id}")
        except Exception as e:
            logger.exception(f"❌ Ошибка отправки поста #{post_id}: {e}")


def start_scheduler(bot):
    scheduler.add_job(check_scheduled_posts, "interval", minutes=1, args=[bot])
    scheduler.start()
    logger.info("🚀 Планировщик запущен (интервал: 1 мин, часовой пояс: UTC)")