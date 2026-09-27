import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_pending_posts, mark_sent

# Планировщик работает в UTC — все сравнения времени в БД идут в UTC
scheduler = AsyncIOScheduler(timezone="UTC")


async def check_scheduled_posts(bot):
    """Каждую минуту проверяет БД и отправляет посты, время которых пришло."""
    posts = get_pending_posts()
    for post in posts:
        post_id, channel_id, media_type, media_file_id, text, links_json, emojis_json = post

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
            print(f"✅ Отправлен пост {post_id} в {channel_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки поста {post_id}: {e}")


def start_scheduler(bot):
    scheduler.add_job(check_scheduled_posts, "interval", minutes=1, args=[bot])
    scheduler.start()