from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline import get_main_menu, get_back_to_main
from utils.data_manager import DataManager
from utils.achievements import AchievementManager
from config import USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE

router = Router()

# Initialize data manager
data_manager = DataManager(USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE)
achievement_manager = AchievementManager(data_manager)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler"""
    await state.clear()
    
    user_id = str(message.from_user.id)
    user = data_manager.get_user(user_id)
    
    # Check for new achievements
    new_achievements = achievement_manager.check_achievements(user_id)
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🎯 Я твой персональный помощник для изучения новых навыков!\n\n"
        "✨ Что я умею:\n"
        "• Помогать отслеживать прогресс\n"
        "• Мотивировать и давать советы\n"
        "• Вести статистику обучения\n"
        "• Награждать достижениями\n\n"
        "📱 Выбери действие в меню ниже:"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_menu())
    
    # Show new achievements if any
    if new_achievements:
        achievement_text = "🎉 Новые достижения!\n\n"
        for ach in new_achievements:
            achievement_text += f"🏆 {ach['name']}\n{ach['description']}\n+{ach['points']} очков\n\n"
        
        await message.answer(achievement_text, reply_markup=get_back_to_main())

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command handler"""
    help_text = (
        "❓ **Помощь по использованию бота**\n\n"
        "🎯 **Основные функции:**\n"
        "• Добавление и управление навыками\n"
        "• Отслеживание времени практики\n"
        "• Система достижений и очков\n"
        "• Персональные советы и мотивация\n\n"
        "📊 **Прогресс:**\n"
        "• Ведите учет времени занятий\n"
        "• Отслеживайте серии (streak)\n"
        "• Ставьте цели по времени\n\n"
        "🏆 **Достижения:**\n"
        "• Получайте награды за активность\n"
        "• Собирайте очки за выполнение целей\n"
        "• Сравнивайте свой прогресс\n\n"
        "💡 **Советы:**\n"
        "• Получайте персональные рекомендации\n"
        "• Изучайте лучшие практики\n"
        "• Находите мотивацию для продолжения\n\n"
        "🚀 **Начните с добавления своего первого навыка!**"
    )
    
    await message.answer(help_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Show main menu"""
    await state.clear()
    
    text = (
        "🏠 **Главное меню**\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Show help via callback"""
    help_text = (
        "❓ **Помощь по использованию бота**\n\n"
        "🎯 **Основные функции:**\n"
        "• Добавление и управление навыками\n"
        "• Отслеживание времени практики\n"
        "• Система достижений и очков\n"
        "• Персональные советы и мотивация\n\n"
        "📊 **Как использовать:**\n"
        "1. Добавьте навык через \"➕ Добавить навык\"\n"
        "2. Записывайте сессии практики\n"
        "3. Отслеживайте прогресс и получайте достижения\n"
        "4. Получайте советы и мотивацию\n\n"
        "🚀 **Начните с добавления первого навыка!**"
    )
    
    await callback.message.edit_text(help_text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current action"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=get_main_menu()
    )
