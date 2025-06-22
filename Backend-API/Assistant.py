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
        self.model = None
        self.tools= False
        self.rag = False
        self.max_context_tokens = 12000
        self.max_assistant_tokens = 2048
        self.is_processing = False
        self.chat_format = default_chat_format
        self.model_path = default_model_path
        self.temperature = 0.3
        self.cuda_options = {"device": "cuda", "cuda_device_id": 0}
        self.metal_options = {"device": "metal", "metal_device_id": 0}
        self.gpu_layers = -1
        self.default_system_message = '''
Eres un asistente con una personalidad amable y honesta.
Como programador experto y pentester,
debes examinar los detalles proporcionados para asegurarte de que sean utilizables.
Si no sabes la respuesta a una pregunta, no compartas información falsa y no te desvíes de la pregunta.
'''
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
            self.use_nmap = True
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
            self.use_nmap = True
        else:
            raise RuntimeError("Sistema operativo no compatible")
        # No cargar modelo automáticamente - dejar que se cargue manualmente

    def load_default_model(self):
        if self.model is None:
            self.model = Model(
                model_path=self.model_path,
                verbose=True,
                n_gpu_layers=self.gpu_layers,
                n_ctx=self.max_context_tokens,
                **self.device_options,
                temp=self.temperature,
                use_mmap=True,
            )
        self.context_window_start = 0
        self.stop_emit = False

    def load_model(self, model_path, format, new_temperature, n_gpu_layer, new_system_message, context,max_response_tokens):
        gpu_layers = int(n_gpu_layer) if isinstance(n_gpu_layer, int) else self.gpu_layers
        ctx = context if isinstance(context, int)  else self.max_context_tokens
        temperature = new_temperature if isinstance(new_temperature, float) else self.temperature
        self.default_system_message = new_system_message
        max_asistant_tokens = max_response_tokens if isinstance(max_response_tokens,int) else self.max_assistant_tokens
        self.model_path = model_path
        self.temperature = temperature
        self.max_context_tokens = ctx
        self.max_assistant_tokens = max_asistant_tokens #TODO: change in interface
        self.gpu_layers = gpu_layers
        self.stop_emit = False
        self.load_default_model()

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
            try:
                # Si hay herramientas, ir directamente a Cortex sin procesar aquí
                if self.tools:
                    Cortex(user_input_o, prompt=user_input, response="", model=self.model, socket=socket)
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
    def emit_ollama_response_stream(self,user_input, socket):
            '''
            Obtiene la respuesta del asistente.

            Parámetros:
            - (obj) socket: Conexion para enviar el stream.
            '''
            client = ollama
            total_user_tokens = 0
            if not self.is_processing:
                self.stop_emit = False
                self.is_processing = True
                full_response = ""
                if(self.model is not None):
                    tokensInput = str(user_input[-1]["content"]).encode()  # Convertir a bytes
                    print(tokensInput)
                    tokens = self.model.tokenize(tokensInput)  
                    total_user_tokens = len(tokens)  # Contar los tokens de la entrada del usuario
                    print(total_user_tokens)
                total_assistant_tokens = 0  # Inicializar el contador de tokens del asistente
                try:
                    for part in client.chat(model='gemma', messages=user_input, stream=True):
                            chunk = part['message']['content']
                            for char in chunk:
                                full_response += char
                                total_assistant_tokens+=1 # Contar los tokens en el chunk actual
                                print(char, end='', flush=True)
                            socket.emit('assistant_response', {
                                'content': chunk,
                                'total_user_tokens': total_user_tokens,
                                'total_assistant_tokens': total_assistant_tokens
                            }, namespace='/test')
                            time.sleep(0.01)
                finally:
                    self.is_processing = False

    def stop_response(self):
        self.stop_emit = True


