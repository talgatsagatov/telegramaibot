"""Обёртка над OpenRouter API для диалога с языковой моделью.

OpenRouter совместим с форматом OpenAI, поэтому используем тот же SDK,
но с изменённым base_url.
"""

from __future__ import annotations

import logging
from typing import Literal, TypedDict

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.config import settings
from app.utils.texts import AI_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
MAX_TG_MESSAGE_LEN: int = 4000  # Telegram режет на 4096, берём с запасом
REQUEST_TIMEOUT_SECONDS: float = 30.0

Role = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str


class OpenAIServiceError(Exception):
    """Любая ошибка при запросе к ИИ — timeout, rate limit, пустой ответ и т.д."""


class OpenAIClient:
    """Клиент для общения с языковой моделью через OpenRouter."""

    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        app_title: str = "Telegram Marketing Bot",
    ) -> None:
        self._client: AsyncOpenAI = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
            default_headers={"X-Title": app_title},
        )
        self.model: str = model
        self.system_prompt: str = system_prompt

    async def ask(self, history: list[ChatMessage]) -> str:
        """Отправляет историю диалога в модель и возвращает ответ.

        Системный промпт добавляется автоматически в начало каждого запроса.
        Ответ обрезается до лимита Telegram.
        """
        messages: list[ChatMessage] = [
            {"role": "system", "content": self.system_prompt},
            *history,
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
            )
        except APITimeoutError as exc:
            logger.warning("OpenRouter request timed out: %s", exc)
            raise OpenAIServiceError("Превышено время ожидания") from exc
        except RateLimitError as exc:
            logger.warning("OpenRouter rate limit hit: %s", exc)
            raise OpenAIServiceError("Слишком много запросов") from exc
        except APIError as exc:
            logger.error("OpenRouter API error: %s", exc)
            raise OpenAIServiceError("Ошибка API") from exc
        except Exception as exc:
            logger.exception("Unexpected error calling OpenRouter")
            raise OpenAIServiceError("Неожиданная ошибка") from exc

        if not response.choices:
            logger.error("OpenRouter returned no choices: %r", response)
            raise OpenAIServiceError("Пустой ответ от модели")

        content = response.choices[0].message.content or ""
        if not content.strip():
            logger.error("OpenRouter returned empty content")
            raise OpenAIServiceError("Пустой ответ от модели")

        return content[:MAX_TG_MESSAGE_LEN]


ai_client: OpenAIClient = OpenAIClient(
    api_key=settings.openrouter_api_key.get_secret_value(),
    model=settings.openrouter_model,
    system_prompt=AI_SYSTEM_PROMPT,
    app_title=settings.agency_name,
)
