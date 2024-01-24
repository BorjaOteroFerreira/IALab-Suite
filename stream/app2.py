from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from stream.llama2 import LlamaAssistant
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'WindowsApesta'
socketio = SocketIO(app, ping_timeout=600, ping_interval=60, cors_allowed_origins="*")

model_path = "models/TheBloke/llama2_7b_chat_uncensored-GGUF/llama2_7b_chat_uncensored.Q8_0.gguf"
llama_assistant = None

@app.before_request
def before_first_request():
    global llama_assistant
    if llama_assistant is None:
        llama_assistant = LlamaAssistant(model_path=model_path,chat_format="tb-uncensored")

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response 

@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(app.static_folder, filename, cache_timeout=0)

@app.route("/")
def index():
    return render_template("index_socketio.html")

@app.route('/clear_context', methods=['POST'])
def clear_context():
    llama_assistant.clear_context()
    return "Contexto limpiado"

@app.route("/ask", methods=["POST"])
def ask():
    socketio.emit('response', {'content': llama_assistant.get_assistant_response(llama_assistant.message_queue)})
    return socketio.emit('response', {'content': llama_assistant.get_assistant_response(llama_assistant.message_queue)})

@socketio.on('join')
def handle_join(data):
    room_id = data['room_id']
    join_room(room_id)
    print(f"Cliente {request.sid} se unió a la sala {room_id}")

@socketio.on('leave')
def handle_leave(data):
    room_id = data['room_id']
    leave_room(room_id)
    print(f"Cliente {request.sid} salió de la sala {room_id}")

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
