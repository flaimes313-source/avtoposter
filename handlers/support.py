from html import escape

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import add_support_message
from keyboards import support_kb

router = Router()


class SupportForm(StatesGroup):
    waiting_question = State()


@router.message(F.text == "🆘 Поддержка")
async def support_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🆘 <b>Поддержка</b>\n\n"
        "Если у вас есть вопрос или проблема — напишите, "
        "админ ответит вам в этом чате.\n\n"
        "Нажмите «✍️ Задать вопрос», чтобы продолжить.",
        parse_mode="HTML",
        reply_markup=support_kb()
    )


@router.callback_query(F.data == "support_write")
async def support_write(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "✍️ Напишите ваш вопрос одним сообщением. Админ получит его и ответит."
    )
    await state.set_state(SupportForm.waiting_question)
    await call.answer()


@router.message(SupportForm.waiting_question)
async def support_question_received(message: Message, state: FSMContext, bot: Bot):
    username = f"@{message.from_user.username}" if message.from_user.username else "(нет username)"

    add_support_message(
        user_id=message.from_user.id,
        username=username,
        text=message.text or "(пусто)"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🆘 <b>Новый вопрос</b>\n"
                f"От: {escape(username)} (<code>{message.from_user.id}</code>)\n\n"
                f"«{escape(message.text or '')}»\n\n"
                f"Откройте «⚙️ Админ-панель» → «❓ Вопросы», чтобы ответить."
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await state.clear()
    await message.answer("✅ Ваш вопрос отправлен! Админ ответит вам в этом чате.")