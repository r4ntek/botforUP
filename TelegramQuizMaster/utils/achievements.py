from typing import List, Dict, Any
from config import ACHIEVEMENTS_CONFIG

class AchievementManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.achievements_config = ACHIEVEMENTS_CONFIG
    
    def check_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Check and return new achievements for user"""
        user = self.data_manager.get_user(user_id)
        current_achievements = set(user.get("achievements", []))
        new_achievements = []
        
        # Check first skill achievement
        if "first_skill" not in current_achievements and user["skills"]:
            new_achievements.append("first_skill")
        
        # Check multiple skills achievement
        if "multiple_skills" not in current_achievements and len(user["skills"]) >= 3:
            new_achievements.append("multiple_skills")
        
        # Check streak achievements
        max_streak = max([skill["streak"] for skill in user["skills"].values()], default=0)
        
        if "streak_3" not in current_achievements and max_streak >= 3:
            new_achievements.append("streak_3")
        
        if "streak_7" not in current_achievements and max_streak >= 7:
            new_achievements.append("streak_7")
        
        if "streak_30" not in current_achievements and max_streak >= 30:
            new_achievements.append("streak_30")
        
        # Check tips achievements
        tips_count = user["statistics"].get("tips_received", 0)
        
        if "first_tip" not in current_achievements and tips_count >= 1:
            new_achievements.append("first_tip")
        
        if "tips_fan" not in current_achievements and tips_count >= 25:
            new_achievements.append("tips_fan")
        
        # Award new achievements
        if new_achievements:
            user["achievements"].extend(new_achievements)
            
            # Add points
            total_points = sum(self.achievements_config[ach]["points"] for ach in new_achievements)
            user["total_points"] += total_points
            
            self.data_manager.update_user(user_id, user)
        
        return [self.achievements_config[ach] for ach in new_achievements]
    
    def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user achievements"""
        user = self.data_manager.get_user(user_id)
        achievements = user.get("achievements", [])
        return [self.achievements_config[ach] for ach in achievements if ach in self.achievements_config]
    
    def get_achievement_progress(self, user_id: str) -> str:
        """Get achievement progress text"""
        user = self.data_manager.get_user(user_id)
        total_achievements = len(self.achievements_config)
        user_achievements = len(user.get("achievements", []))
        
        return f"🏆 Достижения: {user_achievements}/{total_achievements}\n💎 Очки: {user['total_points']}"
