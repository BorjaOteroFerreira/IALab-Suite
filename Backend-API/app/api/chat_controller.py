"""
@Author: Borja Otero Ferreira
Chat controller for IALab Suite API
"""
from flask import request, jsonify
from app.api.base_controller import BaseController
from app.services.chat_service import chat_service
from app.models.data_models import ApiResponse

class ChatController(BaseController):
    """Controller for chat-related endpoints"""
    
    def save_chat(self):
        """Save chat history"""
        try:
            data = self._get_json_data()
            chat_name = data.get('nombre_chat')
            history = data.get('historial')
            
            if not chat_name or not history:
                return jsonify({'error': 'Missing required fields: nombre_chat and historial'}), 400
            
            result = chat_service.save_chat(chat_name, history)
            
            if result.success:
                if "created" in result.message.lower():
                    return jsonify({'message': f'Historial {chat_name} creado exitosamente.'}), 201
                else:
                    return jsonify({'message': f'Historial {chat_name} actualizado exitosamente.'}), 200
            else:
                return jsonify({'error': result.error}), 500
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def load_chat(self):
        """Load chat history"""
        try:
            chat_name = request.args.get('nombre_chat')
            
            if not chat_name:
                # Return list of all chats if no specific chat requested
                result = chat_service.list_chats()
                if result.success:
                    return jsonify(result.data), 200
                else:
                    return jsonify([]), 200
            
            result = chat_service.load_chat(chat_name)
            
            if result.success:
                return jsonify(result.data), 200
            else:
                return jsonify({'error': f'No se encontró el historial {chat_name}.'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def delete_chat(self):
        """Delete chat history"""
        try:
            chat_name = request.args.get('nombre_chat')
            
            if not chat_name:
                return jsonify({'error': 'Missing required parameter: nombre_chat'}), 400
            
            result = chat_service.delete_chat(chat_name)
            
            if result.success:
                return jsonify({'message': f'Historial {chat_name} eliminado exitosamente.'}), 200
            else:
                return jsonify({'error': f'No se encontró el historial {chat_name}.'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Global chat controller instance
chat_controller = ChatController()
