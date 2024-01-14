import time
from llama_cpp import Llama

class LlamaAssistant:
    def __init__(self, model_path):
        # Ruta al modelo local
        self.model_path = model_path

        # Configuración específica para Metal (ajusta según sea necesario)
        self.metal_options = {
            "device": "metal",
            "metal_device_id": 0,
            # Sustituir por torch en Windows para utilizar CUDA
        }

        # Inicializar el modelo Llama2
        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=14,
            n_ctx=4096,
            metal_options=self.metal_options,
            chat_format="llama-2"
        )

        # Historial de conversación
        self.conversation_history = []
        mensaje_sistema = "Eres un asistente de programación que solo sabe hablar en español, cuando te pidan codigo no des exlpicaiones adicionales"
        self.conversation_history.append({"role": "system", "content": mensaje_sistema})

    def add_user_input(self, user_input):
        # Añadir input del usuario al historial de la conversación
        self.conversation_history.append({"role": "user", "content": user_input})

    def get_assistant_response(self):
        # Realizar la inferencia
        output = self.llm.create_chat_completion(messages=self.conversation_history, max_tokens=2048)

        # Obtener la respuesta
        response = output['choices'][0]['message']['content']

        # Añadir la respuesta al historial de la conversación
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

if __name__ == "__main__":
    model_path = "./models/llama-2-7b-chat.Q8_0.gguf"
    llama_assistant = LlamaAssistant(model_path=model_path)
    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'exit':
            break

        # Añadir input del usuario al historial de la conversación
        llama_assistant.add_user_input(user_input)

        # Obtener la respuesta del asistente
        response = llama_assistant.get_assistant_response()

        # Imprimir la respuesta
        print(f"Respuesta: {response}")
