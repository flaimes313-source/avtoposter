from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="📢 Рекламный пост", callback_data="create_ad")],
        [InlineKeyboardButton(text="📋 Мои посты", callback_data="list_posts")],
    ])
    return kb

def media_type_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Картинка", callback_data="media_photo")],
        [InlineKeyboardButton(text="🎞 GIF", callback_data="media_animation")],
        [InlineKeyboardButton(text="📄 Только текст", callback_data="media_none")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")],
    ])
    return kb

def skip_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")],
    ])
    return kb