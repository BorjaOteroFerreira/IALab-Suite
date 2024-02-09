from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import os
from Assistant import Assistant
import logging

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app)

logging.basicConfig(filename='flask_log.log', level=logging.INFO)
selected_model="models/TheBloke/airoboros-l2-7B-gpt4-2.0-GGUF/airoboros-l2-7B-gpt4-2.0.Q8_0.gguf"
selected_format="airoboros" 
llm = None       
@app.before_request
def before_first_request():
    global llm
    if llm is None:
        llm = Assistant(model_path=selected_model,chat_format=selected_format)

@app.route('/')
def index():
    models_list = get_models_list("models")
    format_list = get_format_list()
    return render_template('index.html', models_list=models_list, format_list=format_list)

@socketio.on('user_input', namespace='/test')

@app.route('/user_input', methods=['POST'])
def handle_user_input():
    user_input = request.form.get('content')
    print("Usuario dijo:", user_input)
    llm.add_user_input(user_input)
    llm.emit_assistant_response_stream(socketio)
    return 'Respuesta finalizada! 📩'

@app.route('/start_model', methods=['POST'])
def start_model():
    selected_model = request.form.get('model_path')
    selected_format = request.form.get('format')
    n_gpu_layers = request.form.get('n_gpu_layers')
    system_message = request.form.get('system_message')
    n_ctx = int(request.form.get('context')) if request.form.get('context') != '' else 2048
    llm.unload_model()
    llm.clear_context()
    llm.start_model(selected_model, selected_format, n_gpu_layers, system_message, n_ctx)
    return 'Modelo iniciado:\n ' + selected_model

@app.route('/unload_model', methods=['POST'])
def unload_model():
    llm.unload_model()
    llm.clear_context()
    return 'Modelo desinstalado!'

@app.route('/clear_context', methods=['POST'])
def clear_context():
    llm.clear_context()
    return "Historial limpiado!"

def get_models_list(folder_path):
    models_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".gguf"):
                model_path = os.path.join(root, file)
                models_list.append(model_path)
    return models_list

def get_format_list():
    format_list = [ "guanaco", "llama-2","tb-uncensored", "airoboros", "mistral-24", "qwen", "vicuna"]
    return format_list



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
