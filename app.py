from flask import Flask, render_template, request
from flask_socketio import SocketIO
from llama_cpp import Llama
import os
import platform
import time

app = Flask(__name__)
socketio = SocketIO(app)

class LlamaAssistant:
    MAX_CONTEXT_TOKENS = 2048
    MAX_ASSISTANT_TOKENS = 1024

    def __init__(self, model_path, chat_format):
        self.is_processing = False
        self.mensaje_sistema = '''Eres un asistente en español con una personalidad amable y honesta. Como experto en programación y pentesting, debe examinar los detalles proporcionados para asegurarse de que sean utilizables. 
        Si no sabe la respuesta a una pregunta, no comparta información falsa. Mantenga sus respuestas en español y no se desvíe de la pregunta.
        '''
        self.chat_format = chat_format
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
            n_gpu_layers=14,
            n_ctx=2048,
            **self.device_options,
            chat_format=self.chat_format,
            temp=0.81,
        )

        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0

    def start_model(self, model_path):
        self.model_path = model_path
        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=14,
            n_ctx=2048,
            **self.device_options,
            chat_format=self.chat_format,
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
        return min(1.0, total_tokens / self.MAX_CONTEXT_TOKENS * 7.5)

    def update_context_tokens(self):
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        while total_tokens > self.MAX_CONTEXT_TOKENS:
            removed_message = self.conversation_history.pop(0)
            total_tokens -= len(removed_message["content"].split())
            self.context_window_start += 1

    def add_user_input(self, user_input):
        socketio.emit('assistant_response', {'role': 'assistant', 'content': f"<label id='assistant'><strong>Yo:</strong></label> {user_input}"}, namespace='/test')
        self.update_context_tokens()
        self.conversation_history.append({"role": "user", "content": user_input})

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

    def emit_assistant_response_stream(self, socketio):
        if not self.is_processing:
            last_user_input_time = time.time()
            socketio.emit('assistant_response', {'role': 'assistant', 'content': "<br><br><label id='assistant'><strong>Asistente: </strong></label>"}, namespace='/test')
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history[self.context_window_start:], max_tokens=self.MAX_ASSISTANT_TOKENS, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    socketio.emit('assistant_response', {'role': 'assistant', 'content': response_chunk}, namespace='/test')
                    time.sleep(0.01)
            socketio.emit('assistant_response', {'role': 'assistant', 'content': "<hr>"}, namespace='/test')

        self.is_processing = False
        elapsed_time = round(time.time() - last_user_input_time, 2)
        print(f" | {elapsed_time}s")

    def clear_context(self):
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history:
            print(mensaje)
    
    def clear_chat_history(self):
        socketio.emit('clear_chat', namespace='/test')


model_path="models/llama-2-7b-chat.Q8_0.gguf"
chat_format="tb-uncensored" 
llama_assistant = None       
@app.before_request
def before_first_request():
    global llama_assistant
    if llama_assistant is None:
        llama_assistant = LlamaAssistant(model_path=model_path,chat_format=chat_format)




@app.route('/')
def index():
    models_list = get_models_list("models")
    return render_template('index.html', models_list=models_list)

@socketio.on('user_input', namespace='/test')
def handle_user_input(data):
    user_input = data['content']
    llama_assistant.add_user_input(user_input)
    llama_assistant.emit_assistant_response_stream(socketio)

@app.route('/start_model', methods=['POST'])
def start_model():
    selected_model = request.form.get('model_path')
    llama_assistant.unload_model()
    llama_assistant.clear_context()
    llama_assistant.start_model(selected_model)
    socketio.emit('clear_chat', namespace='/test')  # Agrega este evento para limpiar el historial en el cliente
    return 'Modelo iniciado: ' + selected_model

@app.route('/unload_model', methods=['POST'])
def unload_model():
    llama_assistant.unload_model()
    llama_assistant.clear_context()
    return 'Modelo desinstalado'


def get_models_list(folder_path):
    models_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".gguf"):
                model_path = os.path.join(root, file)
                models_list.append(model_path)
    return models_list

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
