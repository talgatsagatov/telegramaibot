"""Точка входа: инициализация бота, регистрация роутеров, запуск polling."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.engine import engine, init_db
from app.handlers import (
    admin_router,
    ai_dialog_router,
    lead_form_router,
    start_router,
)
from app.services.openai_client import ai_client

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _build_bot() -> Bot:
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def _build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # start идёт первым — /start и /cancel должны работать в любом состоянии FSM
    dp.include_routers(
        start_router,
        ai_dialog_router,
        lead_form_router,
        admin_router,
    )
    return dp


async def _on_startup(bot: Bot) -> None:
    await init_db()
    me = await bot.get_me()
    logger.info("Bot started: @%s (id=%s)", me.username, me.id)


async def _on_shutdown(bot: Bot) -> None:
    logger.info("Shutting down...")
    await bot.session.close()
    await ai_client._client.close()  # noqa: SLF001
    await engine.dispose()
    logger.info("Shutdown complete.")


async def main() -> None:
    _configure_logging()
    bot = _build_bot()
    dp = _build_dispatcher()

    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
