from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="📢 Рекламный пост", callback_data="create_ad")],
        [InlineKeyboardButton(text="📋 Мои посты", callback_data="list_posts")],
        [InlineKeyboardButton(text="🔍 Проверить каналы", callback_data="check_channels")],
    ])


def media_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Картинка", callback_data="media_photo")],
        [InlineKeyboardButton(text="🎞 GIF", callback_data="media_animation")],
        [InlineKeyboardButton(text="📄 Только текст", callback_data="media_none")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")],
    ])


def skip_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")],
    ])