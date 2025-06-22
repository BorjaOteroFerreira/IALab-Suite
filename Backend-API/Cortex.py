import copy 
import datetime 
import queue 
import re 
import threading 
import time 
import os
import pyttsx3
from colorama import Fore, Style

from tools.tool_registry import ToolRegistry
from SocketResponseHandler import SocketResponseHandler

os.environ["YOUTUBE_API_KEY"] = 'AIzaSyDIfrz9h4Y7KKExF-j8VNztYGypt6EYC_o'
os.environ["SERPER_API_KEY"] = 'efdb015cbec193833a7ace9fc226bea17c6c5268'


class Cortex:
    def __init__(self, prompt_o, prompt, response, model, socket, assistant=None):        
        # Inicializar propiedades (response ahora es ignorado, se determinará internamente)
        self.original_prompt = prompt_o
        self.prompt = prompt
        self.socket = socket
        self.assistant = assistant  # Referencia al assistant para acceder a stop_emit
        self.fecha = datetime.datetime.now()
        self.engine_lock = threading.Lock()
        self.response_queue = queue.Queue()
          # Inicializar el registry de herramientas
        self.tool_registry = ToolRegistry()
        # Registrar automáticamente todas las herramientas disponibles
        self.tool_registry.discover_tools()
        
        # Obtener las herramientas disponibles del registry
        self.tools = self._get_available_tools_dict()

        self.patrones_regex = [
            r'herramienta\s*\'([^\']+)\'.*consulta\s*\'([^\']+)\'',
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
            r"\[Funcion\s+'([^']+)'\s*,\s*Query\s*=\s*'([^']+)' \]",   
            r"\[\s*Funcion:\s*'([^']+)',\s*query:\s*'([^']+)'\s*\]"        ]
        
        self.max_iterations = 3  # Límite de iteraciones para evitar bucles infinitos
          # Ahora el flujo principal: determinar herramientas y procesarlas
        herramientas_necesarias = self._determinar_herramientas_necesarias(model)
        self.output_console = f'💭 {herramientas_necesarias}'
        
        # Procesar las herramientas necesarias
        self.final_response = self.process_tool_needs(herramientas_necesarias, model)

    def _determinar_herramientas_necesarias(self, model):
        """Determina qué herramientas necesita usando el modelo"""        # Crear prompt para determinar herramientas usando el registry
        base_instructions = """
TU PRINCIPAL OBJETIVO ES DETERMINAR QUE HERRAMIENTA NECESITAS
"""
        
        # Obtener las instrucciones dinámicas de herramientas
        tool_instructions = self._get_tool_instructions()
        
        additional_instructions = """
responde unicamente con la o las herramientas a lanzar, ejemplo: 
supongamos que necesitas buscar el tiempo en internet , contestas: 
[Funcion: 'buscar_en_internet' , query: 'tiempo proximos dias' ]
Asegurate de que utilizas la sintaxis correcta al colocar un corchete al inicio y otro al final.
Puedes usar mas de una herramienta si lo necesitas.
Debes contestar solo con las funciones que usarias sin texto antes ni despues
SIEMPRE DEBES RESPONDER EN ESPAÑOL.
"""
        
        instrucciones_herramientas = base_instructions + tool_instructions + additional_instructions

        # Crear una copia del prompt original y modificar el mensaje del sistema
        prompt_herramientas = copy.deepcopy(self.original_prompt)
        if prompt_herramientas and prompt_herramientas[0]['role'] == 'system':
            prompt_herramientas[0]['content'] = instrucciones_herramientas
        
        # Solicitar al modelo que determine las herramientas
        try:
            response = ""
            for chunk in model.create_chat_completion(messages=prompt_herramientas, max_tokens=200, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response += chunk['choices'][0]['delta']['content']
            print(f'\n{Fore.BLUE}🧠 Determinando herramientas necesarias\n💭 {response}{Style.RESET_ALL}')
            return response.strip()
        except Exception as e:
            print(f"Error determinando herramientas: {e}")
            return ""

    def _enviar_a_consola(self, mensaje, rol):
        SocketResponseHandler.emit_console_output(self.socket, mensaje, rol)

    def process_tool_needs(self, response, model):
        """Procesa la respuesta para detectar y usar herramientas, con posibilidad de iteración"""
        print('Iniciando proceso iterativo de detección y uso de herramientas')
        self._enviar_a_consola(self.output_console, 'pensamiento')
        
        herramientas_usadas = []
        resultados_herramientas = []
        iterations = 0
        current_response = response
        
        while iterations < self.max_iterations:
            # Verificar si se debe detener la respuesta
            if self.assistant and self.assistant.stop_emit:
                print(f"{Fore.RED}🛑 Stop signal detected, breaking tool iterations{Style.RESET_ALL}")
                self._enviar_a_consola("🛑 Process stopped by user", 'info')
                break
                
            iterations += 1
            print(f"\n{Fore.CYAN}[*] Iteración {iterations} de detección de herramientas{Style.RESET_ALL}")
            self._enviar_a_consola(f"[*] Iteración {iterations} de detección de herramientas", 'info')
            
            # Detectar coincidencias de herramientas 
            coincidencias = self._extraer_coincidencias(current_response, self.patrones_regex)
            
            # Si no hay coincidencias, terminar el ciclo
            if not coincidencias:
                print(f"{Fore.GREEN}[*] No se detectaron más herramientas necesarias{Style.RESET_ALL}")
                self._enviar_a_consola("[*] No se detectaron más herramientas necesarias", 'info')
                break
                
            # Ejecutar las herramientas detectadas
            for funcion_texto, query_texto in coincidencias:
                # Verificar si se debe detener antes de ejecutar cada herramienta
                if self.assistant and self.assistant.stop_emit:
                    print(f"{Fore.RED}🛑 Stop signal detected during tool execution{Style.RESET_ALL}")
                    return "🛑 Process stopped by user"
                    
                if (funcion_texto, query_texto) not in herramientas_usadas:  # Evitar repetir exactamente la misma consulta
                    resultado = self._ejecutar_herramienta_individual(funcion_texto, query_texto)
                    resultados_herramientas.append((funcion_texto, query_texto, resultado))
                    herramientas_usadas.append((funcion_texto, query_texto))
            
            # Consultar al modelo para decidir si necesita más herramientas
            if herramientas_usadas:
                current_response = self._consultar_modelo_para_decision(model, resultados_herramientas)
        
        # Generar respuesta final
        final_response = self.generar_respuesta_final(model, resultados_herramientas)
        return final_response

    def _consultar_modelo_para_decision(self, model, resultados_herramientas):
        """Consulta al modelo para decidir si necesita usar más herramientas o responder"""
        prompt_decision = self._preparar_prompt_decision(resultados_herramientas)
        
        print(f"\n{Fore.BLUE}[*] Consultando al modelo para decisión de herramientas adicionales{Style.RESET_ALL}")
        self._enviar_a_consola("[*] Consultando al modelo para decisión de herramientas adicionales", 'info')
        response_decision = ""
        for chunk in model.create_chat_completion(messages=prompt_decision, max_tokens=1024, stream=True):
            # Verificar si se debe detener
            if self.assistant and self.assistant.stop_emit:
                print(f"{Fore.RED}🛑 Stop signal detected during decision consultation{Style.RESET_ALL}")
                return "🛑 Process stopped by user"
                
            if 'content' in chunk['choices'][0]['delta']:
                fragmento = chunk['choices'][0]['delta']['content']
                response_decision += fragmento
                # No enviamos esta respuesta intermedia al socket
        
        print(f"{Fore.YELLOW}[!] Decisión del modelo:{Style.RESET_ALL}\n{Fore.MAGENTA}{response_decision}{Style.RESET_ALL}")
        self._enviar_a_consola(f"[!] Decisión del modelo: {response_decision[:100]}...", 'pensamiento')
        
        return response_decision

    def _preparar_prompt_decision(self, resultados_herramientas):
        """Prepara el prompt para consultar al modelo sobre decisiones de herramientas adicionales"""
        # Copia del prompt original para no modificarlo
        decision_prompt = copy.deepcopy(self.original_prompt)
          # Información sobre las herramientas disponibles usando el registry
        herramientas_info = "Tienes disponibles las siguientes herramientas:\n"
        for tool_name in self.tool_registry.list_tools():
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                herramientas_info += f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}\n"
          # Información sobre los resultados de las herramientas ya utilizadas
        resultados_info = "He utilizado las siguientes herramientas con estos resultados:\n\n"
        for funcion, query, resultado in resultados_herramientas:
            resultados_info += f"Herramienta: '{funcion}' con consulta: '{query}'\n"
            if resultado is not None:
                resultado_str = str(resultado)
                if len(resultado_str) > 500:
                    resultados_info += f"Resultado: {resultado_str[:500]}...\n\n"
                else:
                    resultados_info += f"Resultado: {resultado_str}\n\n"
            else:
                resultados_info += f"Resultado: Sin resultado (herramienta devolvió None)\n\n"
        
        # Instrucción para el modelo
        instruccion = (
            "Basándote en los resultados anteriores, determina si necesitas usar herramientas adicionales "
            "para investigar más información (como enlaces encontrados) o si ya tienes suficiente información "
            "para responder al usuario. Si necesitas usar otra herramienta, indica cuál y con qué consulta, "
            "usando el formato [Funcion: 'nombre_funcion', query: 'consulta']. "
            "Si no necesitas más herramientas, responde con 'No necesito usar más herramientas' y proporciona "
            "un resumen de la información que usarás para responder al usuario."
            "si los resultados no muestran informacion relevante o no estan completos, puedes buscar mas informacion con dorks de google."        )
        
        # Añadir un mensaje de asistente para mantener la alternancia de roles
        decision_prompt.append({"role": "assistant", "content": "He ejecutado las herramientas solicitadas y tengo los resultados."})
        
        # Añadir la información al prompt        
        decision_prompt.append({"role": "user", "content": herramientas_info + resultados_info + instruccion})
        
        return decision_prompt

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

    def _ejecutar_herramienta_individual(self, funcion_texto, query_texto):
        # Verificar si se debe detener antes de ejecutar la herramienta
        if self.assistant and self.assistant.stop_emit:
            print(f"{Fore.RED}🛑 Stop signal detected before tool execution{Style.RESET_ALL}")
            return "🛑 Process stopped by user"
            
        print("")
        funcion_texto = funcion_texto.replace("'", "")
        query_texto = query_texto.replace("'", "").split(',') if 'cripto_price' in funcion_texto else query_texto
        print(f'\n{Fore.GREEN}[->] Usando {funcion_texto} con consulta {query_texto}...{Style.RESET_ALL}')
        self._enviar_a_consola(f'[->] Usando {funcion_texto} con consulta {query_texto}...', 'info')
        resultado_herramienta = self.ejecutar_herramienta(funcion_texto, query_texto)
        print(f'{Fore.YELLOW}[!] Eureka!:{Style.RESET_ALL}\n{Fore.MAGENTA}{resultado_herramienta}{Style.RESET_ALL}')
        return resultado_herramienta    
    
    def ejecutar_herramienta(self, nombre_herramienta, consulta):
        """Ejecuta una herramienta usando el registry"""
        try:
            # Usar el registry para ejecutar la herramienta
            resultado_ejecucion = self.tool_registry.execute_tool(nombre_herramienta, consulta)
            
            # Verificar si la ejecución fue exitosa
            if not resultado_ejecucion.success:
                error_msg = f'Error usando la herramienta {nombre_herramienta}: {resultado_ejecucion.error}'
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                return error_msg
            
            # Extraer los datos del resultado
            resultado_herramienta = resultado_ejecucion.data
            
            # Manejo especial para herramientas que devuelven múltiples valores
            if nombre_herramienta == "video_search_tool" and isinstance(resultado_herramienta, tuple):
                resultado_herramienta, ids = resultado_herramienta
                SocketResponseHandler.emit_utilities_data(self.socket, {"ids": ids})
            
            self.output_console = resultado_herramienta
            self._enviar_a_consola(self.output_console, 'tool')
            return resultado_herramienta
        except Exception as e:
            error_msg = f'Error usando la herramienta {nombre_herramienta}: {e}'
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            return error_msg

    def generar_respuesta_final(self, model, resultados_herramientas):
        """Genera la respuesta final incorporando los resultados de todas las herramientas"""
        salida = '[>] Generando respuesta final incorporando todos los resultados...✍️'
        self._enviar_a_consola(salida, 'info')
        print(f'\n{Fore.GREEN}{salida}{Style.RESET_ALL}')
        
        # Preparar el prompt final con todos los resultados de herramientas
        prompt_final = copy.deepcopy(self.original_prompt)
        
        info_consolidada = "Utiliza esta información proporcionada por las herramientas para responder al usuario:\n\n"
        for funcion, query, resultado in resultados_herramientas:
            info_consolidada += f"Resultados de {funcion} para '{query}':\n{resultado}\n\n"
        
        info_consolidada += "Inserta los enlaces e imágenes relevantes en tu respuesta y responde en completo español. Organiza la información de manera coherente y clara para el usuario."
        
        # Añadir un mensaje de asistente para mantener la alternancia de roles
        prompt_final.append({"role": "assistant", "content": "He recopilado toda la información necesaria de las herramientas."})
        prompt_final.append({"role": "user", "content": info_consolidada})

          # Generar la respuesta final con todos los resultados
        response_final = self.transmitir_response(model, prompt_final)
        
        salida_final = f'\n{Fore.GREEN}✍️FINAL {response_final}{Style.RESET_ALL}\n\n{Fore.BLUE}{Style.RESET_ALL}\n'
        print(salida_final)
        
        return response_final

    def transmitir_response(self, model, prompt):
        """Transmite la respuesta del modelo al socket"""
        response_completa = ''
        linea = ''        # Calcular tokens solo de la pregunta original del usuario
        # Buscar el último mensaje del usuario en el prompt original
        user_question = ""
        for message in reversed(self.original_prompt):
            if message['role'] == 'user':
                user_question = message['content']
                break
        
        tokensInput = user_question.encode()
        tokens = model.tokenize(tokensInput)
        total_user_tokens = len(tokens)
        total_assistant_tokens = 0          
        response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
            model=model,
            messages=prompt,
            socket=self.socket,
            max_tokens=1024,
            user_tokens=total_user_tokens,
            process_line_breaks=True,
            response_queue=self.response_queue,
            link_remover_func=self.eliminar_enlaces,
            stop_condition=lambda: self.assistant.stop_emit if self.assistant else False
        )        
        self.response_queue.put(None)        
        SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
        return response_completa

    def eliminar_enlaces(self, linea):
        regex_enlaces = r'\[?\b(?:https?://|www\.)\S+\b\]?|<\b(?:https?://|www\.)\S+\b>'
        linea_sin_enlaces = re.sub(regex_enlaces, ' enlace ', linea).replace('/', '')
        return self.eliminar_lineas_repetidas(linea_sin_enlaces).replace('#', '')

    def eliminar_lineas_repetidas(self, texto):
        regex_lineas = r'^=+$'
        return re.sub(regex_lineas, '', texto, flags=re.MULTILINE)

    def hablar_response(self):
        """Función para convertir texto a voz usando pyttsx3"""
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

    def extraer_urls(self, texto):
        """Extrae URLs de un texto para investigación adicional"""       
        patron_url = r'https?://\S+|www\.\S+'
        urls = re.findall(patron_url, texto)
        return urls
    
    def _get_available_tools_dict(self):
        """Obtiene un diccionario de herramientas disponibles desde el registry"""
        available_tools = {}
        for tool_name in self.tool_registry.list_tools():
            # Crear una función wrapper que use el registry para ejecutar la herramienta
            def tool_wrapper(query, name=tool_name):
                result = self.tool_registry.execute_tool(name, query)
                return result.data if result.success else f"Error: {result.error}"
            available_tools[tool_name] = tool_wrapper
        return available_tools
    
    def _get_tool_instructions(self):
        """Genera las instrucciones de herramientas disponibles para el modelo"""
        instructions = "Funciones disponibles:\n"
        for tool_name in self.tool_registry.list_tools():
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                instructions += f"[Funcion: '{tool_name}' , query: '{tool_info.get('description', 'consulta')}']\n"
        return instructions
