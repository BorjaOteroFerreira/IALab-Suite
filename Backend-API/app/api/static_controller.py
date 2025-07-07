"""
@Author: Borja Otero Ferreira
Static controller for IALab Suite API
"""
import os
from flask import render_template, send_from_directory
from app.api.base_controller import BaseController
from app.services.model_service import model_service
from app.services.chat_service import chat_service
from app.config.settings import Config
from app.utils.logger import logger

class StaticController(BaseController):
    """Controller for static content and templates"""
    
    def serve_index(self):
        """Serve the main index page"""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error serving index: {e}")
            return "Error loading page", 500
    
    def serve_fonts(self, filename):
        """Serve font files"""
        try:
            # Try build/fonts directory first
            build_fonts_path = os.path.join(Config.FRONTEND_BUILD_DIR, 'fonts', filename)
            if os.path.exists(build_fonts_path):
                return send_from_directory(
                    os.path.join(Config.FRONTEND_BUILD_DIR, 'fonts'), 
                    filename
                )
            
            # Fallback to public/fonts
            public_fonts_path = os.path.join('frontend/public/fonts', filename)
            if os.path.exists(public_fonts_path):
                return send_from_directory('frontend/public/fonts', filename)
            
            return "Font not found", 404
            
        except Exception as e:
            logger.error(f"Error serving font {filename}: {e}")
            return "Font error", 500
    

# Global static controller instance
static_controller = StaticController()
