from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import random
from datetime import datetime, timedelta

from keyboards.inline import (
    get_session_time, get_user_skills, get_main_menu, 
    get_back_to_main, get_skill_actions
)
from states.user_states import ProgressStates
from utils.data_manager import DataManager
from utils.achievements import AchievementManager
from config import MOTIVATIONAL_MESSAGES, LEARNING_TIPS, USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE

router = Router()

# Initialize managers
data_manager = DataManager(USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE)
achievement_manager = AchievementManager(data_manager)

@router.callback_query(F.data.startswith("add_session_"))
async def add_session_start(callback: CallbackQuery, state: FSMContext):
    """Start adding practice session"""
    skill_key = callback.data.replace("add_session_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill = skills[skill_key]
    await state.update_data(session_skill=skill_key)
    
    text = (
        f"⏱️ **Добавить сессию**\n\n"
        f"🎯 Навык: {skill['name']}\n\n"
        f"Сколько времени вы потратили на практику?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_session_time(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("time_"))
async def select_session_time(callback: CallbackQuery, state: FSMContext):
    """Select session time"""
    minutes = int(callback.data.replace("time_", ""))
    
    data = await state.get_data()
    skill_key = data.get("session_skill")
    
    if not skill_key:
        await callback.answer("❌ Ошибка: навык не выбран")
        return
    
    await add_session_with_time(callback, state, skill_key, minutes)

@router.callback_query(F.data == "custom_time")
async def custom_session_time(callback: CallbackQuery, state: FSMContext):
    """Request custom session time"""
    await state.set_state(ProgressStates.adding_progress)
    
    text = (
        "✏️ **Свое время**\n\n"
        "Напишите количество минут практики (число от 1 до 600):"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.message(ProgressStates.adding_progress)
async def process_custom_time(message: Message, state: FSMContext):
    """Process custom session time"""
    try:
        minutes = int(message.text.strip())
        
        if minutes < 1 or minutes > 600:
            await message.answer("⚠️ Время должно быть от 1 до 600 минут. Попробуйте еще раз:")
            return
        
        data = await state.get_data()
        skill_key = data.get("session_skill")
        
        if not skill_key:
            await message.answer("❌ Ошибка: навык не выбран", reply_markup=get_main_menu())
            await state.clear()
            return
        
        await add_session_with_time(message, state, skill_key, minutes, is_message=True)
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число от 1 до 600:")

async def add_session_with_time(event, state: FSMContext, skill_key: str, minutes: int, is_message: bool = False):
    """Add session with specified time"""
    user_id = str(event.from_user.id)
    
    # Add session
    streak = data_manager.add_session(user_id, skill_key, minutes)
    
    # Get updated skill info
    skills = data_manager.get_user_skills(user_id)
    skill = skills[skill_key]
    
    # Check for achievements
    new_achievements = achievement_manager.check_achievements(user_id)
    
    # Format response
    hours = minutes // 60
    mins = minutes % 60
    time_text = f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
    
    total_hours = skill["total_time_minutes"] // 60
    total_mins = skill["total_time_minutes"] % 60
    total_time_text = f"{total_hours}ч {total_mins}м" if total_hours > 0 else f"{total_mins}м"
    
    text = (
        f"✅ **Сессия добавлена!**\n\n"
        f"🎯 Навык: {skill['name']}\n"
        f"⏰ Время сессии: {time_text}\n"
        f"🔥 Серия: {streak} дней\n"
        f"📊 Всего времени: {total_time_text}\n"
    )
    
    # Add motivational message
    if streak > 1:
        text += f"\n💪 Отличная серия! Продолжайте в том же духе!"
    elif streak == 1:
        text += f"\n🚀 Хорошее начало! Попробуйте заниматься каждый день!"
    
    # Add progress towards goal if set
    if skill["goal_minutes"] > 0:
        progress = min(100, (skill["total_time_minutes"] / skill["goal_minutes"]) * 100)
        text += f"\n🎯 Прогресс к цели: {progress:.1f}%"
    
    keyboard = get_skill_actions(skill_key)
    
    if is_message:
        await event.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Show achievements if any
    if new_achievements:
        achievement_text = "🎉 **Новые достижения!**\n\n"
        for ach in new_achievements:
            achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
        
        if is_message:
            await event.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")
        else:
            await event.message.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    
    await state.clear()

@router.callback_query(F.data == "progress")
async def show_progress(callback: CallbackQuery):
    """Show overall progress"""
    user_id = str(callback.from_user.id)
    user = data_manager.get_user(user_id)
    skills = user["skills"]
    
    if not skills:
        text = (
            "📊 **Ваш прогресс**\n\n"
            "У вас пока нет навыков для отслеживания.\n"
            "Добавьте первый навык, чтобы начать!"
        )
        await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
        return
    
    # Calculate statistics
    total_sessions = sum(skill["sessions"] for skill in skills.values())
    total_minutes = sum(skill["total_time_minutes"] for skill in skills.values())
    total_hours = total_minutes // 60
    total_mins = total_minutes % 60
    
    active_streaks = [skill for skill in skills.values() if skill["streak"] > 0]
    max_streak = max([skill["streak"] for skill in skills.values()], default=0)
    best_streak = max([skill["best_streak"] for skill in skills.values()], default=0)
    
    text = (
        f"📊 **Ваш прогресс**\n\n"
        f"🎯 Активных навыков: {len(skills)}\n"
        f"🔥 Активных серий: {len(active_streaks)}\n"
        f"📈 Лучшая серия: {best_streak} дней\n"
        f"📊 Всего сессий: {total_sessions}\n"
        f"⏰ Общее время: {total_hours}ч {total_mins}м\n\n"
    )
    
    # Show top skills by time
    sorted_skills = sorted(skills.values(), key=lambda x: x["total_time_minutes"], reverse=True)
    text += "🏆 **Топ навыков по времени:**\n"
    
    for i, skill in enumerate(sorted_skills[:5], 1):
        hours = skill["total_time_minutes"] // 60
        mins = skill["total_time_minutes"] % 60
        time_text = f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
        streak_emoji = "🔥" if skill["streak"] > 0 else "💤"
        text += f"{i}. {streak_emoji} {skill['name']} - {time_text}\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("skill_stats_"))
async def show_skill_stats(callback: CallbackQuery):
    """Show detailed skill statistics"""
    skill_key = callback.data.replace("skill_stats_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill = skills[skill_key]
    
    # Calculate statistics
    total_hours = skill["total_time_minutes"] // 60
    total_mins = skill["total_time_minutes"] % 60
    total_time_text = f"{total_hours}ч {total_mins}м" if total_hours > 0 else f"{total_mins}м"
    
    avg_session = skill["total_time_minutes"] / skill["sessions"] if skill["sessions"] > 0 else 0
    avg_hours = int(avg_session) // 60
    avg_mins = int(avg_session) % 60
    avg_text = f"{avg_hours}ч {avg_mins}м" if avg_hours > 0 else f"{avg_mins}м"
    
    # Days since start
    if skill.get("created_at"):
        start_date = datetime.fromisoformat(skill["created_at"])
        days_total = (datetime.now() - start_date).days + 1
        consistency = (skill["sessions"] / days_total * 100) if days_total > 0 else 0
    else:
        days_total = 0
        consistency = 0
    
    text = (
        f"📊 **Статистика навыка**\n\n"
        f"🎯 **{skill['name']}**\n"
        f"📚 Категория: {skill['category']}\n\n"
        f"⏰ Общее время: {total_time_text}\n"
        f"📊 Количество сессий: {skill['sessions']}\n"
        f"📈 Средняя сессия: {avg_text}\n"
        f"🔥 Текущая серия: {skill['streak']} дней\n"
        f"🏆 Лучшая серия: {skill['best_streak']} дней\n"
        f"📅 Дней изучения: {days_total}\n"
        f"📈 Постоянство: {consistency:.1f}%\n"
    )
    
    if skill["goal_minutes"] > 0:
        goal_hours = skill["goal_minutes"] // 60
        goal_mins = skill["goal_minutes"] % 60
        goal_text = f"{goal_hours}ч {goal_mins}м" if goal_hours > 0 else f"{goal_mins}м"
        progress = min(100, (skill["total_time_minutes"] / skill["goal_minutes"]) * 100)
        text += f"\n🎯 Цель: {goal_text}\n📊 Прогресс: {progress:.1f}%\n"
        
        if progress >= 100:
            text += "🎉 Цель достигнута! Поставьте новую цель!"
    
    # Show recent notes if any
    if skill.get("notes"):
        recent_notes = sorted(skill["notes"], key=lambda x: x["date"], reverse=True)[:3]
        text += "\n📝 **Последние заметки:**\n"
        for note in recent_notes:
            note_date = datetime.fromisoformat(note["date"])
            text += f"• {note_date.strftime('%d.%m')} - {note['note']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_skill_actions(skill_key),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("set_goal_"))
async def set_goal_start(callback: CallbackQuery, state: FSMContext):
    """Start setting goal for skill"""
    skill_key = callback.data.replace("set_goal_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill = skills[skill_key]
    await state.update_data(goal_skill=skill_key)
    await state.set_state(ProgressStates.setting_goal)
    
    current_goal = ""
    if skill["goal_minutes"] > 0:
        goal_hours = skill["goal_minutes"] // 60
        goal_mins = skill["goal_minutes"] % 60
        current_goal = f"\n\n📊 Текущая цель: {goal_hours}ч {goal_mins}м"
    
    text = (
        f"🎯 **Установить цель**\n\n"
        f"Навык: {skill['name']}{current_goal}\n\n"
        f"Напишите цель в часах (например: 10) или в минутах (например: 600м):"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.message(ProgressStates.setting_goal)
async def process_goal(message: Message, state: FSMContext):
    """Process goal setting"""
    goal_text = message.text.strip().lower()
    
    try:
        if goal_text.endswith('м'):
            # Minutes
            minutes = int(goal_text[:-1])
        elif goal_text.endswith('ч'):
            # Hours
            hours = int(goal_text[:-1])
            minutes = hours * 60
        else:
            # Assume hours
            hours = int(goal_text)
            minutes = hours * 60
        
        if minutes < 1 or minutes > 10000:
            await message.answer("⚠️ Цель должна быть от 1 минуты до 10000 минут (167 часов). Попробуйте еще раз:")
            return
        
        data = await state.get_data()
        skill_key = data.get("goal_skill")
        
        if not skill_key:
            await message.answer("❌ Ошибка: навык не выбран", reply_markup=get_main_menu())
            await state.clear()
            return
        
        # Update goal
        user_id = str(message.from_user.id)
        user = data_manager.get_user(user_id)
        
        if skill_key in user["skills"]:
            user["skills"][skill_key]["goal_minutes"] = minutes
            data_manager.update_user(user_id, user)
            
            hours = minutes // 60
            mins = minutes % 60
            goal_text = f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
            
            skill_name = user["skills"][skill_key]["name"]
            current_time = user["skills"][skill_key]["total_time_minutes"]
            progress = min(100, (current_time / minutes) * 100) if minutes > 0 else 0
            
            text = (
                f"✅ **Цель установлена!**\n\n"
                f"🎯 Навык: {skill_name}\n"
                f"🎯 Цель: {goal_text}\n"
                f"📊 Текущий прогресс: {progress:.1f}%\n\n"
                f"Удачи в достижении цели!"
            )
            
            await message.answer(text, reply_markup=get_skill_actions(skill_key), parse_mode="Markdown")
        else:
            await message.answer("❌ Навык не найден", reply_markup=get_main_menu())
        
        await state.clear()
        
    except ValueError:
        await message.answer("⚠️ Неверный формат. Используйте число часов (например: 10) или минут (например: 600м):")

@router.callback_query(F.data == "get_tip")
async def get_general_tip(callback: CallbackQuery):
    """Get general learning tip"""
    user_id = str(callback.from_user.id)
    
    # Update statistics
    data_manager.update_statistics(user_id, "tips_received")
    
    # Get random tip
    tips = LEARNING_TIPS["default"]
    tip = random.choice(tips)
    
    # Check for achievements
    new_achievements = achievement_manager.check_achievements(user_id)
    
    text = f"💡 **Совет для обучения**\n\n{tip}"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    
    # Show achievements if any
    if new_achievements:
        achievement_text = "🎉 **Новые достижения!**\n\n"
        for ach in new_achievements:
            achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
        
        await callback.message.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "get_motivation")
async def get_motivation(callback: CallbackQuery):
    """Get motivational message"""
    user_id = str(callback.from_user.id)
    
    # Update statistics
    data_manager.update_statistics(user_id, "motivations_received")
    
    # Get random motivation
    motivation = random.choice(MOTIVATIONAL_MESSAGES)
    
    text = f"💪 **Мотивация**\n\n{motivation}"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery):
    """Show detailed user statistics"""
    user_id = str(callback.from_user.id)
    user = data_manager.get_user(user_id)
    
    # Calculate detailed statistics
    skills = user["skills"]
    stats = user["statistics"]
    
    total_skills = len(skills)
    active_skills = len([s for s in skills.values() if s["streak"] > 0])
    total_sessions = stats["total_sessions"]
    total_minutes = stats["total_time_minutes"]
    total_hours = total_minutes // 60
    total_mins = total_minutes % 60
    
    # Calculate averages
    avg_session = total_minutes / total_sessions if total_sessions > 0 else 0
    avg_hours = int(avg_session) // 60
    avg_mins = int(avg_session) % 60
    
    # Days since registration
    created_date = datetime.fromisoformat(user["created_at"])
    days_registered = (datetime.now() - created_date).days + 1
    
    # Session frequency
    sessions_per_day = total_sessions / days_registered if days_registered > 0 else 0
    
    text = (
        f"📈 **Подробная статистика**\n\n"
        f"👤 **Общая информация:**\n"
        f"📅 В боте: {days_registered} дней\n"
        f"🎯 Всего навыков: {total_skills}\n"
        f"🔥 Активных серий: {active_skills}\n"
        f"🏆 Очков: {user['total_points']}\n\n"
        f"📊 **Активность:**\n"
        f"📈 Всего сессий: {total_sessions}\n"
        f"⏰ Общее время: {total_hours}ч {total_mins}м\n"
        f"📊 Средняя сессия: {avg_hours}ч {avg_mins}м\n"
        f"📅 Сессий в день: {sessions_per_day:.1f}\n\n"
        f"💡 **Взаимодействие:**\n"
        f"💡 Советов получено: {stats['tips_received']}\n"
        f"💪 Мотиваций получено: {stats['motivations_received']}\n"
    )
    
    # Show skill breakdown if any
    if skills:
        text += "\n🎯 **Навыки по времени:**\n"
        sorted_skills = sorted(skills.values(), key=lambda x: x["total_time_minutes"], reverse=True)
        
        for skill in sorted_skills[:5]:
            hours = skill["total_time_minutes"] // 60
            mins = skill["total_time_minutes"] % 60
            time_text = f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
            streak_emoji = "🔥" if skill["streak"] > 0 else "💤"
            percentage = (skill["total_time_minutes"] / total_minutes * 100) if total_minutes > 0 else 0
            text += f"• {streak_emoji} {skill['name']}: {time_text} ({percentage:.1f}%)\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
