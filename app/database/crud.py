"""CRUD-операции для таблицы заявок."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Lead, LeadStatus


async def create_lead(
    session: AsyncSession,
    *,
    tg_user_id: int,
    name: str,
    phone: str,
    description: str,
) -> Lead:
    """Создаёт новую заявку и возвращает её с присвоенным id."""
    lead = Lead(
        tg_user_id=tg_user_id,
        name=name,
        phone=phone,
        description=description,
        status=LeadStatus.NEW,
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead


async def get_lead_by_id(session: AsyncSession, lead_id: int) -> Lead | None:
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def update_lead_status(
    session: AsyncSession,
    lead_id: int,
    new_status: LeadStatus,
) -> Lead | None:
    """Меняет статус заявки. Возвращает None, если заявка не найдена."""
    lead = await get_lead_by_id(session, lead_id)
    if lead is None:
        return None
    lead.status = new_status
    await session.commit()
    await session.refresh(lead)
    return lead
