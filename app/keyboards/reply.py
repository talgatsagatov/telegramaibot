"""Reply-клавиатуры бота.

В проекте нужна только одна reply-клавиатура — для запроса контакта
на шаге FSM «Телефон» (Telegram умеет одной кнопкой переслать
номер пользователя через `request_contact=True`).
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.utils import texts


def phone_request_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой «Отправить мой номер» (request_contact).

    Returns:
        Reply-клавиатура с одной кнопкой запроса контакта.
        Авто-скрывается после первого использования (`one_time_keyboard=True`).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.BTN_SEND_CONTACT, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажмите кнопку или введите номер вручную",
    )


def remove_kb() -> ReplyKeyboardRemove:
    """Удаляет reply-клавиатуру у пользователя.

    Returns:
        Объект `ReplyKeyboardRemove`, передаётся в `reply_markup` сообщения.
    """
    return ReplyKeyboardRemove()
