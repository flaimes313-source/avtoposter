from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


def main_menu(is_admin: bool = False):
    """Главное меню: 2 колонки."""
    rows = [
        [
            InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post"),
            InlineKeyboardButton(text="📢 Реклама", callback_data="create_ad"),
        ],
        [
            InlineKeyboardButton(text="📋 Мои посты", callback_data="list_posts"),
            InlineKeyboardButton(text="📡 Мои каналы", callback_data="my_channels"),
        ],
        [
            InlineKeyboardButton(text="🆘 Поддержка", callback_data="support"),
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
        ],
    ]
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def media_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼 Картинка", callback_data="media_photo"),
            InlineKeyboardButton(text="🎞 GIF", callback_data="media_animation"),
        ],
        [InlineKeyboardButton(text="📄 Только текст", callback_data="media_none")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")],
    ])


def skip_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")],
    ])


def skip_button_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Без кнопки", callback_data="skip_button")],
    ])


def channels_select_kb(channels, action_prefix="pick_channel"):
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
    buttons = []
    for chat_id, title in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ Удалить {title}",
                callback_data=f"del_channel:{chat_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")])
    buttons.append([InlineKeyboardButton(text="🔄 Обновить статус", callback_data="my_channels")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Задать вопрос", callback_data="support_write")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")],
    ])


def admin_panel_kb(subscription_on: bool, open_tickets: int):
    sub_text = "🟢 Обязательная подписка: ВКЛ" if subscription_on else "🔴 Обязательная подписка: ВЫКЛ"
    buttons = [
        [InlineKeyboardButton(text=f"❓ Вопросы ({open_tickets})", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text=sub_text, callback_data="admin_toggle_sub")],
        [InlineKeyboardButton(text="📡 Каналы подписки", callback_data="admin_required_channels")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tickets_list_kb(tickets):
    buttons = []
    for t in tickets:
        preview = (t["text"][:25] + "...") if len(t["text"]) > 25 else t["text"]
        buttons.append([
            InlineKeyboardButton(
                text=f"#{t['id']} от {t['user_id']} — {preview}",
                callback_data=f"admin_ticket:{t['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ticket_actions_kb(ticket_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"admin_ticket_reply:{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть", callback_data=f"admin_ticket_close:{ticket_id}")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_tickets")],
    ])


def required_channels_kb(channels):
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ Удалить {ch['title'] or ch['chat_id']}",
                callback_data=f"admin_del_req:{ch['chat_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="admin_add_req")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscription_check_kb(channels):
    """Клавиатура с кнопками-ссылками на каналы, на которые надо подписаться."""
    buttons = []
    for ch in channels:
        url = ch["url"]
        if not url.startswith("http"):
            url = f"https://t.me/{url.lstrip('@')}"
        buttons.append([
            InlineKeyboardButton(text=f"📢 {ch['title'] or ch['chat_id']}", url=url)
        ])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)