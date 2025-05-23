from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import SKILL_CATEGORIES

def get_main_menu() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Мои навыки", callback_data="my_skills"),
            InlineKeyboardButton(text="➕ Добавить навык", callback_data="add_skill")
        ],
        [
            InlineKeyboardButton(text="📊 Прогресс", callback_data="progress"),
            InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements")
        ],
        [
            InlineKeyboardButton(text="💡 Совет", callback_data="get_tip"),
            InlineKeyboardButton(text="💪 Мотивация", callback_data="get_motivation")
        ],
        [
            InlineKeyboardButton(text="📈 Статистика", callback_data="statistics"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])
    return keyboard

def get_skill_categories() -> InlineKeyboardMarkup:
    """Skill categories keyboard"""
    keyboard = []
    
    for category in SKILL_CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(text=category, callback_data=f"category_{category}")])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skills_in_category(category: str) -> InlineKeyboardMarkup:
    """Skills in category keyboard"""
    skills = SKILL_CATEGORIES.get(category, [])
    keyboard = []
    
    # Add skills in rows of 2
    for i in range(0, len(skills), 2):
        row = []
        for j in range(i, min(i + 2, len(skills))):
            skill = skills[j]
            row.append(InlineKeyboardButton(text=skill, callback_data=f"skill_{skill}"))
        keyboard.append(row)
    
    # Add custom skill option
    keyboard.append([InlineKeyboardButton(text="✏️ Свой вариант", callback_data="custom_skill")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="add_skill")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_user_skills(skills: dict) -> InlineKeyboardMarkup:
    """User skills keyboard"""
    keyboard = []
    
    for skill_key, skill_data in skills.items():
        skill_name = skill_data["name"]
        streak_emoji = "🔥" if skill_data["streak"] > 0 else "💤"
        button_text = f"{streak_emoji} {skill_name}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"view_skill_{skill_key}")])
    
    if not skills:
        keyboard.append([InlineKeyboardButton(text="➕ Добавить первый навык", callback_data="add_skill")])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skill_actions(skill_key: str) -> InlineKeyboardMarkup:
    """Skill actions keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱️ Добавить сессию", callback_data=f"add_session_{skill_key}"),
            InlineKeyboardButton(text="💡 Совет", callback_data=f"skill_tip_{skill_key}")
        ],
        [
            InlineKeyboardButton(text="📚 Материалы", callback_data=f"materials_{skill_key}"),
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"skill_stats_{skill_key}")
        ],
        [
            InlineKeyboardButton(text="🎯 Цель", callback_data=f"set_goal_{skill_key}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_skill_{skill_key}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="my_skills")
        ]
    ])
    return keyboard

def get_session_time() -> InlineKeyboardMarkup:
    """Session time keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="15 мин", callback_data="time_15"),
            InlineKeyboardButton(text="30 мин", callback_data="time_30"),
            InlineKeyboardButton(text="45 мин", callback_data="time_45")
        ],
        [
            InlineKeyboardButton(text="1 час", callback_data="time_60"),
            InlineKeyboardButton(text="1.5 часа", callback_data="time_90"),
            InlineKeyboardButton(text="2 часа", callback_data="time_120")
        ],
        [
            InlineKeyboardButton(text="✏️ Свое время", callback_data="custom_time"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_skill")
        ]
    ])
    return keyboard

def get_back_to_main() -> InlineKeyboardMarkup:
    """Back to main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

def get_confirmation(action: str, data: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
        ]
    ])
