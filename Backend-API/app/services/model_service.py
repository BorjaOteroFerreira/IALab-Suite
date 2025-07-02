"""
@Author: Borja Otero Ferreira
Model service for IALab Suite API
"""
from typing import List, Dict, Any
from llama_cpp.llama_chat_format import LlamaChatCompletionHandlerRegistry
from app.utils.file_manager import file_manager
from app.utils.logger import logger
from app.config.settings import Config

class ModelService:
    """Service for model-related operations"""
    
    def __init__(self):
        self._chat_formats_cache = None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            models = file_manager.get_models_list(Config.MODELS_DIRECTORY)
            logger.debug(f"Found {len(models)} available models")
            return models
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def get_chat_formats(self) -> List[str]:
        """Get list of available chat formats"""
        try:
            if self._chat_formats_cache is None:
                registry = LlamaChatCompletionHandlerRegistry()
                self._chat_formats_cache = list(registry._chat_handlers.keys())
                logger.debug(f"Loaded {len(self._chat_formats_cache)} chat formats")
            
            return self._chat_formats_cache
        except Exception as e:
            logger.error(f"Error getting chat formats: {e}")
            return []
    
    def get_models_and_formats(self) -> Dict[str, List[str]]:
        """Get both models and formats in a single call"""
        return {
            'models': self.get_available_models(),
            'formats': self.get_chat_formats()
        }
    
    def validate_model_path(self, model_path: str) -> bool:
        """Validate if model path exists and is accessible"""
        try:
            import os
            return os.path.exists(model_path) and model_path.endswith('.gguf')
        except Exception as e:
            logger.error(f"Error validating model path {model_path}: {e}")
            return False

# Global model service instance
model_service = ModelService()
