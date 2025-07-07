"""
@Author: Borja Otero Ferreira
Configuration settings for IALab Suite API
"""
import os
from typing import Optional

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_MAX_SIZE = 1024 * 1024  # 1MB
    
    # Model Configuration
    DEFAULT_MODEL_PATH = "Z:/Modelos LM Studio/lmstudio-community/gemma-3-12b-it-GGUF/gemma-3-12b-it-Q4_K_M.gguf"
    DEFAULT_CHAT_FORMAT = "chatml"
    MODELS_DIRECTORY = "Z:/Modelos LM Studio/"
    
    # Directory Configuration
    FRONTEND_BUILD_DIR = 'frontend/build'
    TEMPLATES_DIR = 'templates'
    CHATS_DIR = 'chats'
    LOGS_DIR = 'logs'
    DOCUMENTS_DIR = 'documents'
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/flask_log.log'
    
    # Model Default Parameters
    DEFAULT_TEMPERATURE = 0.81
    DEFAULT_GPU_LAYERS = -1
    DEFAULT_CONTEXT_SIZE = 2048

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SOCKETIO_CORS_ALLOWED_ORIGINS = []  # Configure specific origins in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Production security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config_map.get(config_name, DevelopmentConfig)
