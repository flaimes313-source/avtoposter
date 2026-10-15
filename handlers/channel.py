from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from config import ADMIN_ID

router = Router()


@router.channel_post()
async def channel_post_handler(message: Message):
    """Ловим посты в канале. Сейчас ничего не делаем — канал добавляется
    пользователем вручную через «📡 Мои каналы» → «➕ Добавить канал»."""
    pass


@router.my_chat_member()
async def on_bot_membership_change(update: ChatMemberUpdated):
    """Уведомляем админа, когда бота добавляют или удаляют из канала."""
    status = update.new_chat_member.status
    chat = update.chat

    try:
        if status in ("administrator", "member"):
            await update.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📡 Бот добавлен в канал: <b>{chat.title}</b>\n"
                    f"🆔 ID: <code>{chat.id}</code>\n\n"
                    f"Чтобы добавить канал в свой список — откройте "
                    f"«📡 Мои каналы» → «➕ Добавить канал» и перешлите "
                    f"сюда любое сообщение из этого канала."
                ),
                parse_mode="HTML"
            )
        elif status in ("left", "kicked"):
            await update.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Бот удалён из канала: <b>{chat.title}</b>",
                parse_mode="HTML"
            )
    except Exception:
        pass