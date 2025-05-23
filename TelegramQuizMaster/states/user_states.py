from aiogram.fsm.state import State, StatesGroup

class SkillStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_custom_skill = State()
    waiting_for_session_time = State()

class ProgressStates(StatesGroup):
    adding_progress = State()
    setting_goal = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
