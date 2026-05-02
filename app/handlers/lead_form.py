"""FSM-форма «Оставить заявку»: имя → телефон → описание → подтверждение."""

from __future__ import annotations

import logging
from typing import Final

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.crud import create_lead
from app.database.engine import get_session
from app.handlers.admin import send_new_lead_notification
from app.keyboards.inline import (
    CB_LEAD_BACK_PREFIX,
    CB_LEAD_CANCEL,
    CB_LEAD_CONFIRM,
    CB_NEW_LEAD,
    lead_confirmation_kb,
    lead_navigation_kb,
    main_menu_kb,
)
from app.keyboards.reply import phone_request_kb, remove_kb
from app.states.fsm_states import LeadForm
from app.utils import texts
from app.utils.validators import (
    normalize_phone,
    validate_description,
    validate_name,
    validate_phone,
)

logger = logging.getLogger(__name__)

router: Router = Router(name="lead_form")

KEY_NAME: Final[str] = "lead_name"
KEY_PHONE: Final[str] = "lead_phone"
KEY_DESCRIPTION: Final[str] = "lead_description"


@router.callback_query(F.data == CB_NEW_LEAD)
async def start_lead_form(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LeadForm.waiting_name)
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            text=texts.LEAD_ASK_NAME,
            reply_markup=lead_navigation_kb(back_to=None),
        )


@router.message(LeadForm.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return

    name = message.text.strip()
    if not validate_name(name):
        await message.answer(
            text=texts.LEAD_INVALID_NAME,
            reply_markup=lead_navigation_kb(back_to=None),
        )
        return

    await state.update_data({KEY_NAME: name})
    await state.set_state(LeadForm.waiting_phone)
    await message.answer(text=texts.LEAD_ASK_PHONE, reply_markup=phone_request_kb())
    await message.answer(
        text="Или используйте кнопки ниже:",
        reply_markup=lead_navigation_kb(back_to="name"),
    )


@router.message(LeadForm.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    if message.contact is None or message.contact.phone_number is None:
        return
    phone = normalize_phone(message.contact.phone_number)
    await _save_phone_and_advance(message, state, phone)


@router.message(LeadForm.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return

    raw = message.text.strip()
    if not validate_phone(raw):
        await message.answer(
            text=texts.LEAD_INVALID_PHONE,
            reply_markup=lead_navigation_kb(back_to="name"),
        )
        return

    phone = normalize_phone(raw)
    await _save_phone_and_advance(message, state, phone)


async def _save_phone_and_advance(
    message: Message, state: FSMContext, phone: str
) -> None:
    await state.update_data({KEY_PHONE: phone})
    await state.set_state(LeadForm.waiting_description)
    await message.answer(text=texts.LEAD_ASK_DESCRIPTION, reply_markup=remove_kb())
    await message.answer(
        text="Используйте кнопки ниже для навигации:",
        reply_markup=lead_navigation_kb(back_to="phone"),
    )


@router.message(LeadForm.waiting_description, F.text)
async def process_description(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return

    description = message.text.strip()
    if not validate_description(description):
        await message.answer(
            text=texts.LEAD_INVALID_DESCRIPTION,
            reply_markup=lead_navigation_kb(back_to="phone"),
        )
        return

    await state.update_data({KEY_DESCRIPTION: description})
    await state.set_state(LeadForm.confirmation)

    data = await state.get_data()
    summary = texts.LEAD_CONFIRM_TEMPLATE.format(
        name=data[KEY_NAME],
        phone=data[KEY_PHONE],
        description=data[KEY_DESCRIPTION],
    )
    await message.answer(text=summary, reply_markup=lead_confirmation_kb())


@router.callback_query(F.data == CB_LEAD_CONFIRM, LeadForm.confirmation)
async def process_confirmation(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    if callback.from_user is None:
        return

    data = await state.get_data()
    user_id = callback.from_user.id

    async with get_session() as session:
        lead = await create_lead(
            session,
            tg_user_id=user_id,
            name=data[KEY_NAME],
            phone=data[KEY_PHONE],
            description=data[KEY_DESCRIPTION],
        )

    logger.info("New lead #%s saved (user %s)", lead.id, user_id)

    await send_new_lead_notification(bot, lead)
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            text=texts.LEAD_SUCCESS.format(lead_id=lead.id),
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data.startswith(CB_LEAD_BACK_PREFIX))
async def process_back(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    target = callback.data.removeprefix(CB_LEAD_BACK_PREFIX)
    await callback.answer()

    if target == "name":
        await state.set_state(LeadForm.waiting_name)
        await callback.message.answer(
            text=texts.LEAD_ASK_NAME,
            reply_markup=lead_navigation_kb(back_to=None),
        )
    elif target == "phone":
        await state.set_state(LeadForm.waiting_phone)
        await callback.message.answer(
            text=texts.LEAD_ASK_PHONE,
            reply_markup=phone_request_kb(),
        )
        await callback.message.answer(
            text="Или используйте кнопки ниже:",
            reply_markup=lead_navigation_kb(back_to="name"),
        )
    elif target == "description":
        await state.set_state(LeadForm.waiting_description)
        await callback.message.answer(
            text=texts.LEAD_ASK_DESCRIPTION,
            reply_markup=lead_navigation_kb(back_to="phone"),
        )


@router.callback_query(F.data == CB_LEAD_CANCEL)
async def process_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(text=texts.LEAD_CANCELLED, reply_markup=remove_kb())
        await callback.message.answer(text=texts.GREETING, reply_markup=main_menu_kb())
