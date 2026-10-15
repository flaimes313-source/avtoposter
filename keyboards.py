from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)


# ==================== REPLY (главное меню) ====================

def main_reply_kb(is_admin: bool = False):
    """Главное меню — большие кнопки внизу экрана, по 2 в ряд."""
    rows = [
        [KeyboardButton(text="📝 Создать пост"), KeyboardButton(text="📢 Реклама")],
        [KeyboardButton(text="📋 Мои посты"),    KeyboardButton(text="📡 Мои каналы")],
        [KeyboardButton(text="ℹ️ О боте"),       KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🆘 Поддержка")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True
    )


def remove_kb():
    return ReplyKeyboardRemove()


# ==================== INLINE ====================

def settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕒 Часовой пояс", callback_data="settings_timezone")],
        [InlineKeyboardButton(text="⬅ Закрыть", callback_data="settings_close")],
    ])


def timezone_presets_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Москва", callback_data="tz_set:Europe/Moscow"),
            InlineKeyboardButton(text="🇰🇿 Алматы", callback_data="tz_set:Asia/Almaty"),
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Берлин", callback_data="tz_set:Europe/Berlin"),
            InlineKeyboardButton(text="🇺🇸 Нью-Йорк", callback_data="tz_set:America/New_York"),
        ],
        [InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="tz_manual")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="settings_back")],
    ])


def media_type_kb(is_ad: bool = False):
    """Разные префиксы callback, чтобы обычный пост и реклама не пересекались."""
    prefix = "admedia_" if is_ad else "media_"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼 Картинка", callback_data=f"{prefix}photo"),
            InlineKeyboardButton(text="🎞 GIF",      callback_data=f"{prefix}animation"),
        ],
        [InlineKeyboardButton(text="📄 Только текст", callback_data=f"{prefix}none")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])


def skip_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])


def skip_button_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Без кнопки", callback_data="skip_button")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
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
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
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
    buttons.append([InlineKeyboardButton(text="🔄 Обновить статус", callback_data="refresh_channels")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Задать вопрос", callback_data="support_write")],
    ])


def admin_panel_kb(subscription_on: bool, open_tickets: int):
    sub_text = "🟢 Подписка: ВКЛ" if subscription_on else "🔴 Подписка: ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"❓ Вопросы ({open_tickets})", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text=sub_text, callback_data="admin_toggle_sub")],
        [InlineKeyboardButton(text="📡 Каналы подписки", callback_data="admin_required_channels")],
    ])


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