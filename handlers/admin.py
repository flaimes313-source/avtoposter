import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatMemberAdministrator
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from config import ADMIN_ID
from database import (
    add_post, add_ad_post, get_user_timezone, set_user_timezone,
    get_user_posts, get_known_channels
)
from keyboards import main_menu, media_type_kb, skip_kb

router = Router()


class PostForm(StatesGroup):
    waiting_media = State()
    waiting_text = State()
    waiting_links = State()
    waiting_emojis = State()
    waiting_calendar = State()
    waiting_time_only = State()
    waiting_channel = State()
    waiting_ad_media = State()
    waiting_ad_text = State()
    waiting_ad_links = State()
    waiting_ad_emojis = State()
    waiting_ad_channel = State()
    waiting_timezone = State()
    waiting_channel_to_check = State()


# ==================== ВСПОМОГАТЕЛЬНОЕ ====================

async def check_bot_in_channel(bot, channel_id: str) -> tuple[bool, str]:
    """Проверяет, что бот — админ канала с правом публикации."""
    try:
        chat = await bot.get_chat(channel_id)
        member = await bot.get_chat_member(chat_id=channel_id, user_id=bot.id)

        if member.status in ("administrator", "creator"):
            if isinstance(member, ChatMemberAdministrator) and member.can_post_messages:
                return True, f"✅ {chat.title} — есть право публикации"
            return False, f"⚠️ {chat.title} — админ, но без права публикации"
        return False, f"❌ {chat.title} — бот не админ канала"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"


# ==================== СТАРТ ====================

@router.message(F.text == "/start")
async def start_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return
    tz = get_user_timezone(message.from_user.id)
    await message.answer(
        f"👋 Добро пожаловать в панель управления автопостингом!\n"
        f"🕒 Ваш часовой пояс: <b>{tz}</b>\n\n"
        f"Сменить пояс: /timezone",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("👋 Главное меню", reply_markup=main_menu())
    await call.answer()


# ==================== ЧАСОВОЙ ПОЯС ====================

@router.message(F.text == "/timezone")
async def timezone_cmd(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    current = get_user_timezone(message.from_user.id)
    await message.answer(
        f"🕒 Текущий пояс: <b>{current}</b>\n\n"
        f"Введите новый часовой пояс в формате IANA, например:\n"
        f"<code>Europe/Moscow</code>\n"
        f"<code>Europe/Berlin</code>\n"
        f"<code>Asia/Almaty</code>",
        parse_mode="HTML"
    )
    await state.set_state(PostForm.waiting_timezone)


@router.message(PostForm.waiting_timezone)
async def timezone_set(message: Message, state: FSMContext):
    tz_name = message.text.strip()
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        await message.answer(
            "❌ Неизвестный пояс. Пример: <code>Europe/Moscow</code>",
            parse_mode="HTML"
        )
        return
    set_user_timezone(message.from_user.id, tz_name)
    await state.clear()
    await message.answer(f"✅ Пояс установлен: <b>{tz_name}</b>",
                         reply_markup=main_menu(), parse_mode="HTML")


# ==================== ПРОВЕРКА КАНАЛОВ ====================

@router.callback_query(F.data == "check_channels")
async def check_channels_menu(call: CallbackQuery, state: FSMContext, bot):
    known = get_known_channels()

    lines = ["🔍 <b>Проверка каналов</b>\n"]

    if known:
        lines.append("📌 Известные каналы (в которых был замечен бот):")
        for chat_id, title in known:
            ok, msg = await check_bot_in_channel(bot, chat_id)
            lines.append(f"• {msg}")
        lines.append("")
    else:
        lines.append("📭 Пока нет известных каналов.\n")

    lines.append(
        "Чтобы проверить конкретный канал, отправьте его ID или @username.\n"
        "Например: <code>-1001234567890</code> или <code>@my_channel</code>"
    )

    await call.message.edit_text("\n".join(lines), parse_mode="HTML")
    await state.set_state(PostForm.waiting_channel_to_check)
    await call.answer()


@router.message(PostForm.waiting_channel_to_check)
async def check_single_channel(message: Message, state: FSMContext, bot):
    channel_id = message.text.strip()
    ok, msg = await check_bot_in_channel(bot, channel_id)
    await message.answer(msg, reply_markup=main_menu())
    await state.clear()


# ==================== СОЗДАНИЕ ПОСТА ====================

@router.callback_query(F.data == "create_post")
async def create_post_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Выберите тип медиа:", reply_markup=media_type_kb())
    await call.answer()


@router.callback_query(F.data.startswith("media_"))
async def media_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("is_ad"):
        return  # реклама обрабатывается отдельно

    media_type = call.data.replace("media_", "")
    await state.update_data(media_type=media_type, is_ad=False)

    if media_type == "none":
        await state.update_data(media_file_id=None)
        await call.message.edit_text("Введите текст поста:")
        await state.set_state(PostForm.waiting_text)
    else:
        await call.message.edit_text(
            f"Отправьте {'картинку' if media_type == 'photo' else 'GIF'}:"
        )
        await state.set_state(PostForm.waiting_media)
    await call.answer()


@router.message(PostForm.waiting_media)
async def media_received(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
    else:
        await message.answer("❌ Отправьте картинку или GIF.")
        return
    await state.update_data(media_file_id=file_id, media_type=media_type)
    await message.answer("✅ Медиа сохранено. Введите текст поста:")
    await state.set_state(PostForm.waiting_text)


@router.message(PostForm.waiting_text)
async def text_received(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "Введите ссылки (до 3, каждая с новой строки). Или «Пропустить»:",
        reply_markup=skip_kb()
    )
    await state.set_state(PostForm.waiting_links)


@router.callback_query(F.data == "skip", PostForm.waiting_links)
async def skip_links(call: CallbackQuery, state: FSMContext):
    await state.update_data(links=[])
    await call.message.edit_text(
        "Введите эмодзи (через пробел). Или «Пропустить»:",
        reply_markup=skip_kb()
    )
    await state.set_state(PostForm.waiting_emojis)
    await call.answer()


@router.message(PostForm.waiting_links)
async def links_received(message: Message, state: FSMContext):
    links = [l.strip() for l in message.text.split("\n") if l.strip()][:3]
    await state.update_data(links=links)
    await message.answer(
        "Введите эмодзи (через пробел). Или «Пропустить»:",
        reply_markup=skip_kb()
    )
    await state.set_state(PostForm.waiting_emojis)


@router.callback_query(F.data == "skip", PostForm.waiting_emojis)
async def skip_emojis(call: CallbackQuery, state: FSMContext):
    await state.update_data(emojis=[])
    await call.message.edit_text(
        "📅 Выберите дату публикации:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PostForm.waiting_calendar)
    await call.answer()


@router.message(PostForm.waiting_emojis)
async def emojis_received(message: Message, state: FSMContext):
    emojis = message.text.split()
    await state.update_data(emojis=emojis)
    await message.answer(
        "📅 Выберите дату публикации:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PostForm.waiting_calendar)


# --- Календарь ---

@router.callback_query(PostForm.waiting_calendar, SimpleCalendarCallback.filter())
async def process_calendar(call: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(call, callback_data)
    if selected:
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await call.message.edit_text(
            f"✅ Дата: <b>{date.strftime('%Y-%m-%d')}</b>\n\n"
            f"Введите время в формате <code>ЧЧ:ММ</code> (например, <code>18:30</code>):",
            parse_mode="HTML"
        )
        await state.set_state(PostForm.waiting_time_only)
        await call.answer()


@router.message(PostForm.waiting_time_only)
async def time_only_received(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
    except ValueError:
        await message.answer("❌ Формат: <code>ЧЧ:ММ</code>", parse_mode="HTML")
        return

    data = await state.get_data()
    date_str = data["selected_date"]
    local_dt = datetime.strptime(f"{date_str} {message.text.strip()}", "%Y-%m-%d %H:%M")

    tz_name = get_user_timezone(message.from_user.id)
    user_tz = ZoneInfo(tz_name)
    local_dt = local_dt.replace(tzinfo=user_tz)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    await state.update_data(scheduled_time=utc_dt.isoformat())
    await message.answer(
        f"✅ Время:\n"
        f"🕒 Локально ({tz_name}): <b>{local_dt.strftime('%Y-%m-%d %H:%M')}</b>\n"
        f"🌐 UTC: <b>{utc_dt.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
        f"Введите ID канала (например, <code>-1001234567890</code> или <code>@username</code>):",
        parse_mode="HTML"
    )
    await state.set_state(PostForm.waiting_channel)


@router.message(PostForm.waiting_channel)
async def channel_received(message: Message, state: FSMContext, bot):
    channel_id = message.text.strip()

    ok, msg = await check_bot_in_channel(bot, channel_id)
    if not ok:
        await message.answer(f"{msg}\n\nПопробуйте снова:")
        return

    data = await state.get_data()
    add_post(
        user_id=message.from_user.id,
        channel_id=channel_id,
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        text=data.get("text"),
        links=json.dumps(data.get("links", [])),
        emojis=json.dumps(data.get("emojis", [])),
        scheduled_time_utc=data.get("scheduled_time")
    )
    await state.clear()
    await message.answer("✅ Пост создан и запланирован!", reply_markup=main_menu())


# ==================== СПИСОК ПОСТОВ ====================

@router.callback_query(F.data == "list_posts")
async def list_posts(call: CallbackQuery):
    rows = get_user_posts(call.from_user.id)
    if not rows:
        await call.message.edit_text("📭 У вас пока нет постов.", reply_markup=main_menu())
        await call.answer()
        return

    tz_name = get_user_timezone(call.from_user.id)
    user_tz = ZoneInfo(tz_name)
    lines = ["📋 <b>Ваши последние посты:</b>\n"]
    for pid, channel_id, media_type, text, scheduled_iso, is_sent in rows:
        utc_dt = datetime.fromisoformat(scheduled_iso)
        local_dt = utc_dt.astimezone(user_tz)
        status = "✅ отправлен" if is_sent else "⏳ ожидает"
        preview = (text or "")[:30].replace("\n", " ")
        lines.append(
            f"#{pid} | {status}\n"
            f"  📢 {channel_id}\n"
            f"  🕒 {local_dt.strftime('%Y-%m-%d %H:%M')} ({tz_name})\n"
            f"  📝 {preview}...\n"
        )
    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=main_menu())
    await call.answer()


# ==================== РЕКЛАМНЫЙ ПОСТ ====================

@router.callback_query(F.data == "create_ad")
async def create_ad_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(is_ad=True)
    await call.message.edit_text("Выберите тип медиа для рекламы:", reply_markup=media_type_kb())
    await call.answer()


@router.callback_query(F.data.startswith("media_"))
async def ad_media_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("is_ad"):
        return

    media_type = call.data.replace("media_", "")
    await state.update_data(media_type=media_type)

    if media_type == "none":
        await state.update_data(media_file_id=None)
        await call.message.edit_text("Введите текст рекламного поста:")
        await state.set_state(PostForm.waiting_ad_text)
    else:
        await call.message.edit_text(
            f"Отправьте {'картинку' if media_type == 'photo' else 'GIF'}:"
        )
        await state.set_state(PostForm.waiting_ad_media)
    await call.answer()


@router.message(PostForm.waiting_ad_media)
async def ad_media_received(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
    else:
        await message.answer("❌ Отправьте картинку или GIF.")
        return
    await state.update_data(media_file_id=file_id, media_type=media_type)
    await message.answer("✅ Медиа сохранено. Введите текст рекламного поста:")
    await state.set_state(PostForm.waiting_ad_text)


@router.message(PostForm.waiting_ad_text)
async def ad_text_received(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Введите ссылки (до 3). Или «Пропустить»:", reply_markup=skip_kb())
    await state.set_state(PostForm.waiting_ad_links)


@router.callback_query(F.data == "skip", PostForm.waiting_ad_links)
async def ad_skip_links(call: CallbackQuery, state: FSMContext):
    await state.update_data(links=[])
    await call.message.edit_text("Введите эмодзи. Или «Пропустить»:", reply_markup=skip_kb())
    await state.set_state(PostForm.waiting_ad_emojis)
    await call.answer()


@router.message(PostForm.waiting_ad_links)
async def ad_links_received(message: Message, state: FSMContext):
    links = [l.strip() for l in message.text.split("\n") if l.strip()][:3]
    await state.update_data(links=links)
    await message.answer("Введите эмодзи. Или «Пропустить»:", reply_markup=skip_kb())
    await state.set_state(PostForm.waiting_ad_emojis)


@router.callback_query(F.data == "skip", PostForm.waiting_ad_emojis)
async def ad_skip_emojis(call: CallbackQuery, state: FSMContext):
    await state.update_data(emojis=[])
    await call.message.edit_text(
        "Введите ID канала для рекламы (например, <code>-1001234567890</code> или <code>@username</code>):",
        parse_mode="HTML"
    )
    await state.set_state(PostForm.waiting_ad_channel)
    await call.answer()


@router.message(PostForm.waiting_ad_emojis)
async def ad_emojis_received(message: Message, state: FSMContext):
    await state.update_data(emojis=message.text.split())
    await message.answer(
        "Введите ID канала для рекламы (например, <code>-1001234567890</code> или <code>@username</code>):",
        parse_mode="HTML"
    )
    await state.set_state(PostForm.waiting_ad_channel)


@router.message(PostForm.waiting_ad_channel)
async def ad_channel_received(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    channel_id = message.text.strip()

    ok, msg = await check_bot_in_channel(bot, channel_id)
    if not ok:
        await message.answer(f"{msg}\n\nПопробуйте снова:")
        return

    add_ad_post(
        user_id=message.from_user.id,
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        text=data.get("text"),
        links=json.dumps(data.get("links", [])),
        emojis=json.dumps(data.get("emojis", []))
    )

    links = data.get("links", [])
    emojis = data.get("emojis", [])
    full_text = (data.get("text") or "")
    if emojis:
        full_text += "\n\n" + " ".join(emojis)
    if links:
        full_text += "\n\n" + "\n".join(links)

    try:
        if data.get("media_type") == "photo" and data.get("media_file_id"):
            await bot.send_photo(chat_id=channel_id, photo=data["media_file_id"], caption=full_text)
        elif data.get("media_type") == "animation" and data.get("media_file_id"):
            await bot.send_animation(chat_id=channel_id, animation=data["media_file_id"], caption=full_text)
        else:
            await bot.send_message(chat_id=channel_id, text=full_text)
        await message.answer("✅ Рекламный пост опубликован!", reply_markup=main_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка публикации: <code>{e}</code>", parse_mode="HTML")

    await state.clear()