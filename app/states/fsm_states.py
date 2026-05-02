"""FSM-состояния для двух пользовательских сценариев."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AIDialog(StatesGroup):
    waiting_for_question: State = State()


class LeadForm(StatesGroup):
    waiting_name: State = State()
    waiting_phone: State = State()
    waiting_description: State = State()
    confirmation: State = State()
