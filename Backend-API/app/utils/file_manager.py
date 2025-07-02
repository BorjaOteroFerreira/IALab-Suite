"""
@Author: Borja Otero Ferreira
File utilities for IALab Suite API
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config.settings import Config
from app.utils.logger import logger

class FileManager:
    """Handles file operations for the application"""
    
    def __init__(self):
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            Config.CHATS_DIR,
            Config.LOGS_DIR,
            Config.DOCUMENTS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations"""
        replacements = {
            '/': '-',
            ':': '-',
            ' ': '_',
            '?': '',
            '<': '',
            '>': '',
            '|': '',
            '*': '',
            '"': ''
        }
        
        for old, new in replacements.items():
            filename = filename.replace(old, new)
        
        return filename
    
    def save_chat_history(self, chat_name: str, history: Dict[str, Any]) -> bool:
        """Save chat history to file"""
        try:
            sanitized_name = self.sanitize_filename(chat_name)
            file_path = os.path.join(Config.CHATS_DIR, f'{sanitized_name}.json')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Chat history saved: {sanitized_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chat history {chat_name}: {e}")
            return False
    
    def load_chat_history(self, chat_name: str) -> Optional[Dict[str, Any]]:
        """Load chat history from file"""
        try:
            file_path = os.path.join(Config.CHATS_DIR, f'{chat_name}.json')
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            logger.info(f"Chat history loaded: {chat_name}")
            return history
            
        except Exception as e:
            logger.error(f"Error loading chat history {chat_name}: {e}")
            return None
    
    def delete_chat_history(self, chat_name: str) -> bool:
        """Delete chat history file"""
        try:
            file_path = os.path.join(Config.CHATS_DIR, f'{chat_name}.json')
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Chat history deleted: {chat_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting chat history {chat_name}: {e}")
            return False
    
    def list_chat_histories(self) -> List[str]:
        """List all available chat histories"""
        try:
            if not os.path.exists(Config.CHATS_DIR):
                return []
            
            files = os.listdir(Config.CHATS_DIR)
            chat_names = [
                file.replace('.json', '') 
                for file in files 
                if file.endswith('.json')
            ]
            
            chat_names.sort(reverse=True)
            return chat_names
            
        except Exception as e:
            logger.error(f"Error listing chat histories: {e}")
            return []
    
    def get_models_list(self, models_directory: str = None) -> List[str]:
        """Get list of available models"""
        try:
            directory = models_directory or Config.MODELS_DIRECTORY
            models = []
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".gguf"):
                        model_path = os.path.join(root, file)
                        models.append(model_path)
            
            return models
            
        except Exception as e:
            logger.error(f"Error getting models list: {e}")
            return []

# Global file manager instance
file_manager = FileManager()
