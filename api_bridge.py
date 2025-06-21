from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/models', methods=['GET'])
def get_models():
    models = ["Modelo 1", "Modelo 2", "Modelo 3"]
    return jsonify(models)

@app.route('/api/formats', methods=['GET'])
def get_formats():
    formats = ["chatml", "llama", "openchat"]
    return jsonify(formats)

@app.route('/api/chats', methods=['GET'])
def get_chats():
    return jsonify(["Chat 1", "Chat 2", "Chat 3"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)
