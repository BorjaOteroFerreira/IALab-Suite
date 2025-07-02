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
    
    def serve_playground(self):
        """Serve the playground page with initial data"""
        try:
            models_data = model_service.get_models_and_formats()
            chat_result = chat_service.list_chats()
            
            # Return JSON data instead of rendering template for now
            from flask import jsonify
            return jsonify({
                'models_list': models_data.get('models', []),
                'format_list': models_data.get('formats', []),
                'chat_list': chat_result.data if chat_result.success else []
            })
            
        except Exception as e:
            logger.error(f"Error serving playground: {e}")
            return jsonify({'error': 'Error loading playground data'}), 500
    
    def serve_letsencrypt_challenge(self, challenge):
        """Serve Let's Encrypt challenge files"""
        try:
            return send_from_directory('.well-known/acme-challenge', challenge)
        except Exception as e:
            logger.error(f"Error serving Let's Encrypt challenge {challenge}: {e}")
            return "Challenge not found", 404

# Global static controller instance
static_controller = StaticController()
