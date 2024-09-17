import copy
import datetime
import queue
import re
import threading
import time
from tools.search_tools import SearchTools
from tools.video_search_tool import YoutubeVideoSearchTool
from tools.cripto_price import CriptoPrice
from tools.generate_image import ImageGenerationTool
import os
import pyttsx3
from colorama import Fore, Style

os.environ["YOUTUBE_API_KEY"] = 'AIzaSyDIfrz9h4Y7KKExF-j8VNztYGypt6EYC_o'
os.environ["SERPER_API_KEY"] = 'efdb015cbec193833a7ace9fc226bea17c6c5268'


class Cortex:
    def __init__(self, prompt_o, prompt, response, model, socket):
        self.output_console = f'💭 {response}'
        self.original_prompt = prompt_o
        self.prompt = prompt
        self.prompt.append({"role": "assistant", "content": response})
        self.socket = socket
        self.fecha = datetime.datetime.now()
        self.engine_lock = threading.Lock()
        self.response_queue = queue.Queue()
        self.tools = {
            'buscar_en_internet': SearchTools.search_internet,
            'video_search_tool': YoutubeVideoSearchTool.run,
            'cripto_price': CriptoPrice.get_price,
            'generate_image': ImageGenerationTool.run
        }

        print(f'\n{Fore.BLUE}🧠 Razonando\n💭 {response}{Style.RESET_ALL}')
        print(f'PROMPT{self.prompt}')
        self._detectar_necesidad_herramienta(response, model)

    def _enviar_a_consola(self, mensaje, rol):
        self.socket.emit('output_console', {'content': mensaje, 'role': rol}, namespace='/test')

    def _detectar_necesidad_herramienta(self, response, model):
        print('Detectar necesidad de herramienta')
        self._enviar_a_consola(self.output_console, 'pensamiento')

        patrones_regex = [  r'herramienta\s*\'([^\']+)\'.*consulta\s*\'([^\']+)\'',
                            r"\[Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'\]",
                            r"funcion:\s*'([^']+)',\s*query:\s*'([^']+)'\]",
                            r"función:\s*'([^']+)',\s*query:\s*'([^']+)'\]",
                            r"función:\s*'([^']+)',\s*consulta:\s*'([^']+)'\]",
                            r'herramienta:\s*\'([^\']+)\'.*consulta:\s*\'([^\']+)\'',
                            r'herramienta\s*\"([^"]+)\"\s*con\s*la\s*siguiente\s*consulta:\s*\"([^"]+)\"',
                            r'función\s*\"([^"]+)\"\s*con\s*la\s*consulta\s*\"([^"]+)\"',
                            r'función\s*\"([^"]+)\"\s*con\s*la\s*siguiente\s*consulta\s*\"([^"]+)\"',
                            r"\[Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'",
                            r"Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'\s*,?\s*data:\s*'(.*)'\s*",
                            r"data:\s*'(.*)'\s*,?\s*Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'",
                            r"Funcion:\s*'([^']+)',\s*query:\s*'([^ ']+)'(.*)",
                            r"\[Funcion:\s*'([^']+)',\s*query:\s*'([^ ']+)'(.*)\]",
                            r"\[\s*Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'\s*\]",
                            r"\[\s*Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'",
                            r"\[Funcion:\s*'\s*([^']+)\s*',\s*query:\s*'\s*([^']+)\s*'\]",
                            r'\[Funcion:\s*"([^"]+)",\s*query:\s*"([^"]+)"',
                            r'\[Funcion:\s*([^\s]+),\s*query:\s*([^\s]+)\]',
                            r"\[Funcion:\s*'([^']+)' \s*,\s* query:\s*'([^']+)'",
                            r"\[Funcion:\s*'([^']+)',\s*query:\s*\[([^\]]+)\]\]",
                            r"\[video_search_tool '([^']+)'\]",
                            r"\[buscar_en_internet '([^']+)'\]",
                            r"\[cripto_price '([^']+)'\]",
                            r"función\s+'buscar\s+en\s+internet'\s+con\s+la\s+query\s+'([^']+)'",
                            r'(?P<funcion>buscar_en_internet|video_search_tool|cripto_price)\s+con\s+la\s+consulta\s+"([^"]+)"',
                            r'función\s*\"([^"]+)\"\s+con\s+las\s+consultas\s+"([^"]+)"\s+y\s+"([^"]+)"',
                            r"\[Funcion '(\w+)' query='(.+?)'\]",
                            r"\[Funcion\s+'([^']+)'\s*,\s*query\s*=\s*'([^']+)' \]",
                            r"\[Funcion\s+'([^']+)'\s*,\s*Query\s*=\s*'([^']+)' \]"        

]

        coincidencias = self._extraer_coincidencias(response, patrones_regex)
        self._usar_herramientas(coincidencias, model)

    def _extraer_coincidencias(self, response, patrones_regex):
        coincidencias = set()
        herramientas_ejecutadas = set()
        for regex_pattern in patrones_regex:
            matches = re.findall(regex_pattern, response, re.IGNORECASE)
            for match in matches:
                funcion_texto = match[0]
                query_texto = match[1]
                coincidencias.add((funcion_texto, query_texto))
                herramientas_ejecutadas.add(funcion_texto)

        return list(coincidencias)

    def _usar_herramientas(self, coincidencias, model):
        addon = 'No te olvides de incluir las imagenes en el formato proporcionado por la herramienta en tu respuesta.'
        for funcion_texto, query_texto in coincidencias:
            print("")
            funcion_texto = funcion_texto.replace("'", "")
            query_texto = query_texto.replace("'", "").split(',') if 'cripto_price' in funcion_texto else query_texto
            print(f'\n{Fore.GREEN}[->] Usando {funcion_texto} con consulta {query_texto}...{Style.RESET_ALL}')
            self._enviar_a_consola(f'[->] Usando {funcion_texto} con consulta {query_texto}...', 'info')

            resultado_herramienta = self.ejecutar_herramienta(funcion_texto, query_texto)
            addon += resultado_herramienta
            print(f'{Fore.YELLOW}[!] Eureka!:{Style.RESET_ALL}\n{Fore.MAGENTA}{resultado_herramienta}{Style.RESET_ALL}')

        self.crear_response_final(addon, model)
       

    def ejecutar_herramienta(self, nombre_herramienta, consulta):
        print("Herramienta", nombre_herramienta, consulta)
        try:
            if nombre_herramienta == "video_search_tool":
                resultado_herramienta, ids = self.tools[nombre_herramienta](consulta)
                self.socket.emit('utilidades', {"ids": ids}, namespace='/test')
            elif nombre_herramienta == "generate_image":
                resultado_herramienta = self.tools[nombre_herramienta](consulta)
                imagen = f"<img src='{resultado_herramienta}' width='590' height='345'>", 
                clean_url = str(imagen).replace(",", "").replace("(", "").replace(")", "")

                resultado_herramienta = f'Aqui tienes la imagen: {clean_url}, no acortes ni alteres la  url ni la etiqueta img. Incluyela en tu respuesta final sin texto adicional despues de la etiqueta'
                self.socket.emit('assistant_response', {'content': resultado_herramienta}, namespace='/test')
                print("Enviado")
            else:
                resultado_herramienta = self.tools[nombre_herramienta](consulta)
            self.output_console = resultado_herramienta
            self._enviar_a_consola(self.output_console, 'tool')
            return resultado_herramienta
        except Exception as e:
            print(f'Error usando la herramienta {nombre_herramienta}: {e}')
            return 'Ha habido un error, asegúrate de que has usado una herramienta existente y la sintaxis es correcta'

    def crear_response_final(self, addon, model):
        self.prompt[0]['content'] = self.original_prompt[0]['content']
        herramientas = f'Utiliza esta información proporcionada por la herramienta, inserta los enlaces e imagenes en tu respuesta : {addon}. Responde en completo español.'
        self.prompt.append({"role": "assistant", "content": herramientas})
        self.generar_response(model)

    def generar_response(self, model):
        salida = '[>] Generando response informada...✍️'
        self._enviar_a_consola(salida, 'info')
        print(f'\n{Fore.GREEN}{salida}{Style.RESET_ALL}')
        response = self.transmitir_response(model, self.prompt)
        salida_final = f'\n{Fore.GREEN}✍️FINAL {response}{Style.RESET_ALL}\n\n{Fore.BLUE}¿Puedo ayudarte en algo más?{Style.RESET_ALL}\n'
        print(salida_final)

    def transmitir_response(self, model, prompt):
        #speak_thread = threading.Thread(target=self.hablar_response)
        #speak_thread.start()
        response_completa = ''
        linea = ''
        for chunk in model.create_chat_completion(messages=prompt, max_tokens=1024, stream=True):
            if 'content' in chunk['choices'][0]['delta']:
                fragmento_response = chunk['choices'][0]['delta']['content']
                response_completa += fragmento_response
                for char in fragmento_response:
                    linea += char
                    if char == '\n':
                        linea = self.eliminar_enlaces(linea)
                        if linea.strip():
                            self.response_queue.put(linea.strip())
                        linea = ''
                self.socket.emit('assistant_response', {'content': chunk}, namespace='/test')
                time.sleep(0.01)

        linea = self.eliminar_enlaces(linea)
        if linea.strip():
            self.response_queue.put(linea.strip())
        self.response_queue.put(None)
           
        return response_completa

    def eliminar_enlaces(self, linea):
        regex_enlaces = r'\[?\b(?:https?://|www\.)\S+\b\]?|<\b(?:https?://|www\.)\S+\b>'
        linea_sin_enlaces = re.sub(regex_enlaces, ' enlace ', linea).replace('/', '')
        return self.eliminar_lineas_repetidas(linea_sin_enlaces).replace('#', '')

    def eliminar_lineas_repetidas(self, texto):
        regex_lineas = r'^=+$'
        return re.sub(regex_lineas, '', texto, flags=re.MULTILINE)

    def hablar_response(self):
        engine = pyttsx3.init()
        velocidad = 200
        engine.setProperty('rate', velocidad)
        while True:
            response_chunk = self.response_queue.get()
            if response_chunk is None:
               break
            with self.engine_lock:
                engine.say(response_chunk)
                engine.runAndWait()  # Wait for each chunk to be spoken
        engine.stop()
        return True
    

                


      