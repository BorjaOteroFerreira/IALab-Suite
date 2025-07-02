"""
@Author: Borja Otero Ferreira
Assistant service for IALab Suite API
Migrado completamente a la arquitectura modular
"""
from typing import Optional, List, Dict, Any
from app.core.assistant import Assistant
from app.core.cortex import Cortex
from app.core.rag import Retriever
from app.core.socket_handler import SocketResponseHandler
from app.models.data_models import ModelConfig, UserInput, ApiResponse
from app.utils.logger import logger
from app.config.settings import Config
# Importar el proveedor de instancias socketio
from app.utils import socket_instance

class AssistantService:
    """Service layer for Assistant operations"""
    
    def __init__(self):
        self._assistant: Optional[Assistant] = None
        self._is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize the assistant"""
        try:
            if not self._is_initialized:
                self._assistant = Assistant()
                
                # Inicializar también el tools_manager
                try:
                    from app.core.tools_manager import tools_manager
                    from tools.tool_registry import ToolRegistry
                    from app.core.socket_handler import SocketResponseHandler
                    
                    # Asegurar que el registry esté inicializado
                    tool_registry = ToolRegistry()
                    tool_registry.discover_tools()
                    
                    # Inicializar el tools_manager con el registry
                    tools_manager.initialize_registry(tool_registry)
                    logger.info("🔧 Tools manager initialized with assistant service")
                    
                    # Importante: Guardar referencia al socket para poder enviar actualizaciones más adelante
                    self._tools_registry = tool_registry
                    self._tools_manager = tools_manager
                    
                except ImportError as e:
                    logger.warning(f"Could not initialize tools manager: {e}")
                
                self._is_initialized = True
                logger.info("🤖 Assistant service initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing assistant: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Check if assistant is ready"""
        return self._is_initialized and self._assistant is not None
    
    def load_model(self, config: ModelConfig) -> ApiResponse:
        """Load a model with given configuration"""
        try:
            if not self.is_ready():
                if not self.initialize():
                    return ApiResponse(
                        success=False,
                        message="Failed to initialize assistant",
                        error="Assistant initialization failed"
                    )
            
            # Unload existing model first
            self.unload_model()
            
            # Load new model using the correct parameter order
            self._assistant.load_model(
                model_path=config.path,
                new_temperature=config.temperature,
                n_gpu_layer=config.gpu_layers,
                new_system_message=config.system_message,
                context=config.context_size,
                max_response_tokens=config.context_size
            )
            
            logger.info(f"Model loaded: {config.path}")
            
            return ApiResponse(
                success=True,
                message="Model loaded successfully",
                data={
                    'model_path': config.path,
                    'temperature': config.temperature,
                    'gpu_layers': config.gpu_layers,
                    'context_size': config.context_size,
                    'system_message': config.system_message
                }
            )
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return ApiResponse(
                success=False,
                message="Failed to load model",
                error=str(e)
            )
    
    def unload_model(self) -> ApiResponse:
        """Unload the current model"""
        try:
            if self.is_ready() and self._assistant:
                self._assistant.unload_model()
                logger.info("Model unloaded")
                
            return ApiResponse(
                success=True,
                message="Model unloaded successfully"
            )
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return ApiResponse(
                success=False,
                message="Failed to unload model",
                error=str(e)
            )
    
    def process_user_input(self, user_input: UserInput, socketio) -> ApiResponse:
        """Process user input and generate response"""
        try:
            if not self.is_ready():
                return ApiResponse(
                    success=False,
                    message="Assistant not ready",
                    error="Assistant is not initialized"
                )
            
            # Set tools and RAG based on user input 
            # Asegurar que los valores sean siempre booleanos
            tools_value = bool(user_input.tools) if user_input.tools is not None else False
            rag_value = bool(user_input.rag) if user_input.rag is not None else False
            
            self._assistant.set_tools(tools_value)
            self._assistant.set_rag(rag_value)
            logger.info(f"🔧 Tools configurado como: {tools_value}")
            print(f"🔧 Tools configurado como: {tools_value}")
            logger.info(f"🔧 RAG configurado como: {rag_value}")
            print(f"🔧 RAG configurado como: {rag_value}")
            
            # Process the input using the legacy assistant method
            logger.info(f"Processing user input: {user_input.content}")
            self._assistant.add_user_input(user_input.content, socketio)
            
            logger.info("User input processed successfully")
            
            return ApiResponse(
                success=True,
                message="User input processed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return ApiResponse(
                success=False,
                message="Failed to process user input",
                error=str(e)
            )
    

    
    def stop_response(self) -> ApiResponse:
        """Stop the current response generation"""
        try:
            if self.is_ready() and self._assistant:
                self._assistant.stop_response()
                logger.info("Response stopped by user")
                
            return ApiResponse(
                success=True,
                message="Response stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Error stopping response: {e}")
            return ApiResponse(
                success=False,
                message="Failed to stop response",
                error=str(e)
            )
    
    def send_tools_registry_to_client(self, socketio_instance=None) -> None:
        """Envía el registro de herramientas disponibles a un cliente recién conectado"""
        try:
            if hasattr(self, '_tools_manager') and self._tools_manager:
                from app.api.tools_controller import make_json_serializable
                
                # Obtener el resumen de herramientas desde el tools_manager
                tools_summary = self._tools_manager.get_tools_summary()
                
                # Convertir a formato serializable
                serializable_summary = make_json_serializable(tools_summary)
                
                # Usar la instancia proporcionada o la global si no se proporciona
                socketio = socketio_instance if socketio_instance else socket_instance.get_socketio()
                
                if socketio:
                    # Emitir el registro de herramientas al cliente
                    logger.info(f"🔧 Enviando registro de herramientas: {len(serializable_summary.get('available_tools', {}))} herramientas")
                    socketio.emit('tools_registry', serializable_summary, namespace='/test')
                    
                    # También enviar las herramientas actualmente seleccionadas
                    selected_tools = self._tools_manager.get_selected_tools()
                    logger.info(f"🔧 Enviando herramientas seleccionadas: {len(selected_tools)} herramientas")
                    socketio.emit('tools_selection_update', selected_tools, namespace='/test')
                else:
                    logger.warning("No se pudo enviar el registro de herramientas: instancia socketio no disponible")
        except Exception as e:
            logger.error(f"Error sending tools registry to client: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

# Global assistant service instance
assistant_service = AssistantService()
