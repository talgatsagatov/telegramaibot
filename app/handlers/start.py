"""Обработчики /start, /cancel и кнопки «В главное меню»."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import CB_BACK_TO_MENU, main_menu_kb
from app.keyboards.reply import remove_kb
from app.utils import texts

logger = logging.getLogger(__name__)

router: Router = Router(name="start")


@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(text=texts.GREETING, reply_markup=main_menu_kb())
    # Убираем reply-клавиатуру, если она осталась от формы заявки
    await message.answer("Меню готово.", reply_markup=remove_kb())


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(texts.BACK_TO_MENU, reply_markup=main_menu_kb())
        return

    logger.info("User %s cancelled state %s", message.from_user.id, current_state)
    await state.clear()
    await message.answer(text=texts.LEAD_CANCELLED, reply_markup=remove_kb())
    await message.answer(text=texts.GREETING, reply_markup=main_menu_kb())


@router.callback_query(F.data == CB_BACK_TO_MENU, StateFilter("*"))
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(text=texts.GREETING, reply_markup=main_menu_kb())
