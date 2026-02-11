"""FSM-состояния для онбординга: создание персонажа."""

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Шаги создания персонажа: имя → аватар → архетип."""

    waiting_for_name = State()
    waiting_for_avatar = State()
    waiting_for_archetype = State()
