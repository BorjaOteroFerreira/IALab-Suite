"""
@Author: Borja Otero Ferreira
Main application factory for IALab Suite API
"""
import os
import signal
import time
from flask import Flask
from flask_socketio import SocketIO
from app.config.settings import get_config
from app.utils.logger import logger
from app.api.chat_controller import chat_controller
from app.api.model_controller import model_controller
from app.api.assistant_controller import assistant_controller
from app.api.static_controller import static_controller
from app.services.assistant_service import assistant_service

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Show banner
    print("""
╭─────────────╮
│    IALab    │
├─^───────────┤
│             │
│   ███████   │
│  ██─────██  │
│  ██ o o ██  │
│  ██  ^  ██  │
│  █████████  │
│             │
╰─┬───────────╯
  │
  └─╼═╼═╼═╼═╼═╼[|= | Cogito, ergo svm |
   
              """)
    
    # Get configuration
    config = get_config(config_name)
    
    # Create Flask app
    app = Flask(
        __name__, 
        static_url_path='', 
        static_folder=config.FRONTEND_BUILD_DIR, 
        template_folder=config.TEMPLATES_DIR
    )
    
    # Configure app
    app.config.from_object(config)
    
    # Create SocketIO
    socketio = SocketIO(
        app, 
        async_mode=config.SOCKETIO_ASYNC_MODE,
        cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS,
        max_size=config.SOCKETIO_MAX_SIZE
    )
    
    # Set SocketIO reference in assistant controller
    assistant_controller.set_socketio(socketio)
    
    # Register routes
    _register_routes(app)
    
    # Register WebSocket events
    _register_socket_events(socketio)
    
    # Register hooks
    _register_hooks(app)
    
    logger.info("IALab Suite API initialized successfully")
    
    return app, socketio

def _register_routes(app):
    """Register all application routes"""
    
    # Static routes
    app.route('/')(static_controller.serve_index)
    app.route('/fonts/<path:filename>')(static_controller.serve_fonts)
    app.route('/playground')(static_controller.serve_playground)
    app.route('/.well-known/acme-challenge/<challenge>')(static_controller.serve_letsencrypt_challenge)
    
    # API routes - Models
    app.route('/api/models-and-formats', methods=['GET'])(model_controller.get_models_and_formats)
    app.route('/load_model', methods=['POST'])(model_controller.load_model)
    app.route('/unload_model', methods=['POST'])(model_controller.unload_model)
    
    # API routes - Chat
    app.route('/actualizar_historial', methods=['POST'])(chat_controller.save_chat)
    app.route('/eliminar_historial', methods=['DELETE'])(chat_controller.delete_chat)
    app.route('/recuperar_historial', methods=['GET'])(chat_controller.load_chat)
    
    # API routes - Assistant
    app.route('/user_input', methods=['POST'])(assistant_controller.handle_user_input)
    app.route('/stop_response', methods=['POST'])(assistant_controller.stop_response)


def _register_socket_events(socketio):
    """Register WebSocket events"""
    
    @socketio.on('user_input', namespace='/test')
    def handle_socket_user_input(data):
        """Handle user input from WebSocket"""
        try:
            logger.info(f"Socket user input received: {data}")
            result = assistant_controller.handle_socket_user_input(data)
            return result
        except Exception as e:
            logger.error(f"Error handling socket user input: {e}")
            return {'success': False, 'error': str(e)}
    
    @socketio.on('connect', namespace='/test')
    def handle_connect():
        """Handle client connection"""
        logger.info("Client connected to WebSocket")
    
    @socketio.on('disconnect', namespace='/test')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected from WebSocket")

def _register_hooks(app):
    """Register application hooks"""
    
    @app.before_request  
    def initialize_assistant():
        """Initialize assistant before requests"""
        # Skip initialization if already done
        if hasattr(app, '_assistant_initialized'):
            return
            
        try:
            success = assistant_service.initialize()
            if success:
                logger.info("🤖 Assistant service initialized successfully")
                app._assistant_initialized = True
            else:
                logger.error("❌ Failed to initialize assistant service")
        except Exception as e:
            logger.error(f"Error initializing assistant: {e}")
            app._assistant_initialized = True  # Prevent infinite retry

def stop_server():
    """Stop the server gracefully"""
    logger.info("Shutting down server...")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'
