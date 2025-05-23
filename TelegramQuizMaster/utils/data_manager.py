import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

class DataManager:
    def __init__(self, users_file: str, achievements_file: str):
        self.users_file = users_file
        self.achievements_file = achievements_file
        self.ensure_data_directory()
        self.initialize_files()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs("data", exist_ok=True)
    
    def initialize_files(self):
        """Initialize data files if they don't exist"""
        if not os.path.exists(self.users_file):
            self.save_users_data({})
        
        if not os.path.exists(self.achievements_file):
            self.save_achievements_data({})
    
    def load_users_data(self) -> Dict[str, Any]:
        """Load users data from JSON file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading users data: {e}")
            return {}
    
    def save_users_data(self, data: Dict[str, Any]):
        """Save users data to JSON file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving users data: {e}")
    
    def load_achievements_data(self) -> Dict[str, Any]:
        """Load achievements data from JSON file"""
        try:
            with open(self.achievements_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading achievements data: {e}")
            return {}
    
    def save_achievements_data(self, data: Dict[str, Any]):
        """Save achievements data to JSON file"""
        try:
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving achievements data: {e}")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user data or create new user"""
        users = self.load_users_data()
        if user_id not in users:
            users[user_id] = {
                "skills": {},
                "total_points": 0,
                "achievements": [],
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "statistics": {
                    "total_sessions": 0,
                    "total_time_minutes": 0,
                    "tips_received": 0,
                    "motivations_received": 0
                }
            }
            self.save_users_data(users)
        return users[user_id]
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]):
        """Update user data"""
        users = self.load_users_data()
        users[user_id] = user_data
        users[user_id]["last_active"] = datetime.now().isoformat()
        self.save_users_data(users)
    
    def add_skill(self, user_id: str, skill_name: str, category: str):
        """Add a new skill for user"""
        user = self.get_user(user_id)
        skill_key = skill_name.lower()
        
        if skill_key not in user["skills"]:
            user["skills"][skill_key] = {
                "name": skill_name,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "total_time_minutes": 0,
                "sessions": 0,
                "streak": 0,
                "best_streak": 0,
                "last_session": None,
                "goal_minutes": 0,
                "notes": []
            }
            self.update_user(user_id, user)
            return True
        return False
    
    def add_session(self, user_id: str, skill_name: str, minutes: int, note: str = ""):
        """Add a practice session"""
        user = self.get_user(user_id)
        skill_key = skill_name.lower()
        
        if skill_key in user["skills"]:
            skill = user["skills"][skill_key]
            today = datetime.now().date().isoformat()
            
            # Update session data
            skill["total_time_minutes"] += minutes
            skill["sessions"] += 1
            
            # Update streak
            if skill["last_session"]:
                last_date = datetime.fromisoformat(skill["last_session"]).date()
                today_date = datetime.now().date()
                
                if (today_date - last_date).days == 1:
                    skill["streak"] += 1
                elif (today_date - last_date).days > 1:
                    skill["streak"] = 1
            else:
                skill["streak"] = 1
            
            # Update best streak
            if skill["streak"] > skill["best_streak"]:
                skill["best_streak"] = skill["streak"]
            
            skill["last_session"] = datetime.now().isoformat()
            
            # Add note if provided
            if note:
                skill["notes"].append({
                    "date": datetime.now().isoformat(),
                    "note": note,
                    "minutes": minutes
                })
            
            # Update user statistics
            user["statistics"]["total_sessions"] += 1
            user["statistics"]["total_time_minutes"] += minutes
            
            self.update_user(user_id, user)
            return skill["streak"]
        return 0
    
    def get_user_skills(self, user_id: str) -> Dict[str, Any]:
        """Get all user skills"""
        user = self.get_user(user_id)
        return user["skills"]
    
    def update_statistics(self, user_id: str, stat_type: str):
        """Update user statistics"""
        user = self.get_user(user_id)
        if stat_type in user["statistics"]:
            user["statistics"][stat_type] += 1
            self.update_user(user_id, user)
