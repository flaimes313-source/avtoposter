from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from html import escape

from config import ADMIN_ID
from database import (
    is_subscription_required, toggle_subscription_required,
    get_open_support_messages, get_support_message, mark_support_answered,
    add_required_channel, get_required_channels, remove_required_channel,
    get_all_user_ids
)
from keyboards import (
    main_menu, admin_panel_kb, tickets_list_kb, ticket_actions_kb,
    required_channels_kb, skip_button_kb
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


class AdminForm(StatesGroup):
    waiting_reply_text = State()
    waiting_broadcast_media = State()
    waiting_broadcast_text = State()
    waiting_broadcast_button_name = State()
    waiting_broadcast_button_url = State()
    waiting_required_channel = State()


# ==================== ГЛАВНАЯ АДМИНКА ====================

@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.clear()

    sub_on = is_subscription_required()
    tickets = get_open_support_messages()
    text = (
        "⚙️ <b>Админ-панель</b>\n\n"
        "Управляйте вопросами, рассылками и обязательной подпиской."
    )
    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=admin_panel_kb(sub_on, len(tickets))
    )
    await call.answer()


# ==================== ВОПРОСЫ ====================

@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.clear()

    tickets = get_open_support_messages()
    if not tickets:
        text = "📭 Открытых вопросов нет."
    else:
        text = f"❓ <b>Открытые вопросы:</b> {len(tickets)}\n\nВыберите, чтобы открыть."

    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=tickets_list_kb(tickets) if tickets else admin_panel_kb(
            is_subscription_required(), 0
        )
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_ticket:"))
async def admin_ticket_open(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split(":")[1])
    t = get_support_message(ticket_id)
    if not t:
        await call.answer("Вопрос не найден", show_alert=True)
        return
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(
        f"❓ <b>Вопрос #{t['id']}</b>\n"
        f"От: {escape(t['username'] or '')} (<code>{t['user_id']}</code>)\n\n"
        f"«{escape(t['text'])}»",
        parse_mode="HTML",
        reply_markup=ticket_actions_kb(ticket_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_ticket_reply:"))
async def admin_ticket_reply(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split(":")[1])
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(
        "✍️ Напишите ответ одним сообщением — он уйдёт пользователю."
    )
    await state.set_state(AdminForm.waiting_reply_text)
    await call.answer()


@router.message(AdminForm.waiting_reply_text)
async def admin_reply_sent(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    t = get_support_message(ticket_id)

    try:
        await bot.send_message(
            chat_id=t["user_id"],
            text=(
                f"💬 <b>Ответ поддержки</b>\n\n"
                f"{escape(message.text or '')}"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить: <code>{escape(str(e))}</code>", parse_mode="HTML")
        return

    mark_support_answered(ticket_id)
    await state.clear()
    await message.answer("✅ Ответ отправлен пользователю.",
                         reply_markup=main_menu(True))


@router.callback_query(F.data.startswith("admin_ticket_close:"))
async def admin_ticket_close(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split(":")[1])
    mark_support_answered(ticket_id)
    await call.message.edit_text("✅ Вопрос закрыт без ответа.",
                                 reply_markup=admin_panel_kb(
                                     is_subscription_required(),
                                     len(get_open_support_messages())
                                 ))
    await call.answer()


# ==================== РАССЫЛКА ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text(
        "📣 <b>Рассылка</b>\n\n"
        "Отправьте картинку (или напишите <code>-</code>, если без картинки).",
        parse_mode="HTML"
    )
    await state.set_state(AdminForm.waiting_broadcast_media)
    await call.answer()


@router.message(AdminForm.waiting_broadcast_media)
async def broadcast_media(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.photo:
        await state.update_data(media_type="photo", media_file_id=message.photo[-1].file_id)
    elif message.text and message.text.strip() == "-":
        await state.update_data(media_type="none", media_file_id=None)
    else:
        await message.answer("❌ Отправьте картинку или `-`, чтобы пропустить.", parse_mode="Markdown")
        return
    await message.answer("Введите текст рассылки:")
    await state.set_state(AdminForm.waiting_broadcast_text)


@router.message(AdminForm.waiting_broadcast_text)
async def broadcast_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(text=message.text)
    await message.answer(
        "Введите название кнопки (или нажмите «Без кнопки»):",
        reply_markup=skip_button_kb()
    )
    await state.set_state(AdminForm.waiting_broadcast_button_name)


@router.callback_query(F.data == "skip_button", AdminForm.waiting_broadcast_button_name)
async def broadcast_no_button(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await state.update_data(button_text=None, button_url=None)
    await _do_broadcast(call.message, state, bot, edit=True)
    await call.answer()


@router.message(AdminForm.waiting_broadcast_button_name)
async def broadcast_button_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(button_text=message.text)
    await message.answer("Введите ссылку для кнопки (например, https://t.me/...):")
    await state.set_state(AdminForm.waiting_broadcast_button_url)


@router.message(AdminForm.waiting_broadcast_button_url)
async def broadcast_button_url(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(button_url=message.text)
    await _do_broadcast(message, state, bot)
    await state.clear()


async def _do_broadcast(message: Message, state: FSMContext, bot: Bot, edit: bool = False):
    data = await state.get_data()
    users = get_all_user_ids()

    kb = None
    if data.get("button_text") and data.get("button_url"):
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=data["button_text"], url=data["button_url"])
        ]])

    sent, failed = 0, 0
    for uid in users:
        try:
            if data.get("media_type") == "photo" and data.get("media_file_id"):
                await bot.send_photo(chat_id=uid, photo=data["media_file_id"],
                                     caption=data.get("text"), reply_markup=kb)
            else:
                await bot.send_message(chat_id=uid, text=data.get("text"), reply_markup=kb)
            sent += 1
        except Exception:
            failed += 1

    result = f"✅ Рассылка завершена.\nДоставлено: {sent}\nНе доставлено: {failed}"
    if edit:
        await message.edit_text(result)
    else:
        await message.answer(result, reply_markup=main_menu(True))


# ==================== ОБЯЗАТЕЛЬНАЯ ПОДПИСКА ====================

@router.callback_query(F.data == "admin_toggle_sub")
async def admin_toggle_sub(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    new_state = toggle_subscription_required()
    text = "🟢 Обязательная подписка включена" if new_state else "🔴 Обязательная подписка выключена"
    await call.answer(text, show_alert=True)
    await call.message.edit_reply_markup(
        reply_markup=admin_panel_kb(new_state, len(get_open_support_messages()))
    )


# ==================== КАНАЛЫ ПОДПИСКИ ====================

@router.callback_query(F.data == "admin_required_channels")
async def admin_required_channels(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    channels = get_required_channels()
    if not channels:
        text = "📡 <b>Каналы обязательной подписки</b>\n\nПока нет каналов."
    else:
        text = "📡 <b>Каналы обязательной подписки</b>\n\nВыберите, чтобы удалить:"
    await call.message.edit_text(text, parse_mode="HTML",
                                 reply_markup=required_channels_kb(channels))
    await call.answer()


@router.callback_query(F.data == "admin_add_req")
async def admin_add_req(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "➕ <b>Новый канал подписки</b>\n\n"
        "Отправьте данные в формате:\n"
        "<code>@username | Название | https://t.me/username</code>\n\n"
        "Или просто <code>@username</code>, если название и ссылку можно взять по username.",
        parse_mode="HTML"
    )
    await state.set_state(AdminForm.waiting_required_channel)
    await call.answer()


@router.message(AdminForm.waiting_required_channel)
async def admin_add_req_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    parts = [p.strip() for p in raw.split("|")]
    chat_id = parts[0]
    title = parts[1] if len(parts) > 1 else chat_id
    url = parts[2] if len(parts) > 2 else f"https://t.me/{chat_id.lstrip('@')}"

    add_required_channel(chat_id, title, url)
    await state.clear()
    channels = get_required_channels()
    await message.answer(
        f"✅ Канал «{escape(title)}» добавлен.",
        reply_markup=required_channels_kb(channels)
    )


@router.callback_query(F.data.startswith("admin_del_req:"))
async def admin_del_req(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    chat_id = call.data.split(":", 1)[1]
    remove_required_channel(chat_id)
    channels = get_required_channels()
    await call.message.edit_text(
        "✅ Канал удалён.",
        reply_markup=required_channels_kb(channels)
    )
    await call.answer()