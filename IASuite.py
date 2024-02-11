from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
from Assistant import Assistant  # Importa tu clase Assistant desde el módulo Assistant
import logging

class IASuiteApi:
    def __init__(self):
        self.app = Flask(__name__, static_url_path='/static')
        self.socketio = SocketIO(self.app)
        self.logging_setup()
        self.default_model_path = "models/llama/llama-2-7b-chat.Q8_0.gguf"
        self.default_chat_format = "llama-2"
        self.assistant = None
        self.setup_routes()

    def logging_setup(self):
        logging.basicConfig(filename='flask_log.log', level=logging.INFO)

    def setup_routes(self):
        self.app.before_request(self.before_first_request)
        self.app.route('/')(self.index)
        self.socketio.on_event('user_input', self.handle_user_input_route, namespace='/test')
        self.app.route('/user_input', methods=['POST'])(self.handle_user_input_route)
        self.app.route('/load_model', methods=['POST'])(self.load_model)
        self.app.route('/unload_model', methods=['POST'])(self.unload_model)
        self.app.route('/clear_context', methods=['POST'])(self.clear_context)
        self.app.route('/stop_response', methods=['POST'])(self.stop_response)

    def before_first_request(self):
        if self.assistant is None:
            self.assistant = Assistant(
                default_model_path=self.default_model_path,
                default_chat_format=self.default_chat_format
            )

    def index(self):
        models_list = self.get_models_list("models")
        format_list = self.get_format_list()
        return render_template('index.html', models_list=models_list, format_list=format_list)

    def handle_user_input_route(self):
        user_input = request.form.get('content')
        print("Usuario dijo:", user_input)
        self.assistant.add_user_input(user_input)
        self.assistant.emit_assistant_response_stream(self.socketio)
        return 'Respuesta finalizada! 📩'

    def load_model(self):
        selected_model = request.form.get('model_path')
        selected_format = request.form.get('format')
        n_gpu_layers = request.form.get('n_gpu_layers')
        system_message = request.form.get('system_message')
        temperature = request.form.get('temperature')
        n_ctx = int(request.form.get('context')) if request.form.get('context') != '' else 2048
        self.assistant.unload_model()
        self.assistant.clear_context()
        self.assistant.load_model(selected_model, selected_format, temperature, n_gpu_layers, system_message, n_ctx)
        return 'Modelo iniciado:\n ' + selected_model

    def unload_model(self):
        self.assistant.unload_model()
        self.assistant.clear_context()
        return 'Modelo desinstalado! '

    def clear_context(self):
        self.assistant.clear_context()
        return "Historial limpiado!"

    def stop_response(self):
        self.assistant.stop_response()
        return "Respuesta cancelada!"

    def get_models_list(self, folder_path):
        models_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".gguf"):
                    model_path = os.path.join(root, file)
                    models_list.append(model_path)
        return models_list

    def get_format_list(self):
        format_list = ["guanaco", "llama-2", "tb-uncensored", "airoboros", "mistral-24", "qwen", "vicuna"]
        return format_list