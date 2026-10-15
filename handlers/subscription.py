from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    is_subscription_required, get_required_channels,
    set_subscription, get_user_timezone
)
from keyboards import subscription_check_kb, main_reply_kb

router = Router()


async def user_is_subscribed(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Возвращает (всё_ок, список_непройденных_каналов)."""
    channels = get_required_channels()
    if not channels:
        return True, []

    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            ok = member.status in ("member", "administrator", "creator")
            set_subscription(user_id, ch["chat_id"], ok)
            if not ok:
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return (len(missing) == 0), missing


async def send_subscription_gate(message_or_call, bot, missing, is_edit=False):
    """Показывает экран подписки."""
    text = (
        "🔒 <b>Требуется подписка</b>\n\n"
        "Чтобы пользоваться ботом, подпишитесь на каналы ниже, "
        "затем нажмите «✅ Я подписался»."
    )
    kb = subscription_check_kb(missing)
    if is_edit:
        await message_or_call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message_or_call.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "check_subscription")
async def check_subscription(call: CallbackQuery, state: FSMContext, bot: Bot):
    ok, missing = await user_is_subscribed(bot, call.from_user.id)
    if ok:
        await call.message.edit_text(
            "✅ Спасибо за подписку! Теперь можно пользоваться ботом."
        )
        # Отправляем reply-меню отдельным сообщением, потому что edit_text
        # не может поменять reply-клавиатуру
        await call.message.answer(
            "🏠 Главное меню",
            reply_markup=main_reply_kb(call.from_user.id == ADMIN_ID)
        )
    else:
        await send_subscription_gate(call, bot, missing, is_edit=True)
    await call.answer()