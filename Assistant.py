
from llama_cpp import Llama 
import llama_cpp
import platform
import time

class Assistant:
    '''
        Instancia un asistente conversacional. 

        Parámetros:
        - (str) model_path: ruta al archivo .gguf del modelo.
        - (str) chat_format: formato de la plantilla del modelo.
    '''
    def __init__(self, default_model_path, default_chat_format):
        self.max_context_tokens = 2048
        self.max_assistant_tokens = 2048
        self.is_processing = False
        self.chat_format = default_chat_format
        self.model_path = default_model_path
        self.cuda_options = {"device": "cuda", "cuda_device_id": 0}
        self.metal_options = {"device": "metal", "metal_device_id": 0}
        self.gpu_layers = 14

        self.system_message = '''Eres un asistente en español con una personalidad amable y honesta. Como experto programador y pentester, debe examinar los detalles proporcionados para asegurarse de que sean utilizables. 
        Si no sabe la respuesta a una pregunta, no comparta información falsa. Mantenga sus respuestas en español y no se desvíe de la pregunta.
        '''
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
        else:
            raise RuntimeError("Sistema operativo no compatible")

        self.load_default_model()

    def load_default_model(self):
        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=self.gpu_layers,
            n_ctx=self.max_context_tokens,
            **self.device_options,
            chat_format=self.chat_format,
            temp=0.81,
            use_mmap=True,
            n_threads=11,
        )
        self.conversation_history = [{"role": "system", "content": self.system_message}]
        self.context_window_start = 0
        self.stop_emit = False

    def start_model(self, model_path, format, n_gpu_layer, new_system_message, context):
        '''
        Créa una instancia del modelo.

        Parámetros: 
        - (str) model_path: ruta al archivo gguf del modelo. 
        - (str) format: formato de la plantilla del chat. 
        - (int) n_gpu_layer: numero de capas enviadas a la GPU.
        - (str) new_system_message: mensaje de sistema inicial. 
        - (int) context: tamaño en tokens del contexto máximo. 
        '''
        message = new_system_message if new_system_message is not None and new_system_message != '' else self.system_message
        gpu_layers = n_gpu_layer if n_gpu_layer is not None else -1
        ctx = context if context is not None and context != '' else self.max_context_tokens

        self.system_message = message
        self.model_path = model_path
        self.max_context_tokens = ctx
        self.max_assistant_tokens = ctx
        self.chat_format = format
        self.gpu_layers = gpu_layers
        self.conversation_history = [{"role": "system", "content": self.system_message}]
        self.context_window_start = 0
        self.stop_emit = False
   
        if hasattr(self, 'llm'):
            # Si ya hay un modelo cargado, elimina la referencia
            del self.llm

        self.load_default_model()

    def unload_model(self):
        '''
        Elimina la referencia al modelo vaciando el atributo llm del asistente, liberándolo de memoria
        '''
        del self.llm

    def get_context_fraction(self):
        """
        Calcula la fracción de tokens de contexto utilizados.

        Retorna:
        float: Fracción de tokens de contexto utilizados.
        """
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        return min(1.0, total_tokens / self.max_context_tokens * 10)

    def update_context_tokens(self):
        '''
        Actualiza la ventana de contexto con un numero de mensajes inferior al contexto total.
        '''
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        while total_tokens > self.max_context_tokens:
            removed_message = self.conversation_history.pop(0)
            total_tokens -= len(removed_message["content"].split())
            self.context_window_start += 1
        print("TOKENS: "+ str(total_tokens))

    def add_user_input(self, user_input):
        '''
        Añade el input del usuario al historial de conversación. 
        Parámetros: 
        - (str) user_input: input del usuario.
        '''
        embeddings = llama_cpp.llama_get_embeddings(user_input)
        self.conversation_history.append({"role": "user", "content": user_input, "embeddings": embeddings})
        self.update_context_tokens()

    def get_assistant_response_stream(self, message_queue):
        """
        Obtiene la respuesta del asistente.

        Parámetros:
        - (str[]) message_queue: Cola de mensajes para comunicarse con otros componentes.
        """
        if not self.is_processing:
            last_user_input_time = time.time()
            response = ""
            message_queue.put({"role": "assistant", "content": "\n\n Asistente: \b"})
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history[self.context_window_start:], max_tokens=self.max_assistant_tokens, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    response += response_chunk
                    message_queue.put({"role": "assistant", "content": response_chunk})
            self.is_processing = False
            elapsed_time = round(time.time() - last_user_input_time, 2)
            print(f" | {elapsed_time}s")
            print(response)    

    def emit_assistant_response_stream(self, socketio):
        """
        Obtiene la respuesta del asistente.

        Parámetros:
        - (obj) socketio: Conexion para comunicarse con la plantilla y enviar el stream.
        """
        if not self.is_processing:
            self.stop_emit = False
            self.is_processing = True
            full_response = ""
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history,
                                                        max_tokens=self.max_assistant_tokens, 
                                                        stream=True):
                
                if 'content' in chunk['choices'][0]['delta'] and self.stop_emit is False:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    full_response += response_chunk  # Acumular la respuesta
                    socketio.emit('assistant_response',
                                  {'role': 'assistant', 'content': response_chunk}, namespace='/test')
                    time.sleep(0.01)
            if self.stop_emit is False:
                self.conversation_history.append({"role": "assistant", "content": full_response})
            print(full_response)
        self.is_processing = False



    def clear_context(self):
        '''
            Limpia el historial de conversación.
        '''
        self.conversation_history = [{"role": "system", "content": self.system_message}]
        self.context_window_start = 0
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history:
            print(mensaje)

    def stop_response(self):
        '''
            Stop response stream
        '''
        self.stop_emit = True
    


