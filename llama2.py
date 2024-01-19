import time
import platform  # Importa la biblioteca platform
from llama_cpp import Llama


class LlamaAssistant:
    def __init__(self, model_path):
        self.mensaje_sistema ='''Eres un asistente con una personalidad NIHILISTA, respetuoso y honesto. Como experto programador , debe examinar los detalles proporcionados para asegurarse de que sean utilizables . 
        Si una pregunta no tiene ningún sentido o no es objetivamente coherente. Si no sabe la respuesta a una pregunta, no comparta información falsa. Mantenga sus respuestas en español y no se desvíe de la pregunta.
        Si la respuesta a la pregunta o consulta formulada está completa, finalice su respuesta. Mantenga la respuesta precisa y no omita detalles relacionados con la consulta. Proporcione su salida en formato Markdown'''
        self.mensaje_sistema2 = "usa muchos emoticonos"
        # Ruta al modelo local
        self.model_path = model_path
        # Configuración específica para CUDA en Windows con una Nvidia
        self.cuda_options = {
            "device": "cuda",
            "cuda_device_id": 0,  # El ID del dispositivo CUDA, ajusta según sea necesario
        }
        # Configuración específica para Metal en macOS
        self.metal_options = {
            "device": "metal",
            "metal_device_id": 0,
        }
        # Determina el sistema operativo actual y configura las opciones correspondientes
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
        elif platform.system() == 'Darwin':  # 'Darwin' es la identificación de macOS
            self.device_options = self.metal_options
        else:
            raise RuntimeError("Sistema operativo no compatible")

        # Inicializar el modelo Llama2
        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=14,
            n_ctx=8192,
            **self.device_options, 
            chat_format="llama-2",
            temp = 0.810000,
            top_k = 80, 
            ktop_p = 0.950000,
            use_mlock=False,
            rope_scaling_type = 1, 
            rope_freq_base = 0,  
            rope_freq_scale = .8,  
            numa=False,
            vocab_size=100000
        )

        # Historial de conversación
        self.conversation_history = []
     
        self.conversation_history.append({"role": "system", "content": self.mensaje_sistema})



    def add_user_input(self, user_input):
        # Añadir input del usuario al historial de la conversación
        self.conversation_history.append({"role": "user", "content": user_input})


    def get_assistant_response(self):
        last_user_input_time = time.time()

        # Realizar la inferencia
        output = self.llm.create_chat_completion(messages=self.conversation_history,
                                                    max_tokens=12280,
                                                    repeat_penalty=1,
                                                    frequency_penalty=1,
                                                    presence_penalty=1.3)
        
        # Obtener la respuesta
        response = output['choices'][0]['message']['content']
        # Añadir la respuesta al historial de la conversación
        self.conversation_history.append({"role": "assistant", "content": response})
        elapsed_time = round(time.time() - last_user_input_time, 2)
        response+=" | " + str(elapsed_time) + "s"
        return response
        
    
    def clear_context(self):
        self.conversation_history.clear()
        self.conversation_history.append({"role": "system", "content": self.mensaje_sistema})
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history: 
            print(mensaje)


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