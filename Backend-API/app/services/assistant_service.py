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
            
            # Set tools and RAG based on user input (always set, exactly like legacy)
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
            # El content ya debe ser el chat_history (lista de mensajes) como en legacy
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
    
    def process_ollama_request(self, content: Any, socketio) -> ApiResponse:
        """Process Ollama-compatible request"""
        try:
            if not self.is_ready():
                return ApiResponse(
                    success=False,
                    message="Assistant not ready",
                    error="Assistant is not initialized"
                )
            
            logger.info(f"Processing Ollama request with content: {content}")
            
            # Remove system message (first element) as in original code
            if content and isinstance(content, list) and len(content) > 0:
                content.pop(0)  # Elimina el mensaje del sistema
            
            # Use the legacy assistant method for Ollama compatibility
            self._assistant.emit_ollama_response_stream(content, socketio)
            
            logger.info("Ollama request processed successfully")
            
            return ApiResponse(
                success=True,
                message="Ollama request processed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error processing Ollama request: {e}")
            return ApiResponse(
                success=False,
                message="Failed to process Ollama request",
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

# Global assistant service instance
assistant_service = AssistantService()
