import time
import platform  # Importa la biblioteca platform
from llama_cpp import Llama


class LlamaAssistant:
    def __init__(self, model_path):
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
            n_ctx=4096,
            **self.device_options,  # Usa las opciones correspondientes según el sistema operativo
            chat_format="llama-2"
        )

        # Historial de conversación
        self.conversation_history = []
        '''self.mensaje_sistema = 
        Eres un portfolio inteligente de habla española, solo puedes hablar español , te van a hacer preguntas sobre Borja, tu creador,
        asique te voy a dar un perfil completo de el, para que puedas responder preguntas sobre Borja:
        Nombre completo: Borja Otero Ferreira;
        Fecha de nacimiento : 27-03-1989;
        Edad: 34 años;
        Estado civil actual: En pareja.
        Ocupación actual: Estudiante;
        Centro de estudios: IES Chan Do Monte (Estudiando Ciclo superior de Desarrollo Multiplataforma);
        Direccion del centro de estudios:IES Chan do Monte,  Marín,  36900 (pontevedra);
        Habilidades: fantástico desarrollador multiplataforma, tiene grandes habilidades comunicativas, capacidad de adaptacion, Liderazgo;
        Idiomas: 
        🇪🇸Español - nativo, 
         Gallego - nativo, 
        🏴󠁧󠁢󠁥󠁮󠁧󠁿 Ingles - escrito, 
        🇵🇹 Portugues - oral;
        Lenguajes de programacion:
        Python,
        Java,
        Javascript,
        Php,
        SQL,
        HTML,
        XML,
        CSS,
        Proyectos: Cavern Quest (videojuego JavaFX), API rest (Conjunto de IAs de distintos tipos);
        Experiencia profesional: Tiene experiencia profesional en varios campos de la IT como  Redes y sistemas, pero su pasión es la programación;
        Sobre Borja: Es un chico joven, con energia y mucha ilusion por la tecnología, es un apasionado de la programación y la inteligencia artificial.
        Metas: las metas de Borja, son afianzar una carrera laboral en el mundo del desarrollo, 
            sus preferencias tienden hacia el backend y prefiere la programacion de escritorio o la movil a la progrmacion web, aunque puede adaptarse a cualquiera de ellas
            sus aficiones son el Trekking , y las rutas gastronómicas.  
        Perfil de github: "github.com/BorjaOteroFerreira 🌍";
        Telefono de contacto: 698166558 📞;
        Email de contacto : '<a href="mailto:borjaoteroferreira@gmail.com">borjaoteroferreira@gmail.com</a>'
        '''
        self.mensaje_sistema = "Eres un asistente de programación que solo sabe hablar en español, cuando te pidan codigo no des exlpicaiones adicionales, ademas quiero que uses emoticonos en tus respuestas"
        #mensaje_sistema = "Eres un experto entrenador de futbol español que solo sabe hablar en español, ademas quiero que uses emoticonos en tus respuestas"
        #mensaje_sistema = "Eres un asistente experto en criptos que solo sabe hablar en español, ademas quiero que uses emoticonos en tus respuestas pero uno o dos sin pasarse"
        self.mensaje_sistema ='language: es'
        self.conversation_history.append({"role": "system", "content": self.mensaje_sistema})
 
        


    def add_user_input(self, user_input):
        # Añadir input del usuario al historial de la conversación
        self.conversation_history.append({"role": "user", "content": user_input})

    def get_assistant_response(self):
        last_user_input_time = time.time()

        # Realizar la inferencia
        output = self.llm.create_chat_completion(messages=self.conversation_history, max_tokens=8192)

        # Obtener la respuesta
        response = output['choices'][0]['message']['content']

        # Añadir la respuesta al historial de la conversación
        self.conversation_history.append({"role": "assistant", "content": response})
        elapsed_time = round(time.time() - last_user_input_time, 2)
        response+=" | "+str(elapsed_time)+"s"
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