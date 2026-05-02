"""Уведомления о новых заявках и обработка кнопок смены статуса."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.config import settings
from app.database.crud import update_lead_status
from app.database.engine import get_session
from app.database.models import Lead, LeadStatus
from app.keyboards.inline import CB_LEAD_STATUS_PREFIX, admin_lead_kb
from app.utils import texts

logger = logging.getLogger(__name__)

router: Router = Router(name="admin")

ADMIN_DATETIME_FORMAT: str = "%d.%m.%Y %H:%M UTC"


async def send_new_lead_notification(bot: Bot, lead: Lead) -> None:
    """Отправляет карточку заявки в чат администратора."""
    text = texts.ADMIN_NEW_LEAD_TEMPLATE.format(
        lead_id=lead.id,
        name=lead.name,
        phone=lead.phone,
        description=lead.description,
        created_at=lead.created_at.strftime(ADMIN_DATETIME_FORMAT),
    )
    try:
        await bot.send_message(
            chat_id=settings.admin_chat_id,
            text=text,
            reply_markup=admin_lead_kb(lead.id),
        )
    except TelegramBadRequest as exc:
        logger.error("Failed to notify admin about lead #%s: %s", lead.id, exc)


@router.callback_query(F.data.startswith(CB_LEAD_STATUS_PREFIX))
async def process_lead_status(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        return

    # Проверяем, что кнопку нажал именно администратор
    if callback.from_user.id != settings.admin_chat_id:
        await callback.answer(text=texts.ADMIN_ONLY_ALERT, show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        logger.warning("Malformed status callback: %r", callback.data)
        await callback.answer()
        return

    _, raw_status, raw_id = parts
    try:
        new_status = LeadStatus(raw_status)
        lead_id = int(raw_id)
    except (ValueError, KeyError) as exc:
        logger.warning("Invalid status callback %r: %s", callback.data, exc)
        await callback.answer()
        return

    async with get_session() as session:
        lead = await update_lead_status(session, lead_id, new_status)

    if lead is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    status_label = (
        texts.ADMIN_STATUS_IN_PROGRESS
        if new_status == LeadStatus.IN_PROGRESS
        else texts.ADMIN_STATUS_CLOSED
    )

    if callback.message is not None and callback.message.html_text:
        new_text = f"{callback.message.html_text}\n\n<b>{status_label}</b>"
        try:
            await callback.message.edit_text(text=new_text, reply_markup=None)
        except TelegramBadRequest as exc:
            logger.warning("Cannot edit admin message for lead #%s: %s", lead_id, exc)

    await callback.answer(text=status_label)
    logger.info(
        "Admin changed lead #%s status to %s", lead_id, new_status.value
    )
