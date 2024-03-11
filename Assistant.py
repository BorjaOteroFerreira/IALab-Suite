'''
@author: Borja Otero Ferreira
'''
from llama_cpp import Llama as Model
import platform
import time
import ollama

class Assistant:

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
        self.default_system_message = '''
You are an assistant with a kind and honest personality. 
As an expert programmer and pentester, 
you should examine the details provided to ensure that they are usable.
If you don't know the answer to a question, don't share false information and don't stray from the question.
your responses allways in markdown.
'''
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
            self.use_nmap = True
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
        self.context_window_start = 0
        self.stop_emit = False

    def load_model(self, model_path, format, new_temperature, n_gpu_layer, new_system_message, context):


        message = new_system_message if isinstance(new_system_message, str) and new_system_message != '' else self.default_system_message
        gpu_layers = int(n_gpu_layer) if isinstance(n_gpu_layer, int) else self.gpu_layers
        ctx = context if isinstance(context, int)  else self.max_context_tokens
        temperature = new_temperature if isinstance(new_temperature, float) else self.temperature
        self.system_message = message
        self.model_path = model_path
        self.temperature = temperature
        self.max_context_tokens = ctx
        self.max_assistant_tokens = self.max_assistant_tokens #TODO: change in interface
        self.chat_format = format
        self.gpu_layers = gpu_layers
        self.stop_emit = False

        self.load_default_model()

    def unload_model(self):
        self.model = None



    def add_user_input(self, user_input,socket):
        if not self.is_processing:
            self.emit_assistant_response_stream(user_input,socket)
  
         

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

    def emit_assistant_response_stream(self,user_input, socket):
        '''
        Obtiene la respuesta del asistente.

        Parámetros:
        - (obj) socket: Conexion para enviar el stream.
        '''
        if not self.is_processing:
            self.stop_emit = False
            self.is_processing = True
            response = ""
            tokensInput = str(user_input[-1]["content"]).encode()  # Convertir a bytes
            print(tokensInput)
            tokens = self.model.tokenize(tokensInput)  

            total_user_tokens = len(tokens)  # Contar los tokens de la entrada del usuario
            total_assistant_tokens = 0  # Inicializar el contador de tokens del asistente
            try:
                for chunk in self.model.create_chat_completion(messages=user_input, max_tokens=self.max_assistant_tokens, stream=True):
                    if 'content' in chunk['choices'][0]['delta'] and not self.stop_emit:
                        response_chunk = chunk['choices'][0]['delta']['content']
                        response += response_chunk  
                        total_assistant_tokens+=1 # Contar los tokens en el chunk actual
                        socket.emit('assistant_response', {
                            'content': chunk,
                            'total_user_tokens': total_user_tokens,
                            'total_assistant_tokens': total_assistant_tokens
                        }, namespace='/test')
                        time.sleep(0.01)
            finally:
                self.is_processing = False

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
                for part in client.chat(model='Hax0r', messages=user_input, stream=True):
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

        