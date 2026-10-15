import json
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from aiogram.exceptions import TelegramForbiddenError

from database import (
    get_pending_posts, mark_sent,
    get_users_for_weekly_check, update_last_subscription_check,
    is_subscription_required, get_required_channels,
    set_subscription
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


def deserialize_entities(json_str):
    """Превращает JSON-строку в список MessageEntity."""
    if not json_str:
        return None
    data = json.loads(json_str)
    return [MessageEntity(**e) for e in data]


async def check_scheduled_posts(bot):
    logger.info("⏰ Проверка запланированных постов...")
    posts = get_pending_posts()
    logger.info(f"Найдено постов для отправки: {len(posts)}")

    for post in posts:
        (post_id, channel_id, media_type, media_file_id, text, text_entities_json,
         links_json, emojis_json, button_text, button_url) = post

        text_entities = deserialize_entities(text_entities_json)
        links = json.loads(links_json) if links_json else []
        emojis = json.loads(emojis_json) if emojis_json else []

        extra = ""
        if emojis:
            extra += "\n\n" + " ".join(emojis)
        if links:
            extra += "\n\n" + "\n".join(links)

        full_text = (text or "") + extra

        kb = None
        if button_text and button_url:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=button_text, url=button_url)
            ]])

        kwargs = {
            "chat_id": channel_id,
            "reply_markup": kb,
            "parse_mode": None,
        }
        if text_entities:
            kwargs["entities"] = text_entities

        try:
            if media_type == "photo" and media_file_id:
                await bot.send_photo(photo=media_file_id, caption=full_text, **kwargs)
            elif media_type == "animation" and media_file_id:
                await bot.send_animation(animation=media_file_id, caption=full_text, **kwargs)
            else:
                await bot.send_message(text=full_text, **kwargs)

            mark_sent(post_id)
            logger.info(f"✅ Пост #{post_id} отправлен в {channel_id}")
        except Exception as e:
            logger.exception(f"❌ Ошибка отправки поста #{post_id}: {e}")


async def weekly_subscription_check(bot):
    if not is_subscription_required():
        return

    channels = get_required_channels()
    if not channels:
        return

    user_ids = get_users_for_weekly_check()
    for uid in user_ids:
        missing = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=uid)
                ok = member.status in ("member", "administrator", "creator")
                set_subscription(uid, ch["chat_id"], ok)
                if not ok:
                    missing.append(ch)
            except Exception:
                missing.append(ch)

        if missing:
            text = (
                "🔒 <b>Появились новые каналы для подписки</b>\n\n"
                "Подпишитесь, чтобы бот продолжал работать:"
            )
            buttons = []
            for ch in missing:
                url = ch["url"]
                if not url.startswith("http"):
                    url = f"https://t.me/{url.lstrip('@')}"
                buttons.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=url)])
            buttons.append([InlineKeyboardButton(text="✅ Я подписался",
                                                 callback_data="check_subscription")])

            try:
                await bot.send_message(uid, text, parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            except TelegramForbiddenError:
                pass
            except Exception as e:
                logger.warning(f"Не удалось отправить weekly-сообщение {uid}: {e}")

        update_last_subscription_check(uid)


def start_scheduler(bot):
    scheduler.add_job(check_scheduled_posts, "interval", minutes=1, args=[bot])
    scheduler.add_job(weekly_subscription_check, "interval", hours=6, args=[bot])
    scheduler.start()
    logger.info("🚀 Планировщик запущен")