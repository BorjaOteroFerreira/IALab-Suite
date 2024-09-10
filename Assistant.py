'''
@author: Borja Otero Ferreira
'''
import copy
from llama_cpp import Llama as Model
import platform
import time
import ollama
from cortex import Cortex
from ragai2 import Rag
class Assistant:

    def __init__(self, default_model_path, default_chat_format):
        self.model = None
        self.tools= False
        self.rag = False
        self.max_context_tokens = 14000
        self.max_assistant_tokens =2048
        self.is_processing = False
        self.chat_format = default_chat_format
        self.model_path = default_model_path
        self.temperature = 0.81
        self.cuda_options = {"device": "cuda", "cuda_device_id": 0}
        self.metal_options = {"device": "metal", "metal_device_id": 0}
        self.gpu_layers = -1
        self.default_system_message = '''
Eres un asistente con una personalidad amable y honesta.
Como programador experto y pentester,
debe examinar los detalles proporcionados para asegurarse de que sean utilizables.
Si no sabe la respuesta a una pregunta, no comparta información falsa y no se desvíe de la pregunta.
sus respuestas siempre en rebajas.
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
        self.chat_format = format
        self.gpu_layers = gpu_layers
        self.stop_emit = False
        self.load_default_model()

    def unload_model(self):
        self.model = None

    def set_tools(self,tools):
            self.tools = tools

    def set_rag(self,rag):
            self.rag = rag

    def add_user_input(self, user_input,socket):
        if not self.is_processing:
            self.emit_assistant_response_stream(user_input,socket)
  
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
            user_input_o = user_input
            max_assistant_tokens = self.max_assistant_tokens if not self.tools else 100
            try:
                if self.tools :
                    user_input = self._instruccionesAdicionales(user_input)
                for chunk in self.model.create_chat_completion(messages=user_input, max_tokens=self.max_assistant_tokens, stream=True):
                    if 'content' in chunk['choices'][0]['delta'] and not self.stop_emit:
                        response_chunk = chunk['choices'][0]['delta']['content']
                        response += response_chunk  
                        total_assistant_tokens+=1 # Contar los tokens en el chunk actual
                        if not self.tools and not self.rag: 
                            socket.emit('assistant_response', {
                                'content': chunk,
                                'total_user_tokens': total_user_tokens,
                                'total_assistant_tokens': total_assistant_tokens
                            }, namespace='/test')
                            time.sleep(0.01)

                if self.rag: 
                    Rag(self.model,user_input,socket)
                if self.tools:
                    Cortex(user_input_o, prompt=user_input, response=response, model=self.model,socket=socket )
            finally:          
                self.is_processing = False


    def _instruccionesAdicionales(self, prompt):
            # Copia el historial de mensajes
            prompt_copia = copy.deepcopy(prompt)        
            # Modifica el primer mensaje del sistema
            nuevo_mensaje_sistema =  f"""
    TU PRINCIPAL OBJETIVO ES DETERMINAR QUE HERRAMIENTA NECESITAS
    Funciones disponibles: 
    [Funcion: 'buscar_en_internet' , query: 'url_o_consulta' ]
    [Funcion: 'video_search_tool' , query: 'consulta']
    responde unicamente con la o las herramientas a lanzar, ejemplo: 
    supongamos que necesitas buscar el tiempo en internet , contestas: 
    [Funcion: 'buscar_en_internet' , query: 'tiempo proximos dias' ]
    Asegurate de que utilizas la sintaxis correcta al colocar un corchete al inicio y otro al final.
    Puedes usar mas de una herramienta si lo necesitas.
    Debes contestar solo con las funciones que usarias sin texto antes ni despues
    SIEMPRE DEBES RESPONDER EN ESPAÑOL.
    """     
            if prompt_copia and prompt_copia[0]['role'] == 'system':
                prompt_copia[0]['content'] = nuevo_mensaje_sistema 
        
            #prompt_copia.append({"role": "system", "content": nuevo_mensaje_sistema})
        
    
            """for prompt in prompt_copia:
                print(json.dumps(prompt))
                pass
            """
            return prompt_copia
                    
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


