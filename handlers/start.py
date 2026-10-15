from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import get_user_timezone
from keyboards import main_menu
from html import escape

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Проверку подписки делает subscription.py middleware — сюда попадаем только если всё ок
    tz = get_user_timezone(message.from_user.id)
    is_admin = message.from_user.id == ADMIN_ID

    text = (
        f"👋 Привет, {escape(message.from_user.first_name or 'друг')}!\n\n"
        f"🕒 Ваш часовой пояс: <b>{escape(tz)}</b>\n\n"
        f"Здесь вы можете планировать посты в свои Telegram-каналы, "
        f"отправлять рекламу и управлять каналами.\n\n"
        f"💡 Сменить часовой пояс: /timezone"
    )
    await message.answer(text, reply_markup=main_menu(is_admin), parse_mode="HTML")


@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = call.from_user.id == ADMIN_ID
    await call.message.edit_text("🏠 <b>Главное меню</b>", reply_markup=main_menu(is_admin), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "Этот бот помогает автоматически публиковать посты в ваши Telegram-каналы "
        "по расписанию.\n\n"
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
        "3. Нажмите «📝 Создать пост» и заполните шаги.\n\n"
        "<b>Часовой пояс:</b> /timezone\n"
    )
    await call.message.edit_text(text, parse_mode="HTML",
                                 reply_markup=main_menu(call.from_user.id == ADMIN_ID))
    await call.answer()