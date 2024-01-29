
from llama_cpp import Llama 
import platform
import time

class LlamaAssistant:

    def __init__(self, model_path, chat_format):
        self.max_context_tokens = 5000
        self.max_assistant_tokens = 2048
        self.is_processing = False
        self.chat_format = chat_format
        self.model_path = model_path
        self.cuda_options = {"device": "cuda", "cuda_device_id": 0}
        self.metal_options = {"device": "metal","metal_device_id": 0}
        self.mensaje_sistema = '''Eres un asistente en español con una personalidad amable y honesta. Como experto en programación y pentesting, debe examinar los detalles proporcionados para asegurarse de que sean utilizables. 
        Si no sabe la respuesta a una pregunta, no comparta información falsa. Mantenga sus respuestas en español y no se desvíe de la pregunta.
        '''
        
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
        else:
            raise RuntimeError("Sistema operativo no compatible")

        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=14,
            n_ctx=self.max_context_tokens,
            **self.device_options,
            chat_format=self.chat_format,
            temp=0.81,
        )
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0

    def start_model(self, model_path, format):
        self.model_path = model_path
        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=14,
            n_ctx=self.max_context_tokens,
            **self.device_options,
            chat_format=format,
            temp=0.81,
        )

    def unload_model(self):
        self.llm = None

    def get_context_fraction(self):
        """
        Calcula la fracción de tokens de contexto utilizados.

        Retorna:
        float: Fracción de tokens de contexto utilizados.
        """
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        return min(1.0, total_tokens / self.max_context_tokens * 7.5)

    def update_context_tokens(self):
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        while total_tokens > self.max_context_tokens:
            removed_message = self.conversation_history.pop(0)
            total_tokens -= len(removed_message["content"].split())
            self.context_window_start += 1
        print("TOKENS: "+str(total_tokens))

    def add_user_input(self, user_input,socketio):
        socketio.emit('assistant_response', {'role': 'assistant', 'content': f"<label id='assistant'><strong>Yo:</strong></label> {user_input}"}, namespace='/test')
        self.conversation_history.append({"role": "user", "content": user_input})
        self.update_context_tokens()
      
    def get_assistant_response_stream(self, message_queue):
        """
        Obtiene la respuesta del asistente.

        Parámetros:
        - message_queue: Cola de mensajes para comunicarse con otros componentes.
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
        if not self.is_processing:
            full_response = ""
            last_user_input_time = time.time()
            socketio.emit('assistant_response', 
                          {'role': 'assistant', 'content': "<br><br><div class='chat-bubble'><label id='assistant'><strong>Asistente: </strong></label>"},
                            namespace='/test')
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history,
                                                        max_tokens=self.max_assistant_tokens, 
                                                        stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    full_response += response_chunk  # Acumular la respuesta
                    socketio.emit('assistant_response',
                                  {'role': 'assistant', 'content': response_chunk},
                                    namespace='/test')
                    time.sleep(0.01)
            socketio.emit(
                'assistant_response',
                {'role': 'assistant','content': "</div><hr>"},
                namespace='/test')
            self.conversation_history.append({"role": "assistant", "content": full_response})
        self.is_processing = False
        elapsed_time = round(time.time() - last_user_input_time, 2)
        print(f" | {elapsed_time}s")

    def clear_context(self):
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history:
            print(mensaje)
   
