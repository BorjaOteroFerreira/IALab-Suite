"""
@Author: Borja Otero Ferreira
Assistant - Core component for LLM interaction and orchestration
Migración completa desde Assistant.py legacy manteniendo el flujo original
"""
import copy
import platform
import time
import gc
from typing import Optional, Any, List, Dict
from colorama import Fore, Style
from llama_cpp import Llama as Model
from app.utils.logger import logger


class Assistant:
    """
    Core Assistant functionality integrated into the modular architecture
    Migración completa manteniendo el flujo exacto del legacy
    """
    
    def __init__(self):
        # Estado del modelo 
        self.model = None
        self.temperature = 0.3
        self.max_context_tokens = 8192
        self.max_assistant_tokens = 8192
        self.gpu_layers = -1
        self.is_processing = False
        self.stop_emit = False
        self.tools = False
        self.rag = False
        
        # Sistema de mensaje por defecto 
        self.default_system_message = '''
Eres un asistente con una personalidad amable y honesta.
Si no sabes la respuesta a una pregunta, no compartas información falsa y no te desvíes de la pregunta.
'''
        
        # Configuración de dispositivo según el sistema operativo 
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = {"device": "cuda", "cuda_device_id": 0}
            self.use_nmap = True
        elif platform.system() == 'Darwin':
            self.device_options = {"device": "metal", "metal_device_id": 0}
            self.use_nmap = True
        else:
            raise RuntimeError("Sistema operativo no compatible")
        
        logger.info("Assistant initialized")
    
    def load_model(self, model_path: str, new_temperature: float, n_gpu_layer: int, 
                   new_system_message: str, context: int, max_response_tokens: int):
        """Carga un modelo específico con configuración personalizada"""
        # Validar y establecer parámetros
        self.model_path = model_path
        self.temperature = new_temperature if isinstance(new_temperature, float) else self.temperature
        self.gpu_layers = int(n_gpu_layer) if isinstance(n_gpu_layer, int) else self.gpu_layers
        self.max_context_tokens = context if isinstance(context, int) else self.max_context_tokens
        self.max_assistant_tokens = max_response_tokens if isinstance(max_response_tokens, int) else self.max_assistant_tokens
        self.default_system_message = new_system_message if new_system_message else self.default_system_message
      
        if self.model is not None:
            self.unload_model()

        self.model = Model(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=self.gpu_layers,
            n_ctx=self.max_context_tokens,
            **self.device_options,
            temp=self.temperature,
            use_mmap=True,
        )
        self.stop_emit = False
        logger.info(f"Modelo {model_path} cargado con éxito")

    def unload_model(self):
        """Descargar modelo y liberar memoria"""
        self.model = None
        # Liberar memoria
        gc.collect()

    def set_tools(self, tools: bool):
        """Configurar el uso de herramientas """
        self.tools = tools
        
        # Actualizar el tools_manager
        try:
            from app.core.tools_manager import tools_manager
            tools_manager.set_tools_enabled(tools)
        except ImportError:
            pass
            
        logger.info(f"Tools configured: {tools}")
        print(f"🔧 DEBUG: Tools set to {tools}")

    def set_rag(self, rag: bool):
        """Configurar el uso de RAG """
        self.rag = rag
        logger.info(f"RAG configured: {rag}")
        print(f"🔧 DEBUG: RAG set to {rag}")

    def add_user_input(self, user_input, socket):
        """Procesar entrada del usuario - acepta string o lista"""
        if not self.is_processing:
            if self.model is None:
                # Importar aquí para evitar dependencia circular
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_error_response(
                    socket, 
                    'Error: No hay un modelo cargado. Por favor, carga un modelo primero.'
                )
                return
            
            # Convertir user_input a formato lista si es necesario (como en legacy)
            if isinstance(user_input, str):
                # Si es string, crear un mensaje de usuario simple
                processed_input = [{"role": "user", "content": user_input}]
            elif isinstance(user_input, list):
                # Si ya es lista, usar directamente
                processed_input = user_input
            else:
                logger.error(f"Tipo de user_input no soportado: {type(user_input)}")
                return
                
            logger.info(f"DEBUG: Procesando user_input de tipo {type(user_input)}")
            print(f"🔥 DEBUG: Procesando user_input de tipo {type(user_input)}")
            
            self.emit_assistant_response_stream(processed_input, socket)
      
    def emit_assistant_response_stream(self, user_input: List[Dict], socket):
        """
        Obtiene la respuesta del asistente

        Parámetros:
        - user_input: Lista de mensajes del chat
        - socket: Conexión para enviar el stream
        """
        # Importar aquí para evitar dependencia circular
        from app.core.socket_handler import SocketResponseHandler
        from app.core.agents.agent_registry import agent_registry
        from app.core.rag import Retriever
        
        logger.info(f"DEBUG: emit_assistant_response_stream INICIADO (tools={self.tools}, rag={self.rag})")

        if not self.is_processing:
            self.stop_emit = False
            self.is_processing = True
            response = ""
            tokensInput = str(user_input[-1]["content"]).encode()  # Convertir a bytes
            logger.debug(f"Tokens input: {tokensInput}")
            tokens = self.model.tokenize(tokensInput)  
            total_user_tokens = len(tokens)  # Contar los tokens de la entrada del usuario
            total_assistant_tokens = 0  # Inicializar el contador de tokens del asistente
            user_input_o = user_input           
            max_assistant_tokens = self.max_assistant_tokens
            
            # Enviar tokens del usuario al inicio del stream
            if not self.tools and not self.rag:
                SocketResponseHandler.emit_streaming_response(
                    socket,
                    '',  # Sin contenido aún
                    user_tokens=total_user_tokens,  # Solo tokens del usuario
                    finished=False
                )
                
            try:
                # Si hay herramientas, usar el sistema de agentes
                if self.tools:
                    logger.info("Using tools with agent system")
                    
                    # Usar el agente actual del registro (seleccionado por el usuario)
                    selected_agent = agent_registry.get_current_agent()
                    logger.info(f"Usando agente seleccionado: {selected_agent}")
                    
                    # Crear y ejecutar el agente
                    agent_instance = agent_registry.create_agent(
                        selected_agent,
                        user_input_o, 
                        prompt=user_input, 
                        response="", 
                        model=self.model, 
                        socket=socket, 
                        assistant=self
                    )
                    
                    return 
                
                # Si RAG está habilitado, ir directamente al retriever sin respuesta normal
                if self.rag: 
                    logger.info("Using RAG retriever")
                    print("🔍 Iniciando RAG retriever (RAG exclusivamente - sin respuesta del modelo base)...")
                    # Nos aseguramos de que este sea el único flujo de respuesta cuando RAG está activo
                    Retriever(self.model, user_input, socket)
                    return  # Salir temprano, Retriever se encarga de todo
                  
                # Solo procesar normalmente si no hay herramientas ni RAG
                response, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                    model=self.model,
                    messages=user_input,
                    socket=socket,
                    max_tokens=max_assistant_tokens,
                    user_tokens=total_user_tokens,
                    process_line_breaks=False,
                    response_queue=None,
                    link_remover_func=None,
                    stop_condition=lambda: self.stop_emit  # Condición de parada
                )
                
                # Enviar la señal de finalización para respuesta normal
                SocketResponseHandler.emit_finalization_signal(
                    socket,
                    total_user_tokens,
                    total_assistant_tokens
                )
                    
            except Exception as e:
                logger.error(f"Error in assistant response stream: {e}")
                SocketResponseHandler.emit_error_response(socket, f"Error: {str(e)}")
            finally:          
                self.is_processing = False
                # Liberar memoria
                gc.collect()
    
    def stop_response(self):
        """Detener la respuesta actual (idéntico al legacy)"""
        self.stop_emit = True
        logger.info("Stop signal activada")
        # Emitir señal de finalización inmediata
        try:
            # Si tenemos un socket activo, emitir señal de parada
            logger.info("Response stopping...")
        except Exception as e:
            logger.error(f"Error emitiendo señal de parada: {e}")
