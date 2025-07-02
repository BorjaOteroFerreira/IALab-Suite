"""
@Author: Borja Otero Ferreira
Logging utilities for IALab Suite API
"""
import logging
import os
from datetime import datetime
from app.config.settings import Config

class Logger:
    """Centralized logging utility"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            self._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Ensure logs directory exists
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        file_handler.setFormatter(file_formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Setup root logger
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger('ialab_suite')
    
    def get_logger(self, name: str = None):
        """Get logger instance"""
        if name:
            return logging.getLogger(f'ialab_suite.{name}')
        return self.logger
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

# Global logger instance
logger = Logger()
