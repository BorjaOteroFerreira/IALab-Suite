from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
from Assistant import LlamaAssistant

app = Flask(__name__)
socketio = SocketIO(app)
model_path="models/TheBloke/Mixtral_7Bx2_MoE-GGUF/mixtral_7bx2_moe.Q6_K.gguf"
chat_format="airobos" 
llm = None       

@app.before_request
def before_first_request():
    global llm
    if llm is None:
        llm = LlamaAssistant(model_path=model_path,chat_format=chat_format)

@app.route('/')
def index():
    models_list = get_models_list("models")
    format_list = get_format_list()
    return render_template('index.html', models_list=models_list, format_list=format_list)

@socketio.on('user_input', namespace='/test')

@app.route('/user_input', methods=['POST'])
def handle_user_input():
    user_input = request.form.get('content')
    # Procesar la entrada del usuario según sea necesario
    print("Usuario dijo:", user_input)
    # Realizar operaciones adicionales aquí
    llm.add_user_input(user_input,socketio)
    llm.emit_assistant_response_stream(socketio)
    # Devolver una respuesta si es necesario
    return 'Respuesta del servidor'

@app.route('/start_model', methods=['POST'])
def start_model():
    selected_model = request.form.get('model_path')
    selected_format = request.form.get('format')
    llm.unload_model()
    llm.clear_context()
    llm.start_model(selected_model, selected_format)
    socketio.emit('clear_chat', namespace='/test')  # Agrega este evento para limpiar el historial en el cliente
    return 'Modelo iniciado: ' + selected_model

@app.route('/unload_model', methods=['POST'])
def unload_model():
    llm.unload_model()
    llm.clear_context()
    return 'Modelo desinstalado'

@app.route('/clear_context', methods=['POST'])
def clear_context():
    llm.clear_context()
    return "Historial limpiado"

def get_models_list(folder_path):
    models_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".gguf"):
                model_path = os.path.join(root, file)
                models_list.append(model_path)
    return models_list

def get_format_list():
    format_list = ["llama-2","tb-uncensored", "airoboros", "guanaco"]
    return format_list

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
