'''
@Author: Borja Otero Ferreira
'''
from flask import Flask, render_template, request,jsonify,json,Response
from flask_socketio import SocketIO
import os, signal
from Assistant import Assistant 
import logging

class IASuiteApi:
    def __init__(self):
        self.app = Flask(__name__, static_url_path='/static')
        self.socketio = SocketIO(self.app, async_mode='threading')
        self.logging_setup()
        self.default_model_path = "models/lm-studio/gemma-2b-it-q8_0.gguf"
        self.default_chat_format = "gemma"
        self.assistant = None
        self.setup_routes()

    def logging_setup(self):
        logging.basicConfig(filename='logs/flask_log.log', level=logging.ERROR)


    def setup_routes(self):
        self.app.before_request(self.before_first_request)
        self.app.route('/')(self.index)
        self.socketio.on_event('user_input', self.handle_user_input_route, namespace='/test')
        self.app.route('/actualizar_historial', methods=['POST'])(self.actualizar_historial)
        self.app.route('/eliminar_historial', methods=['DELETE'])(self.eliminar_historial)
        self.app.route('/recuperar_historial', methods=['GET'])(self.recuperar_historial)
        self.app.route('/user_input', methods=['POST'])(self.handle_user_input_route)
        self.app.route('/load_model', methods=['POST'])(self.load_model)
        self.app.route('/unload_model', methods=['POST'])(self.unload_model)
        self.app.route('/stop_response', methods=['POST'])(self.stop_response)
        self.app.route('/v1/chat/completions', methods=['POST'])(self.ollama)


    def ollama(self):
            request_data = request.json  # Obtener los datos JSON del cuerpo de la solicitud
            user_input = request_data.get('content')
            user_input.pop(0)  # Elimina el mensaje del sistema
            self.assistant.emit_ollama_response_stream(user_input,self.socketio)
            print(f'\n\nInput Usuario: {user_input}\n\n')
            return 'Response finished'



    def ollama(self):
        request_data = request.json  # Obtener los datos JSON del cuerpo de la solicitud
        user_input = request_data.get('content')
        user_input.pop(0)  # Elimina el mensaje del sistema
        self.assistant.emit_ollama_response_stream(user_input,self.socketio)
        print(f'\n\nInput Usuario: {user_input}\n\n')
        return 'Response finished'

    def before_first_request(self):
        if self.assistant is None:
            self.assistant = Assistant(
                default_model_path=self.default_model_path,
                default_chat_format=self.default_chat_format
            )


    def index(self):
        models_list = self.get_models_list("models")
        format_list = self.get_format_list()
        chat_list = self.get_chat_list()
        return render_template('index.html', models_list=models_list, format_list=format_list, chat_list=chat_list)




    def actualizar_historial(self):
        nombre_chat = request.json.get('nombre_chat')
        nombre_chat = nombre_chat.replace('/', '-')
        nombre_chat = nombre_chat.replace(':', '-')
        nombre_chat = nombre_chat.replace(' ', '_')
        print(nombre_chat)
        historial = request.json.get('historial')
        ruta_archivo = os.path.join('chats', f'{nombre_chat}.json')

        # Verificar si el archivo existe
        if not os.path.exists(ruta_archivo):
            # Si el archivo no existe, crear uno nuevo con el historial
            with open(ruta_archivo, 'w') as f:
                json.dump(historial, f, indent=4)
            return jsonify({'message': f'Historial {nombre_chat} creado exitosamente.'}), 201
        else:
            # Si el archivo ya existe, actualizar el historial
            with open(ruta_archivo, 'w') as f:
                json.dump(historial, f, indent=4)
            return jsonify({'message': f'Historial {nombre_chat} actualizado exitosamente.'}), 200

    def eliminar_historial(self):
        nombre_chat = request.args.get('nombre_chat')
        ruta_archivo = os.path.join('chats', f'{nombre_chat+'.json'}')
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            return jsonify({'message': f'Historial {nombre_chat} eliminado exitosamente.'}), 200
        else:
            return jsonify({'error': f'No se encontró el historial {nombre_chat}.'}), 404

    def recuperar_historial(self):
        nombre_chat = request.args.get('nombre_chat')
        ruta_archivo = os.path.join('chats', f'{nombre_chat}.json')
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r') as f:
                historial = json.load(f)
            return jsonify(historial), 200
        else:
            return jsonify({'error': f'No se encontró el historial {nombre_chat}.'}), 404



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
    
    def get_chat_list(self):
        nombres_archivos_json = []
        # Obtener la lista de archivos en el directorio
        archivos = os.listdir('chats')
        # Filtrar solo los archivos con extensión .json
        for archivo in archivos:
            if archivo.endswith('.json'):
                nombres_archivos_json.append(archivo.replace('.json', ' '))
        # Ordenar la lista en orden inverso
        nombres_archivos_json.sort(reverse=True)
        return nombres_archivos_json

    def stop_server(self):
        os.kill(os.getpid(), signal.SIGINT) 
        return 'Server shutting down...'