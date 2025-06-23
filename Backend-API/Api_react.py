'''
@Author: Borja Otero Ferreira
'''
from flask import Flask, render_template, request, jsonify, json, send_from_directory
from llama_cpp.llama_chat_format import LlamaChatCompletionHandlerRegistry
from flask_socketio import SocketIO
import os, signal, time
from Assistant import Assistant 
import logging

class IASuiteApi:
    def __init__(self):
        print("""
╭─────────────╮
│    IALab    │
├─^───────────┤
│             │
│   ███████   │
│  ██─────██  │
│  ██ o o ██  │
│  ██  ^  ██  │
│  █████████  │
│             │
╰─┬───────────╯
  │
  └─╼═╼═╼═╼═╼═╼[|= | Cogito, ergo svm |
   
              """)
        self.app = Flask(__name__, static_url_path='', static_folder='frontend/build', template_folder='templates')
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        self.socketio = SocketIO(self.app, async_mode='threading', cors_allowed_origins="*", max_size=1024*1024)
        self.logging_setup()
        self.default_model_path = "Z:/Modelos LM Studio/lmstudio-community/gemma-3-12b-it-GGUF/gemma-3-12b-it-Q4_K_M.gguf"
        self.default_chat_format = "chatml"
        self.assistant = None
        self.setup_routes()

    def logging_setup(self):
        logging.basicConfig(filename='logs/flask_log.log', level=logging.ERROR)    
    def setup_routes(self):
        self.app.before_request(self.before_first_request)        
        # Ruta raíz para mostrar index vacío de templates
        self.app.route('/')(self.serve_empty_index)
        # Ruta específica para archivos de fuentes
        self.app.route('/fonts/<path:filename>')(self.serve_fonts)
        # API REST endpoints
        self.app.route('/api/models-and-formats', methods=['GET'])(self.get_models_and_formats)
        self.socketio.on_event('user_input', self.handle_user_input_route, namespace='/test')
        self.app.route('/actualizar_historial', methods=['POST'])(self.actualizar_historial)
        self.app.route('/eliminar_historial', methods=['DELETE'])(self.eliminar_historial)
        self.app.route('/recuperar_historial', methods=['GET'])(self.recuperar_historial)
        self.app.route('/user_input', methods=['POST'])(self.handle_user_input_route)
        self.app.route('/load_model', methods=['POST'])(self.load_model)
        self.app.route('/unload_model', methods=['POST'])(self.unload_model)
        self.app.route('/stop_response', methods=['POST'])(self.stop_response)        
        self.app.route('/v1/chat/completions', methods=['POST'])(self.ollama)
        self.app.route('/.well-known/acme-challenge/<challenge>')(self.letsencrypt_challenge)
        self.app.route('/playground')(self.playground)

    
    def serve_fonts(self, filename):
        """Sirve archivos de fuentes"""
        try:
            # Intentar desde el directorio build/fonts
            build_fonts_path = os.path.join('frontend/build/fonts', filename)
            if os.path.exists(build_fonts_path):
                return send_from_directory('frontend/build/fonts', filename)
            
            # Fallback al directorio public/fonts
            public_fonts_path = os.path.join('frontend/public/fonts', filename)
            if os.path.exists(public_fonts_path):
                return send_from_directory('frontend/public/fonts', filename)
            
            return "Font not found", 404
        except Exception as e:
            print(f"Error sirviendo fuente {filename}: {e}")
            return "Font error", 500

    def serve_empty_index(self):
        """Sirve el index vacío de templates para la ruta raíz"""
        try:
            return render_template('index.html')
        except Exception as e:
            print(f"Error sirviendo index vacío: {e}")
            return "Error interno", 500
            
    def get_models_and_formats(self):
        models_list = self.get_models_list("Z:/Modelos LM Studio/")
        format_list = self.get_format_list()
        return jsonify({
            'models': models_list,
            'formats': format_list
        })

    def playground(self):
        models_list = self.get_models_list("Z:/Modelos LM Studio/")
        format_list = self.get_format_list()
        chat_list = self.get_chat_list()
        return render_template('playground.html', models_list=models_list, format_list=format_list, chat_list=chat_list)

    def letsencrypt_challenge(self, challenge):
        return send_from_directory('.well-known/acme-challenge', challenge)
                                   
    def ollama(self):
        request_data = request.json
        user_input = request_data.get('content')
        user_input.pop(0)  # Elimina el mensaje del sistema
        self.assistant.emit_ollama_response_stream(user_input,self.socketio)
        print(f'\n\nInput Usuario: {user_input}\n\n')
        return 'Response finished'

    def before_first_request(self):
        # Inicializar el asistente 
        if self.assistant is None:
            self.assistant = Assistant()
            print("🤖 Asistente inicializado")

    def actualizar_historial(self):
        nombre_chat = request.json.get('nombre_chat')
        nombre_chat = nombre_chat.replace('/', '-')
        nombre_chat = nombre_chat.replace(':', '-')
        nombre_chat = nombre_chat.replace(' ', '_')
        nombre_chat = nombre_chat.replace('?', '')
        historial = request.json.get('historial')
        ruta_archivo = os.path.join('chats', f'{nombre_chat}.json')

        if not os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'w') as f:
                json.dump(historial, f, indent=4)
            return jsonify({'message': f'Historial {nombre_chat} creado exitosamente.'}), 201
        else:
            with open(ruta_archivo, 'w') as f:
                json.dump(historial, f, indent=4)
            return jsonify({'message': f'Historial {nombre_chat} actualizado exitosamente.'}), 200

    def eliminar_historial(self):
        nombre_chat = request.args.get('nombre_chat')
        ruta_archivo = os.path.join('chats', f'{nombre_chat}.json')
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            return jsonify({'message': f'Historial {nombre_chat} eliminado exitosamente.'}), 200
        else:
            return jsonify({'error': f'No se encontró el historial {nombre_chat}.'}), 404

    def recuperar_historial(self):
        nombre_chat = request.args.get('nombre_chat')
        
        if not nombre_chat:
            return jsonify(self.get_chat_list()), 200
            
        ruta_archivo = os.path.join('chats', f'{nombre_chat}.json')
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r') as f:
                historial = json.load(f)
            return jsonify(historial), 200
        else:
            return jsonify({'error': f'No se encontró el historial {nombre_chat}.'}), 404

    def handle_user_input_route(self):
        request_data = request.json
        chat_history = request_data.get('content')
        tools = request_data.get("tools")
        rag = request_data.get("rag")
        self.assistant.set_tools(tools)
        self.assistant.set_rag(rag) 
        print("Usuario dijo:", chat_history)
        self.assistant.add_user_input(chat_history,self.socketio)
        return 'Response finished! 📩'

    def load_model(self):
        selected_model = request.form.get('model_path')
        n_gpu_layers = int(request.form.get('gpu_layers')) if request.form.get('gpu_layers') != '' else -1
        system_message = request.form.get('system_message')
        temperature = float(request.form.get('temperature')) if request.form.get('temperature') != '' else 0.81
        n_ctx = int(request.form.get('context')) if request.form.get('context') != '' else 2048
        self.assistant.unload_model()
        self.assistant.load_model(selected_model, temperature, n_gpu_layers, system_message,n_ctx, n_ctx)
        return f'''
                \nModel:{selected_model}
                \ntemp: {temperature}
                \nlayers: {n_gpu_layers}
                \nSM: {system_message}
                \nctx: {n_ctx}
                '''

    def unload_model(self):
        self.assistant.unload_model()
        return 'Model uninstalled 🫗!'

    def stop_response(self):
        try:
            self.assistant.stop_response()
            # Emitir señal de parada via WebSocket
            self.socketio.emit('response_stopped', {
                'message': 'Response stopped by user',
                'timestamp': time.time()
            }, namespace='/test')
            return {"status": "success", "message": "Response stopped successfully"}
        except Exception as e:
            print(f"Error stopping response: {e}")
            return {"status": "error", "message": f"Error stopping response: {str(e)}"}

    def get_models_list(self, folder_path):
        models_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".gguf"):
                    model_path = os.path.join(root, file)
                    models_list.append(model_path)
        return models_list

    def get_format_list(self):
        formats = LlamaChatCompletionHandlerRegistry()._chat_handlers.keys()
        return list(formats)
    
    def get_chat_list(self):
        nombres_archivos_json = []
        chats_dir = 'chats'
        if not os.path.exists(chats_dir):
            os.makedirs(chats_dir)
            
        archivos = os.listdir(chats_dir)
        for archivo in archivos:
            if archivo.endswith('.json'):
                nombres_archivos_json.append(archivo.replace('.json', ''))
        nombres_archivos_json.sort(reverse=True)
        return nombres_archivos_json

    def stop_server(self):
        os.kill(os.getpid(), signal.SIGINT) 
        return 'Server shutting down...'
