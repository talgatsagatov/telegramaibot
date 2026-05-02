"""Валидация пользовательского ввода для формы заявки."""

from __future__ import annotations

import re

# Только буквы (рус/англ), пробелы и дефисы, длина 2–50
_NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\s\-]{1,49}$")

# Принимаем форматы: +7 999 123 45 67 / 8(999)123-45-67 / 79991234567
_PHONE_PATTERN = re.compile(
    r"^\+?[78]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$"
)

_DIGITS_ONLY = re.compile(r"\D+")

NAME_MIN_LEN = 2
NAME_MAX_LEN = 50
DESCRIPTION_MIN_LEN = 10
DESCRIPTION_MAX_LEN = 1000


def validate_name(value: str) -> bool:
    if not isinstance(value, str):
        return False
    value = value.strip()
    if not (NAME_MIN_LEN <= len(value) <= NAME_MAX_LEN):
        return False
    return bool(_NAME_PATTERN.fullmatch(value))


def validate_phone(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_PHONE_PATTERN.fullmatch(value.strip()))


def normalize_phone(value: str) -> str:
    """Приводит любой валидный номер к формату +7XXXXXXXXXX."""
    digits = _DIGITS_ONLY.sub("", value)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    return f"+{digits}"


def validate_description(value: str) -> bool:
    if not isinstance(value, str):
        return False
    length = len(value.strip())
    return DESCRIPTION_MIN_LEN <= length <= DESCRIPTION_MAX_LEN
