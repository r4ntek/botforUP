from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import random

from keyboards.inline import (
    get_skill_categories, get_skills_in_category, get_user_skills,
    get_skill_actions, get_main_menu, get_back_to_main, get_confirmation
)
from states.user_states import SkillStates
from utils.data_manager import DataManager
from utils.achievements import AchievementManager
from config import SKILL_CATEGORIES, LEARNING_TIPS, STUDY_MATERIALS, USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE

router = Router()

# Initialize managers
data_manager = DataManager(USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE)
achievement_manager = AchievementManager(data_manager)

@router.callback_query(F.data == "my_skills")
async def show_my_skills(callback: CallbackQuery):
    """Show user's skills"""
    user_id = str(callback.from_user.id)
    skills = data_manager.get_user_skills(user_id)
    
    if not skills:
        text = (
            "🎯 <b>Мои навыки</b>\n\n"
            "У вас пока нет добавленных навыков.\n"
            "Добавьте первый навык, чтобы начать отслеживать прогресс!"
        )
    else:
        text = "🎯 <b>Мои навыки</b>\n\n"
        for skill_data in skills.values():
            streak_text = f"🔥 {skill_data['streak']}" if skill_data['streak'] > 0 else "💤"
            time_text = f"{skill_data['total_time_minutes']//60}ч {skill_data['total_time_minutes']%60}м"
            text += f"{streak_text} <b>{skill_data['name']}</b>\n"
            text += f"   📊 {skill_data['sessions']} сессий • ⏰ {time_text}\n\n"
    
    await callback.message.edit_text(
        text, 
        reply_markup=get_user_skills(skills),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "add_skill")
async def add_skill_start(callback: CallbackQuery):
    """Start adding a new skill"""
    text = (
        "➕ **Добавить навык**\n\n"
        "Выберите категорию навыка:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_skill_categories(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("category_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Select skill category"""
    category = callback.data.replace("category_", "")
    
    await state.update_data(selected_category=category)
    
    if category == "✨ Другое":
        await state.set_state(SkillStates.waiting_for_custom_skill)
        text = (
            "✏️ **Свой навык**\n\n"
            "Напишите название навыка, который хотите изучать:"
        )
        await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    else:
        text = f"📚 **{category}**\n\nВыберите навык:"
        await callback.message.edit_text(
            text,
            reply_markup=get_skills_in_category(category),
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("skill_"))
async def select_skill(callback: CallbackQuery, state: FSMContext):
    """Select specific skill"""
    skill_name = callback.data.replace("skill_", "")
    user_id = str(callback.from_user.id)
    
    # Get category from state
    data = await state.get_data()
    category = data.get("selected_category", "Другое")
    
    # Add skill
    success = data_manager.add_skill(user_id, skill_name, category)
    
    if success:
        # Check for new achievements
        new_achievements = achievement_manager.check_achievements(user_id)
        
        text = f"✅ **Навык добавлен!**\n\n🎯 {skill_name}\n📚 Категория: {category}\n\nТеперь вы можете отслеживать прогресс и получать советы!"
        
        await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
        
        # Show achievements if any
        if new_achievements:
            achievement_text = "🎉 **Новые достижения!**\n\n"
            for ach in new_achievements:
                achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
            
            await callback.message.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    else:
        text = f"⚠️ **Навык уже добавлен**\n\nНавык \"{skill_name}\" уже есть в вашем списке."
        await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    
    await state.clear()

@router.callback_query(F.data == "custom_skill")
async def custom_skill_input(callback: CallbackQuery, state: FSMContext):
    """Handle custom skill input"""
    await state.set_state(SkillStates.waiting_for_custom_skill)
    
    text = (
        "✏️ **Свой навык**\n\n"
        "Напишите название навыка, который хотите изучать:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.message(SkillStates.waiting_for_custom_skill)
async def process_custom_skill(message: Message, state: FSMContext):
    """Process custom skill name"""
    skill_name = message.text.strip()
    user_id = str(message.from_user.id)
    
    if len(skill_name) < 2:
        await message.answer("⚠️ Название навыка слишком короткое. Попробуйте еще раз:")
        return
    
    if len(skill_name) > 50:
        await message.answer("⚠️ Название навыка слишком длинное (максимум 50 символов). Попробуйте еще раз:")
        return
    
    # Get category from state
    data = await state.get_data()
    category = data.get("selected_category", "✨ Другое")
    
    # Add skill
    success = data_manager.add_skill(user_id, skill_name, category)
    
    if success:
        # Check for new achievements
        new_achievements = achievement_manager.check_achievements(user_id)
        
        text = f"✅ **Навык добавлен!**\n\n🎯 {skill_name}\n📚 Категория: {category}\n\nТеперь вы можете отслеживать прогресс и получать советы!"
        
        await message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")
        
        # Show achievements if any
        if new_achievements:
            achievement_text = "🎉 **Новые достижения!**\n\n"
            for ach in new_achievements:
                achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
            
            await message.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    else:
        text = f"⚠️ **Навык уже добавлен**\n\nНавык \"{skill_name}\" уже есть в вашем списке."
        await message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    
    await state.clear()

@router.callback_query(F.data.startswith("view_skill_"))
async def view_skill(callback: CallbackQuery, state: FSMContext):
    """View skill details"""
    skill_key = callback.data.replace("view_skill_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.message.edit_text(
            "❌ Навык не найден",
            reply_markup=get_main_menu()
        )
        return
    
    skill = skills[skill_key]
    await state.update_data(current_skill=skill_key)
    
    # Format skill info
    total_hours = skill["total_time_minutes"] // 60
    total_minutes = skill["total_time_minutes"] % 60
    time_text = f"{total_hours}ч {total_minutes}м" if total_hours > 0 else f"{total_minutes}м"
    
    streak_emoji = "🔥" if skill["streak"] > 0 else "💤"
    
    text = (
        f"🎯 **{skill['name']}**\n\n"
        f"📚 Категория: {skill['category']}\n"
        f"{streak_emoji} Текущая серия: {skill['streak']} дней\n"
        f"🏆 Лучшая серия: {skill['best_streak']} дней\n"
        f"📊 Всего сессий: {skill['sessions']}\n"
        f"⏰ Общее время: {time_text}\n"
    )
    
    if skill["goal_minutes"] > 0:
        goal_hours = skill["goal_minutes"] // 60
        goal_minutes = skill["goal_minutes"] % 60
        goal_text = f"{goal_hours}ч {goal_minutes}м" if goal_hours > 0 else f"{goal_minutes}м"
        progress = min(100, (skill["total_time_minutes"] / skill["goal_minutes"]) * 100)
        text += f"🎯 Цель: {goal_text} ({progress:.1f}%)\n"
    
    if skill["last_session"]:
        from datetime import datetime
        last_session = datetime.fromisoformat(skill["last_session"])
        text += f"📅 Последняя сессия: {last_session.strftime('%d.%m.%Y')}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_skill_actions(skill_key),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("skill_tip_"))
async def get_skill_tip(callback: CallbackQuery):
    """Get tip for specific skill"""
    skill_key = callback.data.replace("skill_tip_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill = skills[skill_key]
    skill_name = skill["name"].lower()
    
    # Get tips for skill category
    tips = LEARNING_TIPS.get(skill_name, LEARNING_TIPS["default"])
    tip = random.choice(tips)
    
    # Update statistics
    data_manager.update_statistics(user_id, "tips_received")
    
    # Check for achievements
    new_achievements = achievement_manager.check_achievements(user_id)
    
    text = f"💡 **Совет для навыка \"{skill['name']}\"**\n\n{tip}"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
    
    # Show achievements if any
    if new_achievements:
        achievement_text = "🎉 **Новые достижения!**\n\n"
        for ach in new_achievements:
            achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
        
        await callback.message.answer(achievement_text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("delete_skill_"))
async def confirm_delete_skill(callback: CallbackQuery):
    """Confirm skill deletion"""
    skill_key = callback.data.replace("delete_skill_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill_name = skills[skill_key]["name"]
    
    text = f"🗑️ **Удаление навыка**\n\nВы уверены, что хотите удалить навык \"{skill_name}\"?\n\n⚠️ Все данные о прогрессе будут потеряны!"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_confirmation("delete_skill", skill_key),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_delete_skill_"))
async def delete_skill(callback: CallbackQuery):
    """Delete skill"""
    skill_key = callback.data.replace("confirm_delete_skill_", "")
    user_id = str(callback.from_user.id)
    
    user = data_manager.get_user(user_id)
    
    if skill_key in user["skills"]:
        skill_name = user["skills"][skill_key]["name"]
        del user["skills"][skill_key]
        data_manager.update_user(user_id, user)
        
        text = f"✅ **Навык удален**\n\nНавык \"{skill_name}\" успешно удален из вашего списка."
    else:
        text = "❌ **Ошибка**\n\nНавык не найден."
    
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("materials_"))
async def show_study_materials(callback: CallbackQuery):
    """Show study materials for specific skill"""
    skill_key = callback.data.replace("materials_", "")
    user_id = str(callback.from_user.id)
    
    skills = data_manager.get_user_skills(user_id)
    
    if skill_key not in skills:
        await callback.answer("❌ Навык не найден")
        return
    
    skill = skills[skill_key]
    skill_name = skill["name"].lower()
    
    # Get materials for skill
    materials = STUDY_MATERIALS.get(skill_name, STUDY_MATERIALS["default"])
    
    text = f"📚 **Материалы для изучения**\n\n"
    text += f"🎯 Навык: **{skill['name']}**\n\n"
    
    # Videos section
    text += "🎥 **Видео и курсы:**\n"
    for video in materials["videos"][:3]:  # Show top 3
        text += f"• {video}\n"
    text += "\n"
    
    # Books section  
    text += "📖 **Книги и литература:**\n"
    for book in materials["books"][:3]:  # Show top 3
        text += f"• {book}\n"
    text += "\n"
    
    # Websites section
    text += "🌐 **Полезные сайты:**\n"
    for website in materials["websites"][:3]:  # Show top 3
        text += f"• {website}\n"
    text += "\n"
    
    text += "💡 _Начните с одного ресурса и изучайте последовательно!_"
    
    await callback.message.edit_text(text, reply_markup=get_skill_actions(skill_key), parse_mode="Markdown")
