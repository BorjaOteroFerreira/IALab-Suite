"""
@Author: Borja Otero Ferreira
Assistant controller for IALab Suite API
"""
import time
from flask import request, jsonify
from app.api.base_controller import BaseController
from app.services.assistant_service import assistant_service
from app.models.data_models import UserInput, ApiResponse
from app.utils.logger import logger

class AssistantController(BaseController):
    """Controller for assistant-related endpoints"""
    
    def __init__(self):
        super().__init__()
        self.socketio = None
    
    def set_socketio(self, socketio):
        """Set SocketIO instance for real-time communication"""
        self.socketio = socketio
    
    def handle_user_input(self):
        """Handle user input for chat interaction"""
        try:
            data = self._get_json_data()
            content = data.get('content')
            tools = data.get('tools')
            rag = data.get('rag')
            
            logger.info(f"DEBUG: Received data - tools={tools}, rag={rag}")
            
            if not content:
                return jsonify({'error': 'Missing required field: content'}), 400
            
            user_input = UserInput(
                content=content,
                tools=tools,
                rag=rag
            )
            
            logger.info(f"Usuario dijo: {content}")
            result = assistant_service.process_user_input(user_input, self.socketio)
            
            # Return the EXACT format the frontend expects
            return 'Response finished! 📩'
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return f'Error: {str(e)}', 500
    
    
    def stop_response(self):
        """Stop the current response generation"""
        try:
            result = assistant_service.stop_response()
            
            # Emit stop signal via WebSocket if available
            if self.socketio and result.success:
                self.socketio.emit('response_stopped', {
                    'message': 'Response stopped by user',
                    'timestamp': time.time()
                }, namespace='/test')
            
            # Return the EXACT format the frontend expects
            return {"status": "success", "message": "Response stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping response: {e}")
            return {"status": "error", "message": f"Error stopping response: {str(e)}"}
    
    def handle_socket_user_input(self, data):
        """Handle user input from WebSocket connection"""
        try:
            content = data.get('content')
            tools = data.get('tools')
            rag = data.get('rag')
            
            logger.info(f"Socket DEBUG: Received data - tools={tools}, rag={rag}")
            
            if not content:
                return {'success': False, 'error': 'Missing content'}
            
            user_input = UserInput(
                content=content,
                tools=tools,
                rag=rag
            )
            
            result = assistant_service.process_user_input(user_input, self.socketio)
            return {'success': result.success, 'message': result.message}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global assistant controller instance
assistant_controller = AssistantController()
