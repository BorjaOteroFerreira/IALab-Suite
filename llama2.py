import time
import platform
from llama_cpp import Llama

class LlamaAssistant:
    def __init__(self, model_path):
        # ... (código anterior)

        # Porcentaje máximo de capacidad del historial antes de comenzar a borrar
        self.max_context_percentage = 0.8

    def trim_context(self):
        # Calcula el límite de mensajes a mantener
        max_context_size = int(self.max_context_percentage * len(self.conversation_history))
        # Mantén siempre el mensaje inicial del sistema
        max_context_size = max(max_context_size, 1)
        
        # Elimina mensajes más antiguos para mantener el contexto dentro del límite
        self.conversation_history = self.conversation_history[-max_context_size:]

    def add_user_input(self, user_input):
        # Añadir input del usuario al historial de la conversación
        self.conversation_history.append({"role": "user", "content": user_input})
        self.trim_context()

    def get_assistant_response(self):
        last_user_input_time = time.time()

        # Realizar la inferencia
        output = self.llm.create_chat_completion(messages=self.conversation_history, max_tokens=2048)

        # Obtener la respuesta
        response = output['choices'][0]['message']['content']

        # Añadir la respuesta al historial de la conversación
        self.conversation_history.append({"role": "assistant", "content": response})
        elapsed_time = round(time.time() - last_user_input_time, 2)
        response += " | " + str(elapsed_time) + "s"
        self.trim_context()  # Limpia el contexto después de recibir la respuesta

        return response

# Resto del código (if __name__ == "__main__", etc.)

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