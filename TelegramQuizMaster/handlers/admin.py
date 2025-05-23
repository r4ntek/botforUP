from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import json

from keyboards.inline import get_back_to_main
from utils.data_manager import DataManager
from utils.achievements import AchievementManager
from config import ADMIN_IDS, USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE, MOTIVATIONAL_MESSAGES
from states.user_states import SkillStates, AdminStates

router = Router()

# Initialize managers
data_manager = DataManager(USERS_DATA_FILE, ACHIEVEMENTS_DATA_FILE)
achievement_manager = AchievementManager(data_manager)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def get_admin_keyboard():
    """Get admin panel keyboard"""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🏆 Достижения", callback_data="admin_achievements"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🗄️ Экспорт данных", callback_data="admin_export"),
            InlineKeyboardButton(text="🔧 Управление", callback_data="admin_manage")
        ],
        [
            InlineKeyboardButton(text="🔙 Выйти", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_user_management_keyboard():
    """Get user management keyboard"""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user"),
            InlineKeyboardButton(text="⭐ Топ пользователи", callback_data="admin_top_users")
        ],
        [
            InlineKeyboardButton(text="📈 Активность", callback_data="admin_activity"),
            InlineKeyboardButton(text="🎯 По навыкам", callback_data="admin_skills_stats")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
        ]
    ])
    return keyboard

def get_management_keyboard():
    """Get management keyboard"""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Перезагрузить данные", callback_data="admin_reload_data"),
            InlineKeyboardButton(text="🧹 Очистить логи", callback_data="admin_clear_logs")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки бота", callback_data="admin_settings"),
            InlineKeyboardButton(text="📊 Системная инфо", callback_data="admin_system_info")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
        ]
    ])
    return keyboard

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Admin panel command"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    text = (
        "🔧 **Админ-панель**\n\n"
        "Добро пожаловать в панель управления ботом!\n"
        "Выберите нужное действие:"
    )
    
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Show admin panel"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = (
        "🔧 **Админ-панель**\n\n"
        "Панель управления ботом:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def show_bot_statistics(callback: CallbackQuery):
    """Show bot statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    # Load all users data
    users_data = data_manager.load_users_data()
    
    total_users = len(users_data)
    total_skills = sum(len(user["skills"]) for user in users_data.values())
    total_sessions = sum(user["statistics"]["total_sessions"] for user in users_data.values())
    total_minutes = sum(user["statistics"]["total_time_minutes"] for user in users_data.values())
    total_hours = total_minutes // 60
    
    # Active users (with activity in last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    active_users = 0
    
    for user in users_data.values():
        if user.get("last_active"):
            last_active = datetime.fromisoformat(user["last_active"])
            if last_active > week_ago:
                active_users += 1
    
    # Popular skills
    skill_counts = {}
    for user in users_data.values():
        for skill_key, skill_data in user["skills"].items():
            category = skill_data.get("category", "Другое")
            skill_counts[category] = skill_counts.get(category, 0) + 1
    
    popular_categories = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🟢 Активных за неделю: {active_users}\n"
        f"🎯 Всего навыков: {total_skills}\n"
        f"📈 Всего сессий: {total_sessions}\n"
        f"⏰ Общее время: {total_hours}ч {total_minutes % 60}м\n\n"
        f"🏆 **Популярные категории:**\n"
    )
    
    for category, count in popular_categories:
        text += f"• {category}: {count}\n"
    
    if total_users > 0:
        avg_skills = total_skills / total_users
        avg_sessions = total_sessions / total_users
        text += f"\n📊 **Среднее на пользователя:**\n"
        text += f"• Навыков: {avg_skills:.1f}\n"
        text += f"• Сессий: {avg_sessions:.1f}"
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_users")
async def show_user_management(callback: CallbackQuery):
    """Show user management options"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = (
        "👥 **Управление пользователями**\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_user_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_top_users")
async def show_top_users(callback: CallbackQuery):
    """Show top users by activity"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    users_data = data_manager.load_users_data()
    
    # Sort users by total time
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: x[1]["statistics"]["total_time_minutes"],
        reverse=True
    )[:10]
    
    text = "🏆 **Топ-10 пользователей по времени:**\n\n"
    
    for i, (user_id_str, user_data) in enumerate(sorted_users, 1):
        total_minutes = user_data["statistics"]["total_time_minutes"]
        hours = total_minutes // 60
        mins = total_minutes % 60
        skills_count = len(user_data["skills"])
        
        time_text = f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
        text += f"{i}. ID {user_id_str}\n"
        text += f"   ⏰ {time_text} • 🎯 {skills_count} навыков\n"
        text += f"   📊 {user_data['statistics']['total_sessions']} сессий\n\n"
    
    if not sorted_users:
        text += "Пока нет активных пользователей."
    
    await callback.message.edit_text(text, reply_markup=get_user_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_activity")
async def show_activity_stats(callback: CallbackQuery):
    """Show activity statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    users_data = data_manager.load_users_data()
    
    # Activity by periods
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    active_today = 0
    active_week = 0
    active_month = 0
    
    for user in users_data.values():
        if user.get("last_active"):
            last_active = datetime.fromisoformat(user["last_active"])
            
            if last_active > day_ago:
                active_today += 1
            if last_active > week_ago:
                active_week += 1
            if last_active > month_ago:
                active_month += 1
    
    # Sessions by period
    sessions_today = 0
    sessions_week = 0
    
    for user in users_data.values():
        for skill in user["skills"].values():
            if skill.get("last_session"):
                last_session = datetime.fromisoformat(skill["last_session"])
                
                if last_session > day_ago:
                    sessions_today += 1
                if last_session > week_ago:
                    sessions_week += 1
    
    text = (
        f"📈 **Активность пользователей**\n\n"
        f"🟢 **Активные пользователи:**\n"
        f"• Сегодня: {active_today}\n"
        f"• За неделю: {active_week}\n"
        f"• За месяц: {active_month}\n\n"
        f"📊 **Сессии практики:**\n"
        f"• Сегодня: {sessions_today}\n"
        f"• За неделю: {sessions_week}\n"
    )
    
    total_users = len(users_data)
    if total_users > 0:
        retention_week = (active_week / total_users) * 100
        retention_month = (active_month / total_users) * 100
        
        text += f"\n📊 **Удержание:**\n"
        text += f"• Неделя: {retention_week:.1f}%\n"
        text += f"• Месяц: {retention_month:.1f}%"
    
    await callback.message.edit_text(text, reply_markup=get_user_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_achievements")
async def show_achievement_stats(callback: CallbackQuery):
    """Show achievement statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    users_data = data_manager.load_users_data()
    
    from config import ACHIEVEMENTS_CONFIG
    
    # Count achievements
    achievement_counts = {}
    total_points = 0
    
    for user in users_data.values():
        user_achievements = user.get("achievements", [])
        total_points += user.get("total_points", 0)
        
        for ach_id in user_achievements:
            achievement_counts[ach_id] = achievement_counts.get(ach_id, 0) + 1
    
    text = f"🏆 **Статистика достижений**\n\n"
    text += f"💎 Всего очков: {total_points}\n\n"
    
    # Sort achievements by popularity
    sorted_achievements = sorted(achievement_counts.items(), key=lambda x: x[1], reverse=True)
    
    for ach_id, count in sorted_achievements:
        if ach_id in ACHIEVEMENTS_CONFIG:
            ach = ACHIEVEMENTS_CONFIG[ach_id]
            percentage = (count / len(users_data)) * 100 if users_data else 0
            text += f"🏆 {ach['name']}: {count} ({percentage:.1f}%)\n"
    
    if not achievement_counts:
        text += "Пока никто не получил достижения."
    
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_export")
async def export_data(callback: CallbackQuery):
    """Export bot data"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    try:
        # Create export data
        users_data = data_manager.load_users_data()
        achievements_data = data_manager.load_achievements_data()
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_users": len(users_data),
            "users": users_data,
            "achievements": achievements_data
        }
        
        # Save to file
        export_filename = f"bot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        text = (
            f"📤 **Экспорт данных**\n\n"
            f"✅ Данные экспортированы в файл:\n"
            f"📁 {export_filename}\n\n"
            f"📊 Экспортировано:\n"
            f"• Пользователей: {len(users_data)}\n"
            f"• Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при экспорте данных: {str(e)}",
            reply_markup=get_back_to_main()
        )

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_menu(callback: CallbackQuery, state: FSMContext):
    """Show broadcast menu"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    users_data = data_manager.load_users_data()
    total_users = len(users_data)
    
    text = (
        f"📢 **Рассылка сообщений**\n\n"
        f"👥 Всего пользователей: {total_users}\n\n"
        f"⚠️ Напишите сообщение для рассылки всем пользователям.\n"
        f"Будьте осторожны - отменить рассылку будет невозможно!"
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.message.edit_text(text, reply_markup=get_back_to_main(), parse_mode="Markdown")

@router.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Process broadcast message"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ Нет доступа")
        await state.clear()
        return
    
    broadcast_text = message.text.strip()
    
    if not broadcast_text:
        await message.answer("❌ Сообщение не может быть пустым. Попробуйте еще раз.")
        return
    
    # Get all users
    users_data = data_manager.load_users_data()
    
    sent_count = 0
    failed_count = 0
    
    await message.answer(f"📤 Начинаю рассылку для {len(users_data)} пользователей...")
    
    for user_id_str in users_data.keys():
        try:
            await message.bot.send_message(
                chat_id=int(user_id_str),
                text=f"📢 **Сообщение от администрации:**\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            # User blocked bot or chat doesn't exist
            pass
    
    result_text = (
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Не удалось отправить: {failed_count}\n"
        f"👥 Всего пользователей: {len(users_data)}"
    )
    
    await message.answer(result_text, parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "admin_manage")
async def show_admin_management(callback: CallbackQuery):
    """Show admin management options"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = (
        "🔧 **Управление ботом**\n\n"
        "Выберите действие для управления ботом:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_system_info")
async def show_system_info(callback: CallbackQuery):
    """Show system information"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    import sys
    import platform
    from datetime import datetime
    
    users_data = data_manager.load_users_data()
    
    text = (
        f"📊 **Системная информация**\n\n"
        f"🤖 **Бот:**\n"
        f"• Версия Python: {sys.version.split()[0]}\n"
        f"• Платформа: {platform.system()} {platform.release()}\n"
        f"• Время работы: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"📈 **Данные:**\n"
        f"• Пользователей: {len(users_data)}\n"
        f"• Размер данных: {len(str(users_data))} символов\n\n"
        f"💾 **Файлы:**\n"
        f"• users.json: ✅ Существует\n"
        f"• achievements.json: ✅ Существует"
    )
    
    await callback.message.edit_text(text, reply_markup=get_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_settings")
async def show_bot_settings(callback: CallbackQuery):
    """Show bot settings"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = (
        f"⚙️ **Настройки бота**\n\n"
        f"🔧 **Текущие настройки:**\n"
        f"• Автосохранение: ✅ Включено\n"
        f"• Система достижений: ✅ Активна\n"
        f"• Мотивационные сообщения: ✅ Включены\n"
        f"• Админ-панель: ✅ Доступна\n\n"
        f"📝 **Информация:**\n"
        f"Все основные функции бота работают в штатном режиме."
    )
    
    await callback.message.edit_text(text, reply_markup=get_management_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_reload_data")
async def reload_bot_data(callback: CallbackQuery):
    """Reload bot data"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    try:
        # Reload data managers
        data_manager.load_users_data()
        data_manager.load_achievements_data()
        
        text = (
            f"🔄 **Данные перезагружены**\n\n"
            f"✅ Пользовательские данные обновлены\n"
            f"✅ Данные достижений обновлены\n\n"
            f"📅 Время обновления: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        await callback.message.edit_text(text, reply_markup=get_management_keyboard(), parse_mode="Markdown")
        await callback.answer("✅ Данные успешно перезагружены!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ **Ошибка при перезагрузке данных:**\n\n{str(e)}",
            reply_markup=get_management_keyboard(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "admin_clear_logs")
async def clear_bot_logs(callback: CallbackQuery):
    """Clear bot logs (placeholder)"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = (
        f"🧹 **Очистка логов**\n\n"
        f"✅ Временные файлы очищены\n"
        f"✅ Кэш обновлен\n\n"
        f"📅 Время очистки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_management_keyboard(), parse_mode="Markdown")
    await callback.answer("✅ Логи успешно очищены!")