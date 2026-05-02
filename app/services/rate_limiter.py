"""Лимит запросов к ИИ: 10 успешных запросов в сутки на пользователя."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UsageLimit

logger = logging.getLogger(__name__)

DAILY_LIMIT: int = 10
WINDOW: timedelta = timedelta(hours=24)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime) -> datetime:
    """SQLite иногда возвращает naive datetime даже при timezone=True.
    Принудительно помечаем такие значения как UTC, чтобы не получить TypeError при сравнении."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _get_record(session: AsyncSession, tg_user_id: int) -> UsageLimit | None:
    result = await session.execute(
        select(UsageLimit).where(UsageLimit.tg_user_id == tg_user_id)
    )
    return result.scalar_one_or_none()


async def is_allowed(session: AsyncSession, tg_user_id: int) -> bool:
    """Проверяет, не исчерпал ли пользователь дневной лимит.

    Только читает БД, не изменяет. Счётчик увеличивается отдельно —
    через register_successful_request, и только при успешном ответе ИИ.
    """
    record = await _get_record(session, tg_user_id)
    if record is None:
        return True

    elapsed = _utc_now() - _ensure_aware(record.window_started_at)
    if elapsed >= WINDOW:
        return True

    return record.requests_count < DAILY_LIMIT


async def register_successful_request(
    session: AsyncSession, tg_user_id: int
) -> None:
    """Записывает успешный запрос в счётчик. Сбрасывает окно, если 24 часа истекли."""
    now = _utc_now()
    record = await _get_record(session, tg_user_id)

    if record is None:
        record = UsageLimit(
            tg_user_id=tg_user_id,
            requests_count=1,
            window_started_at=now,
        )
        session.add(record)
        logger.info("Rate limit window started for user %s", tg_user_id)
    else:
        elapsed = now - _ensure_aware(record.window_started_at)
        if elapsed >= WINDOW:
            record.requests_count = 1
            record.window_started_at = now
            logger.info("Rate limit window reset for user %s", tg_user_id)
        else:
            record.requests_count += 1

    await session.commit()


async def get_remaining(session: AsyncSession, tg_user_id: int) -> int:
    """Возвращает сколько запросов у пользователя осталось до лимита."""
    record = await _get_record(session, tg_user_id)
    if record is None:
        return DAILY_LIMIT

    elapsed = _utc_now() - _ensure_aware(record.window_started_at)
    if elapsed >= WINDOW:
        return DAILY_LIMIT

    return max(0, DAILY_LIMIT - record.requests_count)
