"""Роутеры aiogram, разделённые по бизнес-сценариям."""

from app.handlers.admin import router as admin_router
from app.handlers.ai_dialog import router as ai_dialog_router
from app.handlers.lead_form import router as lead_form_router
from app.handlers.start import router as start_router

__all__ = [
    "admin_router",
    "ai_dialog_router",
    "lead_form_router",
    "start_router",
]
