import json
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, ChatMemberAdministrator,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from config import ADMIN_ID, DATABASE_URL
from database import (
    add_post, add_ad_post, get_user_timezone,
    get_user_posts, add_user_channel, get_user_channels, remove_user_channel
)
from keyboards import (
    main_reply_kb, media_type_kb, skip_kb, skip_button_kb,
    channels_select_kb, my_channels_kb
)

router = Router()


class PostForm(StatesGroup):
    waiting_media = State()
    waiting_text = State()
    waiting_links = State()
    waiting_emojis = State()
    waiting_button_name = State()
    waiting_button_url = State()
    waiting_calendar = State()
    waiting_time_only = State()
    waiting_channel_pick = State()
    waiting_ad_media = State()
    waiting_ad_text = State()
    waiting_ad_links = State()
    waiting_ad_emojis = State()
    waiting_ad_button_name = State()
    waiting_ad_button_url = State()
    waiting_ad_channel_pick = State()
    waiting_new_channel = State()


# ==================== ВСПОМОГАТЕЛЬНОЕ ====================

async def check_bot_in_channel(bot, channel_id: str) -> tuple[bool, str]:
    try:
        chat = await bot.get_chat(channel_id)
        member = await bot.get_chat_member(chat_id=channel_id, user_id=bot.id)
        title = escape(chat.title or str(chat.id))
        if member.status in ("administrator", "creator"):
            if isinstance(member, ChatMemberAdministrator) and member.can_post_messages:
                return True, f"✅ {title} — есть право публикации"
            return False, f"⚠️ {title} — админ, но без права публикации"
        return False, f"❌ {title} — бот не админ канала"
    except Exception as e:
        return False, f"❌ Ошибка: {escape(str(e))}"


# ==================== ПЕРЕСЛАННЫЕ СООБЩЕНИЯ ====================

@router.message(F.forward_from_chat)
async def get_forwarded_channel_id(message: Message, state: FSMContext):
    chat = message.forward_from_chat
    title = chat.title or str(chat.id)
    channel_id = str(chat.id)

    current_state = await state.get_state()

    await message.answer(
        f"📢 Канал: <b>{escape(title)}</b>\n"
        f"🆔 ID: <code>{channel_id}</code>",
        parse_mode="HTML"
    )

    if current_state == PostForm.waiting_new_channel.state:
        add_user_channel(message.from_user.id, channel_id, title)
        await state.clear()
        channels = get_user_channels(message.from_user.id)
        await message.answer(
            f"✅ Канал «{escape(title)}» добавлен в ваш список!",
            reply_markup=my_channels_kb(channels),
            parse_mode="HTML"
        )


# ==================== /debug ====================

@router.message(F.text == "/debug")
async def debug_db(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, channel_id, media_type, scheduled_time, is_sent
        FROM posts ORDER BY id DESC LIMIT 15
    """)
    rows = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS c FROM posts WHERE is_sent = 0")
    pending = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM posts WHERE is_sent = 1")
    sent = cur.fetchone()["c"]

    cur.execute("SELECT chat_id, title FROM user_channels WHERE user_id = %s",
                (message.from_user.id,))
    channels = cur.fetchall()

    conn.close()

    now_utc = datetime.now(timezone.utc).isoformat()
    lines = [
        f"🕒 <b>Сейчас UTC:</b> <code>{escape(now_utc)}</code>",
        f"📊 Не отправлено: <b>{pending}</b>",
        f"📊 Отправлено: <b>{sent}</b>",
        f"📡 Моих каналов: <b>{len(channels)}</b>\n",
        "<b>Последние 15 постов:</b>"
    ]
    if not rows:
        lines.append("📭 Таблица posts пуста")
    else:
        for r in rows:
            status = "✅" if r["is_sent"] else "⏳"
            lines.append(
                f"{status} #{r['id']} | ch=<code>{escape(str(r['channel_id']))}</code>\n"
                f"    type={escape(str(r['media_type']))} | "
                f"time=<code>{escape(str(r['scheduled_time']))}</code>"
            )
    await message.answer("\n".join(lines), parse_mode="HTML")


# ==================== МОИ КАНАЛЫ ====================

@router.message(F.text == "📡 Мои каналы")
async def my_channels_menu(message: Message, state: FSMContext, bot):
    await state.clear()
    channels = get_user_channels(message.from_user.id)

    if not channels:
        text = (
            "📡 <b>Мои каналы</b>\n\n"
            "У вас пока нет добавленных каналов.\n\n"
            "Нажмите «➕ Добавить канал», затем перешлите боту любое "
            "сообщение из нужного канала."
        )
        kb = my_channels_kb([])
    else:
        lines = ["📡 <b>Мои каналы</b>\n"]
        for chat_id, title in channels:
            ok, msg = await check_bot_in_channel(bot, chat_id)
            lines.append(f"• {msg}")
        lines.append("\nВыберите канал для удаления или добавьте новый:")
        text = "\n".join(lines)
        kb = my_channels_kb(channels)

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "refresh_channels")
async def refresh_channels(call: CallbackQuery, state: FSMContext, bot):
    await call.answer("🔄 Обновлено")
    try:
        await call.message.delete()
    except Exception:
        pass
    await my_channels_menu(call.message, state, bot)


@router.callback_query(F.data == "add_channel")
async def add_channel_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "➕ <b>Добавление канала</b>\n\n"
        "1. Убедитесь, что бот добавлен в канал как админ с правом "
        "«Публикация сообщений».\n"
        "2. Перешлите боту любое сообщение из этого канала.\n\n"
        "Бот сам определит ID и сохранит канал в ваш список.",
        parse_mode="HTML"
    )
    await state.set_state(PostForm.waiting_new_channel)
    await call.answer()


@router.callback_query(F.data.startswith("del_channel:"))
async def delete_channel(call: CallbackQuery, state: FSMContext):
    chat_id = call.data.split(":", 1)[1]
    remove_user_channel(call.from_user.id, chat_id)
    channels = get_user_channels(call.from_user.id)
    await call.message.edit_text("✅ Канал удалён из списка.",
                                 reply_markup=my_channels_kb(channels))
    await call.answer()


# ==================== СОЗДАНИЕ ПОСТА ====================

@router.message(F.text == "📝 Создать пост")
async def create_post_start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(is_ad=False)
    await message.answer("Выберите тип медиа:", reply_markup=media_type_kb())


@router.callback_query(F.data.startswith("media_"))
async def media_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("is_ad"):
        return

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
    links = [l.strip() for l in (message.text or "").split("\n") if l.strip()][:3]
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
        "🔘 Добавить кнопку под постом?\n\n"
        "Напишите её название или нажмите «Без кнопки»:",
        reply_markup=skip_button_kb()
    )
    await state.set_state(PostForm.waiting_button_name)
    await call.answer()


@router.message(PostForm.waiting_emojis)
async def emojis_received(message: Message, state: FSMContext):
    await state.update_data(emojis=(message.text or "").split())
    await message.answer(
        "🔘 Добавить кнопку под постом?\n\n"
        "Напишите её название или нажмите «Без кнопки»:",
        reply_markup=skip_button_kb()
    )
    await state.set_state(PostForm.waiting_button_name)


@router.callback_query(F.data == "skip_button", PostForm.waiting_button_name)
async def skip_button(call: CallbackQuery, state: FSMContext):
    await state.update_data(button_text=None, button_url=None)
    await call.message.edit_text(
        "📅 Выберите дату публикации:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PostForm.waiting_calendar)
    await call.answer()


@router.message(PostForm.waiting_button_name)
async def button_name_received(message: Message, state: FSMContext):
    await state.update_data(button_text=message.text)
    await message.answer("Введите ссылку для кнопки (например, https://t.me/...):")
    await state.set_state(PostForm.waiting_button_url)


@router.message(PostForm.waiting_button_url)
async def button_url_received(message: Message, state: FSMContext):
    await state.update_data(button_url=message.text)
    await message.answer(
        "📅 Выберите дату публикации:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PostForm.waiting_calendar)


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
        datetime.strptime((message.text or "").strip(), "%H:%M")
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

    channels = get_user_channels(message.from_user.id)
    if not channels:
        await message.answer(
            "❌ У вас нет добавленных каналов.\n\n"
            "Добавьте канал: «📡 Мои каналы» → «➕ Добавить канал».",
            reply_markup=main_reply_kb(message.from_user.id == ADMIN_ID)
        )
        await state.clear()
        return

    await message.answer(
        f"✅ Время:\n"
        f"🕒 Локально ({escape(tz_name)}): <b>{local_dt.strftime('%Y-%m-%d %H:%M')}</b>\n"
        f"🌐 UTC: <b>{utc_dt.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
        f"Выберите канал для публикации:",
        parse_mode="HTML",
        reply_markup=channels_select_kb(channels, action_prefix="pick_channel")
    )
    await state.set_state(PostForm.waiting_channel_pick)


@router.callback_query(F.data.startswith("pick_channel:"))
async def pick_channel(call: CallbackQuery, state: FSMContext):
    channel_id = call.data.split(":", 1)[1]
    data = await state.get_data()

    add_post(
        user_id=call.from_user.id,
        channel_id=channel_id,
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        text=data.get("text"),
        links=json.dumps(data.get("links", [])),
        emojis=json.dumps(data.get("emojis", [])),
        button_text=data.get("button_text"),
        button_url=data.get("button_url"),
        scheduled_time_utc=data.get("scheduled_time")
    )
    await state.clear()
    await call.message.edit_text(
        "✅ Пост создан и запланирован!",
        reply_markup=main_reply_kb(call.from_user.id == ADMIN_ID)
    )
    await call.answer()


# ==================== СПИСОК ПОСТОВ ====================

@router.message(F.text == "📋 Мои посты")
async def list_posts(message: Message):
    rows = get_user_posts(message.from_user.id)
    if not rows:
        await message.answer("📭 У вас пока нет постов.")
        return

    tz_name = get_user_timezone(message.from_user.id)
    user_tz = ZoneInfo(tz_name)
    lines = ["📋 <b>Ваши последние посты:</b>\n"]
    for r in rows:
        utc_dt = r["scheduled_time"]
        if isinstance(utc_dt, str):
            utc_dt = datetime.fromisoformat(utc_dt)
        local_dt = utc_dt.astimezone(user_tz)
        status = "✅ отправлен" if r["is_sent"] else "⏳ ожидает"
        preview = escape((r["text"] or "")[:30].replace("\n", " "))
        lines.append(
            f"#{r['id']} | {status}\n"
            f"  📢 {escape(str(r['channel_id']))}\n"
            f"  🕒 {local_dt.strftime('%Y-%m-%d %H:%M')} ({escape(tz_name)})\n"
            f"  📝 {preview}...\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


# ==================== РЕКЛАМНЫЙ ПОСТ ====================

@router.message(F.text == "📢 Реклама")
async def create_ad_start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(is_ad=True)
    await message.answer("Выберите тип медиа для рекламы:", reply_markup=media_type_kb())


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
    links = [l.strip() for l in (message.text or "").split("\n") if l.strip()][:3]
    await state.update_data(links=links)
    await message.answer("Введите эмодзи. Или «Пропустить»:", reply_markup=skip_kb())
    await state.set_state(PostForm.waiting_ad_emojis)


@router.callback_query(F.data == "skip", PostForm.waiting_ad_emojis)
async def ad_skip_emojis(call: CallbackQuery, state: FSMContext):
    await state.update_data(emojis=[])
    await call.message.edit_text(
        "🔘 Добавить кнопку под рекламой?\n\n"
        "Напишите её название или нажмите «Без кнопки»:",
        reply_markup=skip_button_kb()
    )
    await state.set_state(PostForm.waiting_ad_button_name)
    await call.answer()


@router.message(PostForm.waiting_ad_emojis)
async def ad_emojis_received(message: Message, state: FSMContext):
    await state.update_data(emojis=(message.text or "").split())
    await message.answer(
        "🔘 Добавить кнопку под рекламой?\n\n"
        "Напишите её название или нажмите «Без кнопки»:",
        reply_markup=skip_button_kb()
    )
    await state.set_state(PostForm.waiting_ad_button_name)


@router.callback_query(F.data == "skip_button", PostForm.waiting_ad_button_name)
async def ad_skip_button(call: CallbackQuery, state: FSMContext):
    await state.update_data(button_text=None, button_url=None)
    channels = get_user_channels(call.from_user.id)
    if not channels:
        await call.message.edit_text(
            "❌ У вас нет добавленных каналов. Добавьте через «📡 Мои каналы».",
            reply_markup=main_reply_kb(call.from_user.id == ADMIN_ID)
        )
        await state.clear()
        await call.answer()
        return

    await call.message.edit_text(
        "Выберите канал для публикации рекламы:",
        reply_markup=channels_select_kb(channels, action_prefix="pick_ad_channel")
    )
    await state.set_state(PostForm.waiting_ad_channel_pick)
    await call.answer()


@router.message(PostForm.waiting_ad_button_name)
async def ad_button_name_received(message: Message, state: FSMContext):
    await state.update_data(button_text=message.text)
    await message.answer("Введите ссылку для кнопки (например, https://t.me/...):")
    await state.set_state(PostForm.waiting_ad_button_url)


@router.message(PostForm.waiting_ad_button_url)
async def ad_button_url_received(message: Message, state: FSMContext):
    await state.update_data(button_url=message.text)
    channels = get_user_channels(message.from_user.id)
    if not channels:
        await message.answer(
            "❌ У вас нет добавленных каналов. Добавьте через «📡 Мои каналы».",
            reply_markup=main_reply_kb(message.from_user.id == ADMIN_ID)
        )
        await state.clear()
        return

    await message.answer(
        "Выберите канал для публикации рекламы:",
        reply_markup=channels_select_kb(channels, action_prefix="pick_ad_channel")
    )
    await state.set_state(PostForm.waiting_ad_channel_pick)


@router.callback_query(F.data.startswith("pick_ad_channel:"))
async def pick_ad_channel(call: CallbackQuery, state: FSMContext, bot):
    channel_id = call.data.split(":", 1)[1]
    data = await state.get_data()

    add_ad_post(
        user_id=call.from_user.id,
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        text=data.get("text"),
        links=json.dumps(data.get("links", [])),
        emojis=json.dumps(data.get("emojis", [])),
        button_text=data.get("button_text"),
        button_url=data.get("button_url")
    )

    links = data.get("links", [])
    emojis = data.get("emojis", [])
    full_text = (data.get("text") or "")
    if emojis:
        full_text += "\n\n" + " ".join(emojis)
    if links:
        full_text += "\n\n" + "\n".join(links)

    kb = None
    if data.get("button_text") and data.get("button_url"):
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=data["button_text"], url=data["button_url"])
        ]])

    try:
        if data.get("media_type") == "photo" and data.get("media_file_id"):
            await bot.send_photo(chat_id=channel_id, photo=data["media_file_id"],
                                 caption=full_text, reply_markup=kb)
        elif data.get("media_type") == "animation" and data.get("media_file_id"):
            await bot.send_animation(chat_id=channel_id, animation=data["media_file_id"],
                                     caption=full_text, reply_markup=kb)
        else:
            await bot.send_message(chat_id=channel_id, text=full_text, reply_markup=kb)

        await call.message.edit_text(
            "✅ Рекламный пост опубликован!",
            reply_markup=main_reply_kb(call.from_user.id == ADMIN_ID)
        )
    except Exception as e:
        await call.message.edit_text(
            f"❌ Ошибка публикации: <code>{escape(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=main_reply_kb(call.from_user.id == ADMIN_ID)
        )

    await state.clear()
    await call.answer()