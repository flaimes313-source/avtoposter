from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="📢 Рекламный пост", callback_data="create_ad")],
        [InlineKeyboardButton(text="📋 Мои посты", callback_data="list_posts")],
        [InlineKeyboardButton(text="📡 Мои каналы", callback_data="my_channels")],
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


def channels_select_kb(channels, action_prefix="pick_channel"):
    """Клавиатура для выбора канала.
    channels — список кортежей (chat_id, title).
    action_prefix — 'pick_channel' для обычного поста, 'pick_ad_channel' для рекламы.
    """
    buttons = []
    for chat_id, title in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 {title}",
                callback_data=f"{action_prefix}:{chat_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def my_channels_kb(channels):
    """Клавиатура управления каналами."""
    buttons = []
    for chat_id, title in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ Удалить {title}",
                callback_data=f"del_channel:{chat_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)