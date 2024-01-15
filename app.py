from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from llama2 import LlamaAssistant
from flask_cors import CORS


app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")
# Instanciar el asistente de Llama
model_path = "./models/llama-2-7b-chat.Q8_0.gguf"
llama_assistant = LlamaAssistant(model_path=model_path)


@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(app.static_folder, filename, cache_timeout=0)


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response
    
@app.route("/")
def index():
    return render_template("index_socketio.html")

@app.route('/clear_context', methods=['POST'])
def clear_context():
    llama_assistant.clear_context()
    return "Contexto limpiado"


@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.form["user_input"]

    # Añadir input del usuario al asistente de Llama
    llama_assistant.add_user_input(user_input)
    print(user_input)
    # Obtener la respuesta del asistente
    response = llama_assistant.get_assistant_response()
    
    # Enviar la respuesta a través del socket
    socketio.emit("response", {"role": "assistant", "content": response})

    return jsonify({"status": "success"})

if __name__ == "__main__":
    CORS(app)
    # Iniciar la aplicación Flask y SocketIO
    if __name__ == '__main__':
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
