"""Конфигурация приложения.

Загружает переменные окружения из файла `.env` и валидирует их через
`pydantic-settings`. При отсутствии обязательных переменных приложение
падает на старте с понятной ошибкой.

Использование:
    from app.config import settings
    print(settings.bot_token)
"""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения / `.env`.

    Attributes:
        bot_token: Токен Telegram-бота от @BotFather.
        openai_api_key: API-ключ OpenAI.
        admin_chat_id: Telegram chat_id администратора для уведомлений.
        openai_model: Идентификатор модели OpenAI (по умолчанию gpt-4o-mini).
        agency_name: Название агентства, подставляемое в тексты и промпт ИИ.
        database_url: Async DSN для подключения к БД (SQLite через aiosqlite).
        log_level: Уровень логирования стандартного `logging`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: SecretStr = Field(..., description="Токен Telegram-бота")
    openrouter_api_key: SecretStr = Field(..., description="OpenRouter API key")
    admin_chat_id: int = Field(..., description="Telegram chat_id админа")

    openrouter_model: str = Field(default="openai/gpt-4o-mini")
    agency_name: str = Field(default="Marketing Pro")
    database_url: str = Field(default="sqlite+aiosqlite:///bot.db")
    log_level: str = Field(default="INFO")


def _load_settings() -> Settings:
    """Загружает настройки и оборачивает ошибки валидации в понятное сообщение.

    Returns:
        Готовый объект `Settings`.

    Raises:
        SystemExit: Если переменные окружения не валидны или отсутствуют.
    """
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:
        raise SystemExit(
            f"[CONFIG ERROR] Не удалось загрузить настройки из .env: {exc}\n"
            "Проверьте, что файл .env существует и содержит BOT_TOKEN, "
            "OPENROUTER_API_KEY и ADMIN_CHAT_ID."
        ) from exc


settings: Settings = _load_settings()
