"""
@Author: Borja Otero Ferreira
Default Tool Executor - Ejecutor de herramientas para el agente default (migración de Cortex)
Maneja la ejecución individual de herramientas y la iteración de detección usando patrones JSON
"""
import re
import json
from typing import List, Tuple, Any, Set, Dict
from colorama import Fore, Style

from app.utils.logger import logger
from .config import DefaultAgentConfig
from ..utils import safe_emit_status


class DefaultToolExecutor:
    """
    Ejecutor de herramientas especializado para el agente default
    Migrado desde la lógica de Cortex
    """
    
    def __init__(self, tools_manager, tool_registry, socket, assistant, config: DefaultAgentConfig):
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
        self.socket = socket
        self.assistant = assistant
        self.config = config
        
    def process_tool_needs(self, response: str, model: Any) -> str:
        """
        Procesa la respuesta para detectar y usar herramientas, con posibilidad de iteración
        Migrado desde Cortex.process_tool_needs
        """
        print('Iniciando proceso iterativo de detección y uso de herramientas')
        logger.info('Iniciando proceso iterativo de detección y uso de herramientas')
        self._enviar_a_consola(f'💭 {response}', 'pensamiento')
        
        # Obtener solo herramientas ACTIVAS (habilitadas Y seleccionadas)
        active_tools = []
        if hasattr(self.tools_manager, 'get_active_tools'):
            active_tools = self.tools_manager.get_active_tools()
            
        # Si no hay herramientas activas, salir inmediatamente
        if not active_tools:
            mensaje = "No hay herramientas activas seleccionadas disponibles para usar."
            print(f"{Fore.YELLOW}{mensaje}{Style.RESET_ALL}")
            logger.warning(mensaje)
            self._enviar_a_consola(mensaje, 'info')
            return response
        
        herramientas_usadas = []
        resultados_herramientas = []
        iterations = 0
        current_response = response
        herramientas_no_disponibles = False
        
        while iterations < self.config.MAX_ITERATIONS:
            # Verificar si se debe detener la respuesta
            if self.assistant and self.assistant.stop_emit:
                print(f"{Fore.RED}🛑 Stop signal detected, breaking tool iterations{Style.RESET_ALL}")
                logger.warning("Stop signal detected, breaking tool iterations")
                self._enviar_a_consola("🛑 Process stopped by user", 'info')
                break
                
            iterations += 1
            print(f"\n{Fore.CYAN}[*] Iteración {iterations} de detección de herramientas{Style.RESET_ALL}")
            logger.info(f"[*] Iteración {iterations} de detección de herramientas")
            self._enviar_a_consola(f"[*] Iteración {iterations} de detección de herramientas", 'info')
            
            # Detectar coincidencias de herramientas usando JSON
            coincidencias = self._extraer_coincidencias_json(current_response)
            
            # Si no hay coincidencias, terminar el ciclo
            if not coincidencias:
                print(f"{Fore.GREEN}[*] No se detectaron más herramientas necesarias{Style.RESET_ALL}")
                logger.info("[*] No se detectaron más herramientas necesarias")
                self._enviar_a_consola("[*] No se detectaron más herramientas necesarias", 'info')
                break
                
            # Ejecutar las herramientas detectadas
            for funcion_texto, query_texto in coincidencias:
                # Verificar si se debe detener antes de ejecutar cada herramienta
                if self.assistant and self.assistant.stop_emit:
                    print(f"{Fore.RED}🛑 Stop signal detected during tool execution{Style.RESET_ALL}")
                    logger.warning("🛑 Stop signal detected during tool execution")
                    return "🛑 Process stopped by user"
                
                # Verificar si la herramienta está disponible y seleccionada
                herramienta_disponible = funcion_texto.lower().strip("'\" ") in [t.lower() for t in active_tools]
                if not herramienta_disponible:
                    herramientas_no_disponibles = True
                    
                if (funcion_texto, query_texto) not in herramientas_usadas:  # Evitar repetir exactamente la misma consulta
                    resultado = self._ejecutar_herramienta_individual(funcion_texto, query_texto)
                    resultados_herramientas.append((funcion_texto, query_texto, resultado))
                    herramientas_usadas.append((funcion_texto, query_texto))
            
            # Consultar al modelo para decidir si necesita más herramientas
            if herramientas_usadas:
                current_response = self._consultar_modelo_para_decision(model, resultados_herramientas)
        
        # Si se alcanzó el máximo de iteraciones, informar
        if iterations >= self.config.MAX_ITERATIONS:
            mensaje = f"Se alcanzó el máximo de iteraciones ({self.config.MAX_ITERATIONS}). Generando respuesta final."
            print(f"{Fore.YELLOW}{mensaje}{Style.RESET_ALL}")
            logger.warning(mensaje)
            self._enviar_a_consola(mensaje, 'info')
        
        # Si se intentó usar herramientas no disponibles, añadir un mensaje final
        if herramientas_no_disponibles:
            mensaje = "Se intentó usar herramientas que no están seleccionadas o disponibles."
            print(f"{Fore.YELLOW}{mensaje}{Style.RESET_ALL}")
            logger.warning(mensaje)
            self._enviar_a_consola(mensaje, 'info')
            
            # Añadir un mensaje explícito a los resultados
            resultados_herramientas.append(
                ("sistema", "aviso", 
                 "Algunas herramientas solicitadas no están seleccionadas. Por favor, utiliza solo las herramientas disponibles.")
            )
        
        return current_response, resultados_herramientas
    
    def _extraer_coincidencias_json(self, response: str) -> List[Tuple[str, str]]:
        """Extraer coincidencias de herramientas usando detección JSON"""
        tool_calls = []
        
        try:
            # Buscar bloques JSON válidos en la respuesta
            json_blocks = self._extract_json_blocks(response)
            
            for json_block in json_blocks:
                try:
                    data = json.loads(json_block)
                    parsed_calls = self._parse_json_tool_calls(data)
                    tool_calls.extend(parsed_calls)
                except json.JSONDecodeError:
                    continue
            
            # Si no se encontraron llamadas JSON válidas, buscar patrones básicos
            if not tool_calls:
                tool_calls = self._extract_basic_patterns(response)
            
            # Filtrar herramientas válidas
            valid_calls = []
            active_tools = self.tools_manager.get_active_tools() if hasattr(self.tools_manager, 'get_active_tools') else []
            
            for tool_name, query in tool_calls:
                if tool_name.lower() in [t.lower() for t in active_tools]:
                    valid_calls.append((tool_name, query))
                else:
                    logger.warning(f"Herramienta '{tool_name}' no está en las herramientas activas")
            
            return valid_calls
            
        except Exception as e:
            logger.error(f"Error extrayendo coincidencias JSON: {e}")
            return []
    
    def _extract_json_blocks(self, text: str) -> List[str]:
        """Extraer bloques JSON válidos del texto"""
        json_blocks = []
        
        # Buscar patrones JSON comunes
        patterns = [
            r'\{[^{}]*"tool"[^{}]*\}',
            r'\{[^{}]*"function"[^{}]*\}',
            r'\{[^{}]*"name"[^{}]*"query"[^{}]*\}',
            r'\{[^{}]*"herramienta"[^{}]*\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            json_blocks.extend(matches)
        
        # Buscar arrays JSON
        array_pattern = r'\[[^\[\]]*\{[^{}]*\}[^\[\]]*\]'
        array_matches = re.findall(array_pattern, text, re.IGNORECASE | re.DOTALL)
        json_blocks.extend(array_matches)
        
        return json_blocks
    
    def _parse_json_tool_calls(self, data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Parsear llamadas de herramientas desde datos JSON"""
        tool_calls = []
        
        try:
            # Caso 1: Objeto único con herramienta
            if isinstance(data, dict):
                tool_call = self._parse_single_tool_call(data)
                if tool_call:
                    tool_calls.append(tool_call)
            
            # Caso 2: Array de herramientas
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        tool_call = self._parse_single_tool_call(item)
                        if tool_call:
                            tool_calls.append(tool_call)
                            
        except Exception as e:
            logger.error(f"Error parseando llamadas de herramientas JSON: {e}")
        
        return tool_calls
    
    def _parse_single_tool_call(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Parsear una sola llamada de herramienta desde JSON"""
        tool_name = None
        query = None
        
        # Buscar nombre de herramienta
        for key in ['tool', 'function', 'name', 'herramienta', 'funcion']:
            if key in data:
                tool_name = str(data[key]).strip()
                break
        
        # Buscar query/consulta
        for key in ['query', 'consulta', 'parameters', 'args', 'input']:
            if key in data:
                if isinstance(data[key], str):
                    query = data[key].strip()
                elif isinstance(data[key], dict) and 'query' in data[key]:
                    query = str(data[key]['query']).strip()
                elif isinstance(data[key], dict) and 'consulta' in data[key]:
                    query = str(data[key]['consulta']).strip()
                else:
                    query = str(data[key]).strip()
                break
        
        if tool_name and query:
            return (tool_name, query)
        
        return None
    
    def _extract_basic_patterns(self, response: str) -> List[Tuple[str, str]]:
        """Extraer patrones básicos si no se encuentra JSON válido"""
        tool_calls = []
        
        # Patrones básicos simplificados
        basic_patterns = [
            r'\[Funcion:\s*[\'"]([^\'"]+)[\'"]\s*,\s*query:\s*[\'"]([^\'"]+)[\'"]\]',
            r'\{\s*[\'"]tool[\'"]:\s*[\'"]([^\'"]+)[\'"],\s*[\'"]query[\'"]:\s*[\'"]([^\'"]+)[\'"]\s*\}',
            r'herramienta[:\s]+[\'"]([^\'"]+)[\'"][,\s]+consulta[:\s]+[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in basic_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    tool_calls.append((match[0], match[1]))
        
        return tool_calls
    
    def _ejecutar_herramienta_individual(self, funcion_texto: str, query_texto: str) -> str:
        """Ejecutar una herramienta individual"""
        # Verificar si se debe detener antes de ejecutar la herramienta
        if self.assistant and self.assistant.stop_emit:
            print(f"{Fore.RED}Stop signal detected before tool execution{Style.RESET_ALL}")
            logger.warning("Stop signal detected before tool execution")
            return "Process stopped by user"
            
        print("")
        funcion_texto = funcion_texto.replace("'", "")
        query_texto = query_texto.replace("'", "").split(',') if 'cripto_price' in funcion_texto else query_texto
        
        print(f'\n{Fore.GREEN}[->] Usando {funcion_texto} con consulta {query_texto}...{Style.RESET_ALL}')
        logger.info(f'[->] Usando {funcion_texto} con consulta {query_texto}...')
        self._enviar_a_consola(f'[->] Usando {funcion_texto} con consulta {query_texto}...', 'info')
        
        resultado_herramienta = self.ejecutar_herramienta(funcion_texto, query_texto)
        print(f'{Fore.YELLOW}[!] Eureka!:{Style.RESET_ALL}\n{Fore.MAGENTA}{resultado_herramienta}{Style.RESET_ALL}')
        # No loggear resultado_herramienta aquí para evitar problemas de codificación
        return resultado_herramienta
    
    def ejecutar_herramienta(self, nombre_herramienta: str, consulta: Any) -> str:
        """Ejecuta una herramienta usando el registry"""
        try:
            # Verificar si las herramientas están habilitadas globalmente
            if hasattr(self.tools_manager, 'is_tools_enabled') and not self.tools_manager.is_tools_enabled():
                error_msg = f'Las herramientas están deshabilitadas globalmente'
                print(f"{Fore.YELLOW}{error_msg}{Style.RESET_ALL}")
                logger.warning(error_msg)
                return error_msg
                
            # Verificar si la herramienta está activa (habilitada y seleccionada)
            if hasattr(self.tools_manager, 'is_tool_active') and not self.tools_manager.is_tool_active(nombre_herramienta):
                # Comprobar si está en las herramientas seleccionadas
                selected_tools = self.tools_manager.get_selected_tools()
                if nombre_herramienta not in selected_tools:
                    error_msg = f'La herramienta {nombre_herramienta} no está seleccionada por el usuario'
                else:
                    error_msg = f'La herramienta {nombre_herramienta} no está disponible actualmente'
                
                print(f"{Fore.YELLOW}{error_msg}{Style.RESET_ALL}")
                logger.warning(error_msg)
                self._enviar_a_consola(error_msg, 'info')
                return error_msg
                
            # Usar el registry para ejecutar la herramienta
            resultado_ejecucion = self.tool_registry.execute_tool(nombre_herramienta, consulta)
            
            # Verificar si la ejecución fue exitosa
            if not resultado_ejecucion.success:
                error_msg = f'Error usando la herramienta {nombre_herramienta}: {resultado_ejecucion.error}'
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                logger.error(error_msg)
                self._enviar_a_consola(error_msg, 'error')
                return error_msg
            
            # Extraer los datos del resultado
            resultado_herramienta = resultado_ejecucion.data
            
            # Manejo especial para herramientas que devuelven múltiples valores
            if nombre_herramienta == "video_search_tool" and isinstance(resultado_herramienta, tuple):
                resultado_herramienta, ids = resultado_herramienta
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_utilities_data(self.socket, {"ids": ids})
            
            # Asegurar que el resultado sea siempre un string antes de enviar por socket
            if not isinstance(resultado_herramienta, str):
                resultado_herramienta = str(resultado_herramienta)
            
            self._enviar_a_consola(resultado_herramienta, 'tool')
            return resultado_herramienta
            
        except Exception as e:
            error_msg = f'Error usando la herramienta {nombre_herramienta}: {e}'
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._enviar_a_consola(error_msg, 'error')
            return error_msg
    
    def _consultar_modelo_para_decision(self, model: Any, resultados_herramientas: List[tuple]) -> str:
        """Consultar al modelo para decidir si necesita más herramientas"""
        try:
            # Crear prompt para consultar al modelo
            decision_prompt = self._crear_prompt_decision(resultados_herramientas)
            
            # Generar respuesta del modelo 
            response_content = ""
            for chunk in model.create_chat_completion(messages=decision_prompt, max_tokens=8192, stream=True):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        response_content += delta['content']
            
            return response_content.strip()
            
        except Exception as e:
            logger.error(f"Error consulting model for decision: {e}")
            return f"Error en consulta al modelo: {e}"
    
    def _crear_prompt_decision(self, resultados_herramientas: List[tuple]) -> List[dict]:
        """Crear prompt para que el modelo decida si necesita más herramientas"""
        # Crear información de herramientas disponibles
        herramientas_info = "HERRAMIENTAS DISPONIBLES:\n"
        if hasattr(self.tools_manager, 'get_active_tools'):
            active_tools = self.tools_manager.get_active_tools()
            for tool in active_tools:
                herramientas_info += f"- {tool}\n"
        
        # Crear información de resultados obtenidos
        resultados_info = "\nRESULTADOS OBTENIDOS:\n"
        for funcion, query, resultado in resultados_herramientas:
            resultados_info += f"Herramienta: {funcion}\nConsulta: {query}\nResultado: {resultado}\n---\n"
        
        # Crear instrucción para el modelo
        instruccion = """
Basándote en los resultados obtenidos y las herramientas disponibles, determina si necesitas ejecutar más herramientas.
Si necesitas más herramientas, responde con formato JSON:
{"tool": "nombre_herramienta", "query": "consulta"}

Para múltiples herramientas usa un array:
[{"tool": "herramienta1", "query": "consulta1"}, {"tool": "herramienta2", "query": "consulta2"}]

Si no necesitas más herramientas, genera una respuesta final integrando toda la información obtenida.
"""
        
        decision_prompt = [
            {"role": "system", "content": "Eres un asistente que decide si necesita ejecutar más herramientas o generar una respuesta final."},
            {"role": "user", "content": f"Consulta original: {getattr(self.assistant, 'original_prompt', 'No disponible')}"},
        ]
        
        decision_prompt.append({"role": "assistant", "content": "He ejecutado las herramientas solicitadas y tengo los resultados."})
        decision_prompt.append({"role": "user", "content": herramientas_info + resultados_info + instruccion})
        
        return decision_prompt
    
    def _enviar_a_consola(self, mensaje: str, rol: str):
        """Enviar mensaje a consola usando SocketResponseHandler"""
        if self.config.ENABLE_SOCKET_EMISSION:
            try:
                # Asegurar que el mensaje sea siempre un string
                if not isinstance(mensaje, str):
                    mensaje = str(mensaje)
                
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_console_output(self.socket, mensaje, rol)
            except Exception as e:
                logger.error(f"Error emitting to socket: {e}")
                logger.error(f"Message type: {type(mensaje)}, Message: {mensaje}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
