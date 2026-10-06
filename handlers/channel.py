from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated

router = Router()


@router.channel_post()
async def channel_post_handler(message: Message):
    """Ловим посты в канале — можно использовать для авто-реакций.
    Сейчас ничего не делаем, канал пользователь добавляет через «📡 Мои каналы»."""
    pass


@router.my_chat_member()
async def on_bot_membership_change(update: ChatMemberUpdated):
    """Реагируем на добавление/удаление бота в канал.
    Запоминать здесь канал в user_channels нельзя — мы не знаем, кто владелец.
    Пользователь сам добавит канал через «📡 Мои каналы» → «➕ Добавить канал»."""
    pass