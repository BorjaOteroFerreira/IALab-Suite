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
from app.api.tools_controller import tools_controller
from app.api.agent_controller import agent_controller
from app.services.assistant_service import assistant_service
# Importar el proveedor de instancias socketio
from app.utils import socket_instance

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
    
    # Almacenar la instancia socketio en el proveedor global
    socket_instance.set_socketio(socketio)
    
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
    
    # API routes - Tools
    app.route('/api/tools/available', methods=['GET'])(tools_controller.get_available_tools)
    app.route('/api/tools/selected', methods=['GET'])(tools_controller.get_selected_tools)
    app.route('/api/tools/selected', methods=['POST'])(tools_controller.set_selected_tools)
    app.route('/api/tools/refresh', methods=['POST'])(tools_controller.refresh_tools)
    
    # API routes - MCP Tools
    app.route('/api/remote/tools', methods=['GET'])(tools_controller.get_mcp_tools)
    app.route('/api/remote/tools/selected', methods=['GET'])(tools_controller.get_selected_remote_tools)
    app.route('/api/remote/tools/selected', methods=['POST'])(tools_controller.set_selected_remote_tools)
    
    # Register Blueprints - Agents
    app.register_blueprint(agent_controller)


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
        # Enviar el registro de herramientas al cliente recién conectado
        try:
            # Almacenar o actualizar la referencia en el proveedor global (por si acaso)
            socket_instance.set_socketio(socketio)
            # Enviar registro de herramientas usando el objeto socketio
            assistant_service.send_tools_registry_to_client(socketio)
            # Enviar registro de agentes al cliente
            assistant_service.send_agents_registry_to_client(socketio)
        except Exception as e:
            logger.error(f"Error sending registry on connection: {e}")
            try:
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            except ImportError:
                logger.error("No se pudo importar traceback para el registro de errores")
    
    @socketio.on('disconnect', namespace='/test')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected from WebSocket")
    
    @socketio.on('request_tools_registry', namespace='/test')
    def handle_request_tools_registry(data=None):
        """Handle request for tools registry from client"""
        try:
            logger.info("Client requested tools registry")
            # Asegurar que la referencia global esté actualizada
            socket_instance.set_socketio(socketio)
            # Enviar registro de herramientas al cliente actual
            assistant_service.send_tools_registry_to_client(socketio)
            return {'success': True, 'message': 'Tools registry sent'}
        except Exception as e:
            try:
                import traceback
                logger.error(f"Error sending tools registry on request: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
            except ImportError:
                logger.error(f"Error sending tools registry on request: {e}")
            return {'success': False, 'error': str(e)}
    
    @socketio.on('agent_selected', namespace='/test')
    def handle_agent_selected(data):
        """Handle agent selection from WebSocket"""
        try:
            logger.info(f"Agent selected via WebSocket: {data}")
            # Notificar a otros clientes conectados sobre el cambio
            socketio.emit('agent_changed', data, namespace='/test')
            return {'success': True}
        except Exception as e:
            logger.error(f"Error handling agent selection: {e}")
            return {'success': False, 'error': str(e)}

    @socketio.on('request_agents_registry', namespace='/test')
    def handle_request_agents_registry(data):
        """Handle request for agents registry"""
        try:
            logger.info("Agents registry requested via WebSocket")
            assistant_service.send_agents_registry_to_client(socketio)
            return {'success': True}
        except Exception as e:
            logger.error(f"Error sending agents registry: {e}")
            return {'success': False, 'error': str(e)}

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
                logger.info("Assistant service initialized successfully")
                app._assistant_initialized = True
            else:
                logger.error("Failed to initialize assistant service")
        except Exception as e:
            logger.error(f"Error initializing assistant: {e}")
            app._assistant_initialized = True  # Prevent infinite retry

def stop_server():
    """Stop the server gracefully"""
    logger.info("Shutting down server...")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'
