"""
@Author: Borja Otero Ferreira
Model controller for IALab Suite API
"""
from flask import request, jsonify
from app.api.base_controller import BaseController
from app.services.model_service import model_service
from app.services.assistant_service import assistant_service
from app.models.data_models import ModelConfig, ApiResponse
from app.utils.logger import logger

class ModelController(BaseController):
    """Controller for model-related endpoints"""
    
    def get_models_and_formats(self):
        """Get available models and chat formats"""
        try:
            data = model_service.get_models_and_formats()
            return jsonify({
                'models': data.get('models', []),
                'formats': data.get('formats', [])
            })
            
        except Exception as e:
            logger.error(f"Error retrieving models and formats: {e}")
            return jsonify({
                'models': [],
                'formats': []
            }), 500
    
    def load_model(self):
        """Load a model with specified configuration """
        try:
            # Get form data
            model_path = request.form.get('model_path')
            gpu_layers = request.form.get('gpu_layers', '')
            system_message = request.form.get('system_message', '')
            temperature = request.form.get('temperature', '')
            context_size = request.form.get('context', '')
            
            if not model_path:
                return "Missing model_path parameter", 400
            
            # Validate model path
            if not model_service.validate_model_path(model_path):
                return "Invalid model path or file does not exist", 400
            
            # Parse parameters with defaults
            config = ModelConfig(
                path=model_path,
                temperature=float(temperature) if temperature else 0.81,
                gpu_layers=int(gpu_layers) if gpu_layers else -1,
                context_size=int(context_size) if context_size else 2048,
                system_message=system_message
            )
            
            result = assistant_service.load_model(config)
            
            if result.success:
                # Return the EXACT format the frontend expects
                return f'''
                \nModel:{model_path}
                \ntemp: {config.temperature}
                \nlayers: {config.gpu_layers}
                \nSM: {config.system_message}
                \nctx: {config.context_size}
                '''
            else:
                return f"Error loading model: {result.error}", 500
            
        except ValueError as e:
            return f"Invalid parameter values: {str(e)}", 400
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return f"Error loading model: {str(e)}", 500
    
    def unload_model(self):
        """Unload the current model"""
        try:
            result = assistant_service.unload_model()
            return 'Model uninstalled 🫗!'
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return f"Error unloading model: {str(e)}", 500

# Global model controller instance
model_controller = ModelController()
