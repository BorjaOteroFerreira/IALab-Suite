import time
import platform
from llama_cpp import Llama

class LlamaAssistant:

    MAX_CONTEXT_TOKENS = 2048
    MAX_ASSISTANT_TOKENS = 1024

    def __init__(self, model_path,chat_format):
        """
        Inicializa el asistente Llama.

        Parámetros:
        - model_path (str): Ruta al modelo Llama.
        """
        self.is_processing = False
        self.mensaje_sistema = '''Eres un asistente con una personalidad amable y honesta. Como experto programador, debe examinar los detalles proporcionados para asegurarse de que sean utilizables. 
        Si no sabe la respuesta a una pregunta, no compartas información falsa. Manten tus respuestas en español y no te desvíes de la pregunta.
        '''
        self.chat_format=chat_format
        self.model_path = model_path
        self.cuda_options = {
            "device": "cuda",
            "cuda_device_id": 0,
        }
        self.metal_options = {
            "device": "metal",
            "metal_device_id": 0,
        }

        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
        else:
            raise RuntimeError("Sistema operativo no compatible")

        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=1,
            n_ctx=4096,
            **self.device_options,
            chat_format=self.chat_format,
            temp=0.81,
        )
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0  # Iniciamos desde el mensaje del sistema en la ventana de contexto móvil

    def count_tokens(self, text):
        """
        Cuenta los tokens en el texto dado utilizando la lógica interna de Llama.
        """
        tokens = self.llm.tokenize(self,text)
        print(tokens)
        return len(tokens)

    def add_user_input(self, user_input):
        """
        Agrega la entrada del usuario al historial de conversación.

        Parámetros:
        - user_input (str): Entrada del usuario.
        """
        
        self.update_context_tokens()
        self.conversation_history.append({"role": "user", "content": user_input})
        

    def get_context_fraction(self):
        """
        Calcula la fracción de tokens de contexto utilizados.

        Retorna:
        float: Fracción de tokens de contexto utilizados.
        """
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        return min(1.0, total_tokens / self.MAX_CONTEXT_TOKENS * 7.5)

    def update_context_tokens(self):
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        while total_tokens > self.MAX_CONTEXT_TOKENS:
            removed_message = self.conversation_history.pop(0)
            total_tokens -= len(removed_message["content"].split())
            self.context_window_start += 1
    
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
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history[self.context_window_start:], max_tokens=self.MAX_ASSISTANT_TOKENS, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    response += response_chunk
                    message_queue.put({"role": "assistant", "content": response_chunk})
                    
            self.is_processing = False
            elapsed_time = round(time.time() - last_user_input_time, 2)
            print(f" | {elapsed_time}s")
            print(response)

    def get_assistant_response(self):
        last_user_input_time = time.time()

        # Realizar la inferencia
        output = self.llm.create_chat_completion(messages=self.conversation_history, max_tokens=4096)
        print(output)
        # Obtener la primera respuesta generada por el modelo
        response = output['choices'][0]['message']['content']
        # Eliminar "### RESPONSE:" de la respuesta
        #response = response.replace("### RESPONSE:", "")
        # Añadir la respuesta al historial de la conversación
        self.conversation_history.append({"role": "assistant", "content": response})
        elapsed_time = round(time.time() - last_user_input_time, 2)
        response += " | " + str(elapsed_time) + "s"
        return response

    def clear_context(self):
        """
        Limpia el historial de conversación.
        """
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history:
            print(mensaje)

# Ejemplo de uso:
# llama_assistant = LlamaAssistant("ruta/al/modelo","chat_format="formato_chat")
# llama_assistant.add_user_input("Hola, ¿cómo estás?")
# llama_assistant.get_assistant_response(message_queue)
# llama_assistant.clear_context()
