'''
@Author: Borja Otero Ferreira
'''
from flask import Flask, render_template, request,jsonify,json
from flask_socketio import SocketIO
import os, signal
from Assistant import Assistant 
import logging

class IASuiteApi:
    def __init__(self):
        self.app = Flask(__name__, static_url_path='/static')
        self.socketio = SocketIO(self.app, async_mode='threading')
        self.logging_setup()
        self.default_model_path = "models/Google/gemma-2b-it-q8_0.gguf"
        self.default_chat_format = "gemma"
        self.assistant = None
        self.setup_routes()

    def logging_setup(self):
        logging.basicConfig(filename='flask_log.log', level=logging.ERROR)


    def setup_routes(self):
        self.app.before_request(self.before_first_request)
        self.app.route('/')(self.index)
        self.socketio.on_event('user_input', self.handle_user_input_route, namespace='/test')
        self.app.route('/user_input', methods=['POST'])(self.handle_user_input_route)
        self.app.route('/load_model', methods=['POST'])(self.load_model)
        self.app.route('/unload_model', methods=['POST'])(self.unload_model)
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
        request_data = request.json  # Obtener los datos JSON del cuerpo de la solicitud
        chat_history = request_data.get('content')
        print("Usuario dijo:", chat_history)
        self.assistant.add_user_input(chat_history,self.socketio)
        return 'Response finished! 📩'

    def load_model(self):
        selected_model = request.form.get('model_path')
        selected_format = request.form.get('format')
        n_gpu_layers = int(request.form.get('gpu_layers')) if request.form.get('gpu_layers') != '' else -1
        system_message = request.form.get('system_message')
        temperature = float(request.form.get('temperature')) if request.form.get('temperature') != '' else 0.81
        n_ctx = int(request.form.get('context')) if request.form.get('context') != '' else 2048
        self.assistant.unload_model()
        self.assistant.load_model(selected_model,selected_format,temperature,n_gpu_layers,system_message,n_ctx)
        return f'''
                \nModel:{selected_model}
                \nformat: {selected_format}
                \ntemp: {temperature}
                \nlayers: {n_gpu_layers}
                \nSM: {system_message}
                \nctx: {n_ctx}
                '''

    def unload_model(self):
        self.assistant.unload_model()
        return 'Model uninstalled 🫗!'


    def stop_response(self):
        self.assistant.stop_response()
        return "Finishing response...\nPlease wait ⏳"

    def get_models_list(self, folder_path):
        models_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".gguf"):
                    model_path = os.path.join(root, file)
                    models_list.append(model_path)
        return models_list

    def get_format_list(self):
        format_list = [ "llama-2",
                        "Custom-IALab",
                        "functionary",
                        "airoboros",
                        "guanaco",
                        "mistral-24",
                        "gemma",
                        "saiga",
                        "openchat",
                        "chatglm3",
                        "mistral-instruct",
                        "chatml",
                        "pygmalion",
                        "zephyr",
                        "mistrallite",
                        "open-orca",
                        "intel",
                        "phind",
                        "snoozy",
                        "redpajama-incite",
                        "openbuddy",
                        "baichuan",
                        "vicuna",
                        "qwen",
                        "baichuan-2",
                        "oasst_llama",
                        "rarete"]
        return format_list
    
    def stop_server(self):
        os.kill(os.getpid(), signal.SIGINT) 
        return 'Server shutting down...'