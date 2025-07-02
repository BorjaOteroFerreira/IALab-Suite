"""
Services layer for IALab Suite
Capa de servicios que integra los componentes core
"""

from .assistant_service import AssistantService, assistant_service
from .model_service import ModelService, model_service 
from .chat_service import ChatService, chat_service

__all__ = [
    'AssistantService', 'assistant_service',
    'ModelService', 'model_service',
    'ChatService', 'chat_service'
]
