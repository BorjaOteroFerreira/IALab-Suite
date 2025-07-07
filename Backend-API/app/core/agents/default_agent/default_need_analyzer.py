"""
@Author: Borja Otero Ferreira
Default Need Analyzer - Analizador de necesidades de herramientas para el agente default
Migrado desde la lógica de determinación de herramientas de Cortex con formato JSON
"""
import copy
from typing import Any, List, Dict
from colorama import Fore, Style

from app.utils.logger import logger
from .config import DefaultAgentConfig


class DefaultNeedAnalyzer:
    """
    Analizador de necesidades de herramientas para el agente default
    Migrado desde Cortex._determinar_herramientas_necesarias con formato JSON
    """
    
    def __init__(self, model, tools_manager, tool_registry, config: DefaultAgentConfig):
        self.model = model
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
        self.config = config
    
    def determinar_herramientas_necesarias(self, prompt_original) -> str:
        """
        Determina qué herramientas necesita usando el modelo con formato JSON
        Migrado desde Cortex._determinar_herramientas_necesarias
        """
        try:
            logger.info("Determinando herramientas necesarias usando formato JSON")
            
            # Verificar si hay herramientas activas disponibles
            active_tools = []
            if hasattr(self.tools_manager, 'get_active_tools'):
                active_tools = self.tools_manager.get_active_tools()
                
            if not active_tools:
                logger.warning("No hay herramientas activas disponibles para usar")
                return "No hay herramientas activas disponibles"
            
            # Extraer el contenido del prompt si es una lista
            if isinstance(prompt_original, list):
                # Buscar el último mensaje del usuario
                user_content = ""
                for message in reversed(prompt_original):
                    if message.get('role') == 'user':
                        user_content = message.get('content', '')
                        break
                prompt_text = user_content
            else:
                prompt_text = str(prompt_original)
            
            # Crear prompt para determinar herramientas usando el registry
            base_instructions = """
TU PRINCIPAL OBJETIVO ES DETERMINAR QUE HERRAMIENTA NECESITAS
"""
            
            # Obtener las instrucciones dinámicas de herramientas SOLO para herramientas activas
            tool_instructions = self._get_tool_instructions()
            
            additional_instructions = """
responde unicamente con la o las herramientas a lanzar usando formato JSON, ejemplo: 
supongamos que necesitas buscar el tiempo en internet , contestas: 
{"tool": "buscar_en_internet", "query": "tiempo proximos dias"}
Para múltiples herramientas usa un array:
[{"tool": "buscar_en_internet", "query": "noticias"}, {"tool": "video_search_tool", "query": "tutoriales"}]
Asegurate de que utilizas la sintaxis JSON correcta.
Puedes usar mas de una herramienta si lo necesitas.
Debes contestar solo con el JSON de las funciones que usarias sin texto antes ni despues
IMPORTANTE: Sólo puedes usar las herramientas listadas arriba. No uses ninguna otra herramienta.
SIEMPRE DEBES RESPONDER EN ESPAÑOL.
"""
            
            # Construir el prompt completo
            instrucciones_herramientas = base_instructions + tool_instructions + additional_instructions
            
            # Crear una copia del prompt original y modificar el mensaje del sistema
            if isinstance(prompt_original, list):
                prompt_herramientas = copy.deepcopy(prompt_original)
                if prompt_herramientas and prompt_herramientas[0]['role'] == 'system':
                    prompt_herramientas[0]['content'] = instrucciones_herramientas
                else:
                    prompt_herramientas.insert(0, {"role": "system", "content": instrucciones_herramientas})
            else:
                prompt_herramientas = [
                    {"role": "system", "content": instrucciones_herramientas},
                    {"role": "user", "content": prompt_text}
                ]
            
            # Generar respuesta 
            response_content = ""
            for chunk in self.model.create_chat_completion(messages=prompt_herramientas, max_tokens=200, stream=True):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        response_content += delta['content']
            
            print(f'\n{Fore.BLUE}🧠 Determinando herramientas necesarias\n💭 {response_content}{Style.RESET_ALL}')
            logger.info(f"Herramientas determinadas (JSON): {response_content[:200]}...")
            return response_content.strip()
            
        except Exception as e:
            logger.error(f"Error determinando herramientas necesarias: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error en análisis: {e}"
    
    def _get_tool_instructions(self) -> str:
        """
        Obtiene las instrucciones dinámicas de herramientas para herramientas activas
        Migrado desde Cortex._get_tool_instructions
        """
        try:
            tool_instructions = "\n## HERRAMIENTAS DISPONIBLES:\n"
            
            # Obtener solo herramientas activas
            active_tools = []
            if hasattr(self.tools_manager, 'get_active_tools'):
                active_tools = self.tools_manager.get_active_tools()
            
            if not active_tools:
                return "\n## No hay herramientas activas disponibles\n"
            
            # Generar instrucciones para cada herramienta activa
            for tool_name in active_tools:
                try:
                    # Obtener información de la herramienta del registry
                    if hasattr(self.tool_registry, 'get_tool_info'):
                        tool_info = self.tool_registry.get_tool_info(tool_name)
                        if tool_info:
                            tool_instructions += f"\n### {tool_name}\n"
                            tool_instructions += f"- **Descripción**: {tool_info.get('description', 'Sin descripción')}\n"
                            tool_instructions += f"- **Uso JSON**: {{\"tool\": \"{tool_name}\", \"query\": \"tu_consulta\"}}\n"
                        else:
                            # Información básica si no hay detalles específicos
                            tool_instructions += f"\n### {tool_name}\n"
                            tool_instructions += f"- **Uso JSON**: {{\"tool\": \"{tool_name}\", \"query\": \"tu_consulta\"}}\n"
                    else:
                        # Fallback si no hay get_tool_info
                        tool_instructions += f"\n### {tool_name}\n"
                        tool_instructions += f"- **Uso JSON**: {{\"tool\": \"{tool_name}\", \"query\": \"tu_consulta\"}}\n"
                        
                except Exception as e:
                    logger.error(f"Error getting info for tool {tool_name}: {e}")
                    # Continuar con la siguiente herramienta
                    continue
            
            return tool_instructions
            
        except Exception as e:
            logger.error(f"Error getting tool instructions: {e}")
            return "\n## Error obteniendo instrucciones de herramientas\n"
    
    def _get_available_tools_dict(self) -> Dict[str, Any]:
        """
        Obtiene un diccionario de herramientas disponibles
        Migrado desde Cortex._get_available_tools_dict
        """
        try:
            tools_dict = {}
            
            # Obtener herramientas activas
            if hasattr(self.tools_manager, 'get_active_tools'):
                active_tools = self.tools_manager.get_active_tools()
                
                for tool_name in active_tools:
                    try:
                        if hasattr(self.tool_registry, 'get_tool_info'):
                            tool_info = self.tool_registry.get_tool_info(tool_name)
                            tools_dict[tool_name] = tool_info or {"name": tool_name}
                        else:
                            tools_dict[tool_name] = {"name": tool_name}
                    except Exception as e:
                        logger.error(f"Error getting info for tool {tool_name}: {e}")
                        tools_dict[tool_name] = {"name": tool_name}
            
            return tools_dict
            
        except Exception as e:
            logger.error(f"Error getting available tools dict: {e}")
            return {}
