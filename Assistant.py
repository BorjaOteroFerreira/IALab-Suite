
from llama_cpp import Llama as Model
import llama_cpp
import platform
import time

class Assistant:
    '''
        Instancia un asistente conversacional. 

        Parámetros:
        - (str) default_model_path: ruta al archivo .gguf del modelo.
        - (str) default_chat_format: formato de la plantilla del modelo.
    '''
    def __init__(self, default_model_path, default_chat_format):
        self.model = None
        self.max_context_tokens = 2048
        self.max_assistant_tokens = 2048
        self.is_processing = False
        self.chat_format = default_chat_format
        self.model_path = default_model_path
        self.temperature = 0.81
        self.cuda_options = {"device": "cuda", "cuda_device_id": 0}
        self.metal_options = {"device": "metal", "metal_device_id": 0}
        self.gpu_layers = -1
        self.system_message = '''
You are an assistant with a kind and honest personality. 
As an expert programmer and pentester, 
you should examine the details provided to ensure that they are usable.
If you don't know the answer to a question, don't share false information and don't stray from the question.
your responses allways in markdown.
'''

        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
            self.use_nmap = False
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
            self.use_nmap = True
        else:
            raise RuntimeError("Sistema operativo no compatible")
        self.load_default_model()

    def load_default_model(self):
        self.model = Model(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=self.gpu_layers,
            n_ctx=self.max_context_tokens,
            **self.device_options,
            chat_format=self.chat_format,
            temp=self.temperature,
           

        )
        self.conversation_history = [{"role": "system", "content": self.system_message}]
        self.context_window_start = 0
        self.stop_emit = False

    def load_model(self, model_path, format, new_temperature, n_gpu_layer, new_system_message, context):
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
        gpu_layers = int(n_gpu_layer) if n_gpu_layer is not None and n_gpu_layer != '' else -1
        ctx = context if context is not None and context != '' else self.max_context_tokens
        temperature = new_temperature if new_temperature is not None else 0.81
        self.system_message = message
        self.model_path = model_path
        self.temperature = temperature
        self.max_context_tokens = ctx
        self.max_assistant_tokens = ctx
        self.chat_format = format
        self.gpu_layers = gpu_layers
        self.conversation_history = [{"role": "system", "content": self.system_message}]
        self.context_window_start = 0
        self.stop_emit = False
   
        if hasattr(self, 'model'):
             self.model = None

        self.load_default_model()

    def unload_model(self):
        '''
        Elimina la referencia al modelo vaciando el atributo model del asistente, liberándolo de memoria
        '''
        self.model = None

    def get_context_fraction(self):
        '''
        Calcula la fracción de tokens de contexto utilizados.

        Retorna:
        float: Fracción de tokens de contexto utilizados.
        '''
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
        '''
        Obtiene la respuesta del asistente.

        Parámetros:
        - (map[]) message_queue: Cola de mensajes para comunicarse con otros componentes como example_gui.py.
        '''
        if not self.is_processing:
            self.stop_emit = False
            response = ""
            for chunk in self.model.create_chat_completion(messages=self.conversation_history[self.context_window_start:], 
                                                           max_tokens=self.max_assistant_tokens, 
                                                           stream=True):
                          
                if 'content' in chunk['choices'][0]['delta'] and not self.stop_emit:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    response += response_chunk
                    message_queue.put({"role": "assistant", "content": response_chunk})

            if not self.stop_emit:
                self.conversation_history.append({"role": "assistant", "content": response})
                print(response)
            self.is_processing = False
 
    #TODO: stop token generation thread
    def emit_assistant_response_stream(self, socket):
        '''
        Obtiene la respuesta del asistente.

        Parámetros:
        - (obj) socket: Conexion para enviar el stream.
        '''
        if not self.is_processing:
            self.stop_emit = False
            self.is_processing = True
            response = ""
            for chunk in self.model.create_chat_completion(messages=self.conversation_history,
                                                        max_tokens=self.max_assistant_tokens, 
                                                        stream=True):
                
                if 'content' in chunk['choices'][0]['delta'] and not self.stop_emit:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    response += response_chunk  
                    socket.emit('assistant_response',
                                {'role': 'assistant', 'content': response_chunk}, namespace='/test')
                    time.sleep(0.01)
            if not self.stop_emit:
                self.conversation_history.append({"role": "assistant", "content": response})
                print(response)
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
            Detiene la generación de repspuesta en curso
        '''
        self.stop_emit = True
    


