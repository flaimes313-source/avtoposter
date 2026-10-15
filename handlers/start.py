from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import get_user_timezone, set_user_timezone
from keyboards import (
    main_reply_kb, settings_kb, timezone_presets_kb
)

router = Router()


class SettingsForm(StatesGroup):
    waiting_timezone = State()


# ==================== /start ====================

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tz = get_user_timezone(message.from_user.id)
    is_admin = message.from_user.id == ADMIN_ID

    text = (
        f"👋 Привет, {escape(message.from_user.first_name or 'друг')}!\n\n"
        f"🏠 <b>Главное меню</b>\n"
        f"🕒 Ваш часовой пояс: <b>{escape(tz)}</b>\n\n"
        f"Планируйте посты в Telegram-каналы, отправляйте рекламу "
        f"и управляйте каналами."
    )
    await message.answer(text, reply_markup=main_reply_kb(is_admin), parse_mode="HTML")


@router.message(F.text == "🏠 Главное меню")
async def reply_main_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=main_reply_kb(is_admin),
        parse_mode="HTML"
    )


# ==================== О БОТЕ ====================

@router.message(F.text == "ℹ️ О боте")
async def reply_about(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "Этот бот помогает автоматически публиковать посты в ваши "
        "Telegram-каналы по расписанию.\n\n"
        "<b>Что умеет:</b>\n"
        "• 📝 Создавать отложенные посты (картинка/GIF/текст)\n"
        "• 🔗 Добавлять до 3 ссылок и эмодзи\n"
        "• 🔘 Прикреплять кнопку с названием и ссылкой\n"
        "• 📢 Отправлять рекламные посты в другие каналы\n"
        "• 📡 Хранить список ваших каналов\n"
        "• 🆘 Поддержка — задайте вопрос, админ ответит\n\n"
        "<b>Как начать:</b>\n"
        "1. Добавьте бота в свой канал как администратора "
        "с правом «Публикация сообщений».\n"
        "2. Откройте «📡 Мои каналы» → «➕ Добавить канал» → "
        "перешлите сообщение из канала.\n"
        "3. Нажмите «📝 Создать пост» и заполните шаги.\n"
    )
    await message.answer(text, parse_mode="HTML")


# ==================== НАСТРОЙКИ ====================

@router.message(F.text == "⚙️ Настройки")
async def reply_settings(message: Message, state: FSMContext):
    await state.clear()
    tz = get_user_timezone(message.from_user.id)
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"🕒 Часовой пояс: <b>{escape(tz)}</b>",
        parse_mode="HTML",
        reply_markup=settings_kb()
    )


@router.callback_query(F.data == "settings_timezone")
async def settings_timezone(call: CallbackQuery, state: FSMContext):
    tz = get_user_timezone(call.from_user.id)
    await call.message.edit_text(
        f"🕒 <b>Часовой пояс</b>\n\n"
        f"Текущий: <b>{escape(tz)}</b>\n\n"
        f"Выберите из списка или введите вручную.",
        parse_mode="HTML",
        reply_markup=timezone_presets_kb()
    )
    await call.answer()


@router.callback_query(F.data == "settings_back")
async def settings_back(call: CallbackQuery, state: FSMContext):
    tz = get_user_timezone(call.from_user.id)
    await call.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n🕒 Часовой пояс: <b>{escape(tz)}</b>",
        parse_mode="HTML",
        reply_markup=settings_kb()
    )
    await call.answer()


@router.callback_query(F.data == "settings_close")
async def settings_close(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("tz_set:"))
async def tz_set_preset(call: CallbackQuery, state: FSMContext):
    tz_name = call.data.split(":", 1)[1]
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        await call.answer("❌ Неизвестный пояс", show_alert=True)
        return
    set_user_timezone(call.from_user.id, tz_name)
    await state.clear()
    await call.message.edit_text(
        f"✅ Часовой пояс установлен: <b>{escape(tz_name)}</b>",
        parse_mode="HTML",
        reply_markup=settings_kb()
    )
    await call.answer()


@router.callback_query(F.data == "tz_manual")
async def tz_manual(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "✍️ Введите часовой пояс в формате IANA, например:\n"
        "<code>Europe/Moscow</code>\n"
        "<code>Europe/Berlin</code>\n"
        "<code>Asia/Almaty</code>\n"
        "<code>America/New_York</code>",
        parse_mode="HTML"
    )
    await state.set_state(SettingsForm.waiting_timezone)
    await call.answer()


@router.message(SettingsForm.waiting_timezone)
async def tz_manual_set(message: Message, state: FSMContext):
    tz_name = (message.text or "").strip()
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
    await message.answer(
        f"✅ Часовой пояс установлен: <b>{escape(tz_name)}</b>",
        parse_mode="HTML",
        reply_markup=settings_kb()
    )


# ==================== УНИВЕРСАЛЬНАЯ ОТМЕНА ====================

@router.callback_query(F.data == "cancel")
async def cancel_action(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_text("❌ Действие отменено.")
    except Exception:
        pass
    await call.answer()