from aiogram import Router
from aiogram.types import Message

router = Router()

@router.channel_post()
async def channel_post_handler(message: Message):
    """Ловим посты в канале — можно использовать для логирования или авто-ответов."""
    pass