from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.inline import get_back_to_main
from utils.data_manager import DataManager
from utils.achievements import AchievementManager
from config import ACHIEVEMENTS_CONFIG, USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE

router = Router()

# Initialize managers
data_manager = DataManager(USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE)
achievement_manager = AchievementManager(data_manager)

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
    """Show user achievements"""
    user_id = str(callback.from_user.id)
    user = data_manager.get_user(user_id)
    
    user_achievements = user.get("achievements", [])
    total_achievements = len(ACHIEVEMENTS_CONFIG)
    earned_count = len(user_achievements)
    
    text = (
        f"🏆 **Ваши достижения**\n\n"
        f"📊 Прогресс: {earned_count}/{total_achievements}\n"
        f"💎 Очки: {user['total_points']}\n\n"
    )
    
    if not user_achievements:
        text += (
            "У вас пока нет достижений.\n"
            "Начните изучать навыки, чтобы получить первые награды!\n\n"
            "🎯 **Доступные достижения:**\n"
        )
    else:
        text += "✅ **Полученные достижения:**\n"
        
        # Show earned achievements
        for ach_id in user_achievements:
            if ach_id in ACHIEVEMENTS_CONFIG:
                ach = ACHIEVEMENTS_CONFIG[ach_id]
                text += f"🏆 {ach['name']}\n   {ach['description']} (+{ach['points']} очков)\n\n"
        
        # Show remaining achievements
        remaining = [ach_id for ach_id in ACHIEVEMENTS_CONFIG.keys() if ach_id not in user_achievements]
        if remaining:
            text += "🎯 **Доступные достижения:**\n"
    
    # Show remaining achievements or all if none earned
    if not user_achievements or earned_count < total_achievements:
        remaining_achievements = [ach_id for ach_id in ACHIEVEMENTS_CONFIG.keys() if ach_id not in user_achievements]
        
        for ach_id in remaining_achievements:
            ach = ACHIEVEMENTS_CONFIG[ach_id]
            text += f"🔒 {ach['name']}\n   {ach['description']} (+{ach['points']} очков)\n\n"
    
    # Add achievement tips
    text += "💡 **Как получать достижения:**\n"
    text += "• Добавляйте новые навыки\n"
    text += "• Занимайтесь каждый день\n"
    text += "• Получайте советы и мотивацию\n"
    text += "• Отслеживайте свой прогресс\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "achievement_details")
async def show_achievement_details(callback: CallbackQuery):
    """Show detailed achievement information"""
    user_id = str(callback.from_user.id)
    user = data_manager.get_user(user_id)
    
    # Calculate progress towards achievements
    skills = user["skills"]
    stats = user["statistics"]
    
    # Current stats
    skill_count = len(skills)
    max_streak = max([skill["streak"] for skill in skills.values()], default=0)
    tips_count = stats.get("tips_received", 0)
    
    text = (
        f"🎯 **Прогресс к достижениям**\n\n"
        f"📊 **Текущие показатели:**\n"
        f"🎯 Навыков: {skill_count}\n"
        f"🔥 Максимальная серия: {max_streak} дней\n"
        f"💡 Советов получено: {tips_count}\n\n"
        f"🏆 **Прогресс к достижениям:**\n"
    )
    
    # Progress to first skill
    if "first_skill" not in user["achievements"]:
        text += f"🎯 Первый шаг: {'✅' if skill_count >= 1 else '❌'} Добавить навык ({skill_count}/1)\n"
    
    # Progress to multiple skills
    if "multiple_skills" not in user["achievements"]:
        text += f"🌟 Многогранность: {'✅' if skill_count >= 3 else '❌'} Изучать 3+ навыка ({skill_count}/3)\n"
    
    # Progress to streak achievements
    if "streak_3" not in user["achievements"]:
        text += f"🔥 Горячий старт: {'✅' if max_streak >= 3 else '❌'} Серия 3 дня ({max_streak}/3)\n"
    
    if "streak_7" not in user["achievements"]:
        text += f"⚡ Неделя силы: {'✅' if max_streak >= 7 else '❌'} Серия 7 дней ({max_streak}/7)\n"
    
    if "streak_30" not in user["achievements"]:
        text += f"💎 Месяц упорства: {'✅' if max_streak >= 30 else '❌'} Серия 30 дней ({max_streak}/30)\n"
    
    # Progress to tips achievements
    if "first_tip" not in user["achievements"]:
        text += f"💡 Любознательность: {'✅' if tips_count >= 1 else '❌'} Получить совет ({tips_count}/1)\n"
    
    if "tips_fan" not in user["achievements"]:
        text += f"🧠 Ученик: {'✅' if tips_count >= 25 else '❌'} Получить 25 советов ({tips_count}/25)\n"
    
    text += "\n💡 Продолжайте заниматься, чтобы получить новые достижения!"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
