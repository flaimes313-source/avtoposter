from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated

from database import save_known_channel, remove_known_channel

router = Router()


@router.channel_post()
async def channel_post_handler(message: Message):
    """Любой пост в канале — запоминаем канал."""
    if message.chat and message.chat.title:
        save_known_channel(message.chat.id, message.chat.title)


@router.my_chat_member()
async def on_bot_membership_change(update: ChatMemberUpdated):
    """Реагируем на добавление/удаление бота в канал."""
    status = update.new_chat_member.status
    chat = update.chat
    if status in ("administrator", "member"):
        save_known_channel(chat.id, chat.title or str(chat.id))
    elif status in ("left", "kicked"):
        remove_known_channel(chat.id)