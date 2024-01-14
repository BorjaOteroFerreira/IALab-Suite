from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from llama2f import LlamaAssistant
from flask_cors import CORS

app = Flask(__name__)
socketio = SocketIO(app)

# Instanciar el asistente de Llama
model_path = "./models/llama-2-7b-chat.Q8_0.gguf"
llama_assistant = LlamaAssistant(model_path=model_path)

@app.route("/")
def index():
    return render_template("index_socketio.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.form["user_input"]

    # Añadir input del usuario al asistente de Llama
    llama_assistant.add_user_input(user_input)

    # Obtener la respuesta del asistente
    response = llama_assistant.get_assistant_response()

    # Enviar la respuesta a través del socket
    socketio.emit("response", {"role": "assistant", "content": response})

    return jsonify({"status": "success"})

if __name__ == "__main__":
    CORS(app)
    # Iniciar la aplicación Flask y SocketIO
    socketio.run(app, debug=True)
