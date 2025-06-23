'''
@author: Borja Otero Ferreira
'''
import copy
from llama_cpp import Llama as Model
import platform
import time
import ollama
from Cortex import Cortex
from Rag import Retriever
from SocketResponseHandler import SocketResponseHandler

class Assistant:
    
    def __init__(self, default_model_path, default_chat_format):
        # Estado del modelo
        self.model = None
        self.model_path = default_model_path
        self.chat_format = default_chat_format
        self.temperature = 0.3
        self.max_context_tokens = 12000
        self.max_assistant_tokens = 2048
        self.gpu_layers = -1
        self.is_processing = False
        self.stop_emit = False
        self.tools = False
        self.rag = False
        self.default_system_message = '''
Eres un asistente con una personalidad amable y honesta.
Como programador experto y pentester,
debes examinar los detalles proporcionados para asegurarte de que sean utilizables.
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
        
        print("🤖 Assistant inicializado (modelo no cargado - usar load_model() para cargar)")
    
    def load_model(self, model_path, format, new_temperature, n_gpu_layer, new_system_message, context, max_response_tokens):
        """Carga un modelo específico con configuración personalizada"""
        # Validar y establecer parámetros
        self.model_path = model_path
        self.chat_format = format
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
        print(f"✅ Modelo {model_path} cargado con éxito")

    def unload_model(self):
        self.model = None
        # Liberar memoria
        import gc
        gc.collect()

    def set_tools(self,tools):
            self.tools = tools

    def set_rag(self,rag):
            self.rag = rag

    def add_user_input(self, user_input,socket):
        if not self.is_processing:
            if self.model is None:
                SocketResponseHandler.emit_error_response(
                    socket, 
                    'Error: No hay un modelo cargado. Por favor, carga un modelo primero.'
                )
                return
            self.emit_assistant_response_stream(user_input,socket)
      
    def emit_assistant_response_stream(self,user_input, socket):
        '''
        Obtiene la respuesta del asistente.

        Parámetros:
        - (obj) socket: Conexion para enviar el stream.
        '''
        print(f"🔥 DEBUG: emit_assistant_response_stream INICIADO (tools={self.tools}, rag={self.rag})")

        if not self.is_processing:
            self.stop_emit = False
            self.is_processing = True
            response = ""
            tokensInput = str(user_input[-1]["content"]).encode()  # Convertir a bytes
            print(tokensInput)
            tokens = self.model.tokenize(tokensInput)  
            total_user_tokens = len(tokens)  # Contar los tokens de la entrada del usuario
            total_assistant_tokens = 0  # Inicializar el contador de tokens del asistente
            user_input_o = user_input           
            max_assistant_tokens = self.max_assistant_tokens if not self.tools else 100
            # Enviar tokens del usuario al inicio del stream
            if not self.tools and not self.rag:
                SocketResponseHandler.emit_streaming_response(
                    socket,
                    '',  # Sin contenido aún
                    user_tokens=total_user_tokens,  # Solo tokens del usuario
                    finished=False                )
            try:                # Si hay herramientas, ir directamente a Cortex sin procesar aquí
                if self.tools:
                    Cortex(user_input_o, prompt=user_input, response="", model=self.model, socket=socket, assistant=self)
                    return  # Salir temprano, Cortex se encarga de todo
                  # Solo procesar normalmente si no hay herramientas usando el método unificado
                response, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                    model=self.model,
                    messages=user_input,
                    socket=socket,
                    max_tokens=max_assistant_tokens,
                    user_tokens=total_user_tokens if not self.rag else None,
                    process_line_breaks=False,
                    response_queue=None,
                    link_remover_func=None,
                    stop_condition=lambda: self.stop_emit  # Condición de parada
                )
                
                # Solo emitir en el contexto adecuado
                if not self.tools and not self.rag:
                    SocketResponseHandler.emit_finalization_signal(
                        socket,
                        total_user_tokens,
                        total_assistant_tokens
                    )
                
                if self.rag: 
                    Retriever(self.model,user_input,socket)
                # La llamada a Cortex ahora se hace al principio si hay herramientas
            finally:          
                self.is_processing = False
                # Liberar memoria
                import gc
                gc.collect()
    

    def stop_response(self):
        self.stop_emit = True
        print("🛑 Stop signal activada")
        # Emitir señal de finalización inmediata
        try:
            from SocketResponseHandler import SocketResponseHandler
            # Si tenemos un socket activo, emitir señal de parada
            # Nota: Necesitaríamos guardar la referencia del socket para esto
            print("🛑 Response stopping...")
        except Exception as e:
            print(f"Error emitiendo señal de parada: {e}")


