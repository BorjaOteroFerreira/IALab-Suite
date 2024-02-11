from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
from Assistant import Assistant
import logging

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app)

logging.basicConfig(filename='flask_log.log', level=logging.INFO)
default_model_path="models/llama/llama-2-7b-chat.Q8_0.gguf"
default_chat_format="llama-2" 
assistant = None  

@app.before_request
def before_first_request():
    global assistant
    if assistant is None:
        assistant = Assistant(default_model_path=default_model_path,default_chat_format=default_chat_format)

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
    assistant.add_user_input(user_input)
    assistant.emit_assistant_response_stream(socketio)
    return 'Respuesta finalizada! 📩'

@app.route('/load_model', methods=['POST'])
def load_model():
    selected_model = request.form.get('model_path')
    selected_format = request.form.get('format')
    n_gpu_layers = request.form.get('n_gpu_layers')
    system_message = request.form.get('system_message')
    n_ctx = int(request.form.get('context')) if request.form.get('context') != ''  else 2048
    assistant.unload_model()
    assistant.clear_context()
    assistant.load_model(selected_model, selected_format, n_gpu_layers, system_message, n_ctx)
    return 'Modelo iniciado:\n ' + selected_model

@app.route('/unload_model', methods=['POST'])
def unload_model():
    assistant.unload_model()
    assistant.clear_context()
    return 'Modelo desinstalado! '

@app.route('/clear_context', methods=['POST'])
def clear_context():
    assistant.clear_context()
    return "Historial limpiado!"

@app.route('/stop_response', methods=['POST'])
def stop_response():
    assistant.stop_response()
    return "Respuesta cancelada!"

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

'''
TODO:
    - Best control of context.
    - FormatChat editor. 
    - Conversations List. 
    - Save conversation.
    - Advanced parameters to menu configuration.
    - Capture exceptions.
    - Refactor the code. 
    - Implement LangChain.
'''