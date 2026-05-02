"""Ветка «Задать вопрос ИИ»: диалог с моделью с контекстом сессии."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.engine import get_session
from app.keyboards.inline import CB_ASK_AI, back_to_menu_kb
from app.services import rate_limiter
from app.services.openai_client import ChatMessage, OpenAIServiceError, ai_client
from app.states.fsm_states import AIDialog
from app.utils import texts

logger = logging.getLogger(__name__)

router: Router = Router(name="ai_dialog")

# Храним в FSM последние 5 пар вопрос/ответ — этого хватает для контекста
MAX_HISTORY_MESSAGES: int = 10
HISTORY_KEY: str = "ai_history"


@router.callback_query(F.data == CB_ASK_AI)
async def start_ai_dialog(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AIDialog.waiting_for_question)
    await state.update_data({HISTORY_KEY: []})
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            text=texts.AI_PROMPT_QUESTION,
            reply_markup=back_to_menu_kb(),
        )


@router.message(AIDialog.waiting_for_question, F.text)
async def handle_ai_question(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        return

    user_id = message.from_user.id
    question = message.text.strip()
    if not question:
        return

    async with get_session() as session:
        if not await rate_limiter.is_allowed(session, user_id):
            await message.answer(
                text=texts.AI_LIMIT_REACHED,
                reply_markup=back_to_menu_kb(),
            )
            logger.info("User %s hit daily AI limit", user_id)
            return

    data = await state.get_data()
    history: list[ChatMessage] = list(data.get(HISTORY_KEY, []))
    request_payload: list[ChatMessage] = [
        *history,
        {"role": "user", "content": question},
    ]

    thinking_msg = await message.answer(text=texts.AI_THINKING)

    try:
        answer = await ai_client.ask(request_payload)
    except OpenAIServiceError as exc:
        logger.warning("OpenRouter failed for user %s: %s", user_id, exc)
        await thinking_msg.edit_text(texts.AI_ERROR)
        await message.answer(
            text="Можете задать другой вопрос или вернуться в меню.",
            reply_markup=back_to_menu_kb(),
        )
        return

    # Добавляем ответ в историю и обрезаем до 5 последних пар
    new_history: list[ChatMessage] = [
        *request_payload,
        {"role": "assistant", "content": answer},
    ]
    new_history = new_history[-MAX_HISTORY_MESSAGES:]
    await state.update_data({HISTORY_KEY: new_history})

    async with get_session() as session:
        await rate_limiter.register_successful_request(session, user_id)

    await thinking_msg.delete()
    await message.answer(text=answer, reply_markup=back_to_menu_kb())
