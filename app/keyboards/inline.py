"""Inline-клавиатуры и константы callback_data."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import texts

CB_ASK_AI: str = "ask_ai"
CB_NEW_LEAD: str = "new_lead"
CB_BACK_TO_MENU: str = "back_to_menu"
CB_LEAD_CANCEL: str = "lead_cancel"
CB_LEAD_CONFIRM: str = "lead_confirm"
CB_LEAD_BACK_PREFIX: str = "lead_back:"
CB_LEAD_STATUS_PREFIX: str = "lead_status:"


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=texts.BTN_ASK_AI, callback_data=CB_ASK_AI)
    builder.button(text=texts.BTN_NEW_LEAD, callback_data=CB_NEW_LEAD)
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=texts.BTN_BACK_TO_MENU, callback_data=CB_BACK_TO_MENU)
    return builder.as_markup()


def lead_navigation_kb(*, back_to: str | None = None) -> InlineKeyboardMarkup:
    """Навигация по шагам формы. back_to=None — кнопка «Назад» не показывается."""
    builder = InlineKeyboardBuilder()
    if back_to is not None:
        builder.button(
            text=texts.BTN_BACK,
            callback_data=f"{CB_LEAD_BACK_PREFIX}{back_to}",
        )
    builder.button(text=texts.BTN_CANCEL, callback_data=CB_LEAD_CANCEL)
    builder.adjust(2 if back_to else 1)
    return builder.as_markup()


def lead_confirmation_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=texts.BTN_CONFIRM, callback_data=CB_LEAD_CONFIRM)
    builder.button(text=texts.BTN_BACK, callback_data=f"{CB_LEAD_BACK_PREFIX}description")
    builder.button(text=texts.BTN_CANCEL, callback_data=CB_LEAD_CANCEL)
    builder.adjust(1, 2)
    return builder.as_markup()


def admin_lead_kb(lead_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BTN_TAKE_LEAD,
        callback_data=f"{CB_LEAD_STATUS_PREFIX}in_progress:{lead_id}",
    )
    builder.button(
        text=texts.BTN_CLOSE_LEAD,
        callback_data=f"{CB_LEAD_STATUS_PREFIX}closed:{lead_id}",
    )
    builder.adjust(2)
    return builder.as_markup()


def empty_kb() -> InlineKeyboardMarkup:
    """Пустая клавиатура — используется чтобы убрать кнопки через edit_reply_markup."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=" ", callback_data="noop")]]
    )
