"""
@Author: Borja Otero Ferreira
Default Agent - Sistema de procesamiento de herramientas con lógica migrada de Cortex
Arquitectura modularizada siguiendo el patrón de lineal_agent y adaptive_agent
"""
import datetime
import queue
import threading
import os
from typing import Any, Optional, List, Tuple, Dict
from colorama import Fore, Style

try:
    import pyttsx3
except ImportError:
    pass

from app.utils.logger import logger
from dotenv import load_dotenv
from app.core.mcp_manager import mcp_manager

# Importar módulos del agente default
from .config import DefaultAgentConfig
from .default_need_analyzer import DefaultNeedAnalyzer
from .default_tool_executor import DefaultToolExecutor
from .default_response_generator import DefaultResponseGenerator  # Usar el ResponseGenerator estándar
from ..utils import get_available_tools_dict, safe_emit_status

load_dotenv()

# Configurar API keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
os.environ["YOUTUBE_API_KEY"] = YOUTUBE_API_KEY
os.environ["SERPER_API_KEY"] = SERPER_API_KEY


class DefaultAgent:
    """
    Sistema de procesamiento de herramientas con lógica migrada de Cortex
    Mantiene el comportamiento original pero con arquitectura modularizada
    """
    
    def __init__(self, prompt_o: Any, prompt: Any, response: str, model: Any, socket: Any, assistant: Any = None):
        # Inicializar propiedades básicas
        self.original_prompt = prompt_o
        self.prompt = prompt
        self.socket = socket
        self.assistant = assistant
        self.model = model
        self.fecha = datetime.datetime.now()
        self.engine_lock = threading.Lock()
        self.response_queue = queue.Queue()
        
        # Configuración del agente
        self.config = DefaultAgentConfig()
        
        # Inicializar el registry de herramientas
        self.mcp_registry = mcp_manager.registry
        mcp_manager.set_tools_enabled(True)  # Habilitar herramientas MCP siempre al crear el agente
        self._initialize_tools()
        
        # Verificar si las herramientas están habilitadas
        if hasattr(self, 'tools_manager') and not self.tools_manager.is_tools_enabled():
            logger.warning("Las herramientas están deshabilitadas globalmente.")
            self.final_response = self._generate_normal_response()
            return
        
        # Variables para el procesamiento de herramientas
        self.max_iterations = self.config.MAX_ITERATIONS
        self.output_console = ""
        
        # Inicializar componentes modulares del agente default
        self.need_analyzer = DefaultNeedAnalyzer(
            self.model, self.tools_manager, self.tool_registry, self.config
        )
        self.tool_executor = DefaultToolExecutor(
            self.tools_manager, self.tool_registry, self.socket, self.assistant, self.config
        )
        self.response_generator = DefaultResponseGenerator(
            self.model, self.socket, self.response_queue, self.original_prompt, self.assistant, self.config
        )
        
        # Iniciar el procesamiento del agente default
        logger.info("Inicializando Default Agent (migración de Cortex)")
        self.final_response = self._default_processing()
    
    def _initialize_tools(self):
        """Inicializar el registry de herramientas"""
        try:
            from tools.tool_registry import ToolRegistry
            from app.core.tools_manager import tools_manager
            from app.core.mcp_manager import mcp_manager

            # Usar el singleton de MCPRegistry
            self.tool_registry = mcp_manager
            self.tools_manager = tools_manager
            # Registrar herramientas MCP como disponibles en el mismo formato que las locales
            self.tools = get_available_tools_dict(self.tool_registry)
            logger.info(f"Default Agent: {len(self.tools)} tools available (incluyendo MCP)")

            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler

        except Exception as e:
            logger.error(f"Error initializing tools in default agent: {e}")
            self.tools = {}
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler

    def _default_processing(self) -> str:
        """Procesamiento principal del agente default (migración de Cortex)"""
        try:
            logger.info("Default Agent processing started")

            # Verificar si las herramientas están habilitadas globalmente
            tools_enabled = False
            if hasattr(self, 'tools_manager') and hasattr(self.tools_manager, 'is_tools_enabled'):
                tools_enabled = self.tools_manager.is_tools_enabled()
            if hasattr(self, 'tool_registry') and hasattr(self.tool_registry, 'is_tools_enabled'):
                tools_enabled = tools_enabled or self.tool_registry.is_tools_enabled()
            if not tools_enabled:
                logger.info("Las herramientas están deshabilitadas globalmente. Generando respuesta directa.")
                print(f"{Fore.YELLOW}🔧 Las herramientas están deshabilitadas globalmente.{Style.RESET_ALL}")
                safe_emit_status(self.socket, "Las herramientas están deshabilitadas. Generando respuesta directa.")
                return self._generate_normal_response()

            # Detectar todas las herramientas activas (locales y MCP)
            active_tools = set()
            # MCP
            if hasattr(self, 'tool_registry') and hasattr(self.tool_registry, 'get_active_tools'):
                mcp_activas = self.tool_registry.get_active_tools()
                logger.info(f"MCP activas: {mcp_activas}")
                active_tools.update(mcp_activas)
            # Locales
            if hasattr(self, 'tools_manager') and hasattr(self.tools_manager, 'get_active_tools'):
                locales_activas = self.tools_manager.get_active_tools()
                logger.info(f"Locales activas: {locales_activas}")
                active_tools.update(locales_activas)
            active_tools = [t for t in active_tools if t]  # Filtrar vacíos

            logger.info(f"Herramientas activas detectadas (final): {active_tools}")

            if not active_tools:
                logger.info("No hay herramientas activas seleccionadas (ni MCP ni locales). Generando respuesta directa.")
                print(f"{Fore.YELLOW}🔧 No hay herramientas activas seleccionadas (ni MCP ni locales).{Style.RESET_ALL}")
                safe_emit_status(self.socket, "No hay herramientas seleccionadas. Generando respuesta directa.")
                return self._generate_normal_response()

            # Paso 1: Determinar herramientas necesarias
            safe_emit_status(self.socket, "🧠 Analizando necesidades de herramientas...")
            herramientas_necesarias = self.need_analyzer.determinar_herramientas_necesarias(self.original_prompt)
            self.output_console = f' {herramientas_necesarias}'

            # Enviar pensamiento al frontend
            safe_emit_status(self.socket, self.output_console, 'pensamiento')

            # Paso 2: Procesar herramientas necesarias (detección iterativa y ejecución)
            safe_emit_status(self.socket, "🔧 Procesando herramientas detectadas...")
            processed_response, resultados_herramientas = self.tool_executor.process_tool_needs(
                herramientas_necesarias, self.model
            )

            # Paso 3: Generar respuesta final
            safe_emit_status(self.socket, "📝 Generando respuesta final...")

            # Convertir resultados al formato esperado por ResponseGenerator
            execution_results = self._convert_results_to_execution_format(resultados_herramientas)

            # Generar respuesta final usando el ResponseGenerator estándar
            final_response = self.response_generator.generar_respuesta_final(resultados_herramientas, self._safe_emit_status)

            # Paso 4: Mostrar estadísticas del proceso
            self._display_processing_stats(resultados_herramientas)

            logger.info("Default Agent processing completed")
            return final_response

        except Exception as e:
            logger.error(f"Error in Default Agent processing: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            safe_emit_status(self.socket, f"❌ Error en Default Agent: {e}")
            return self._generate_normal_response()

    def _convert_results_to_execution_format(self, resultados_herramientas: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """
        The function `_convert_results_to_execution_format` converts results from a default agent into a
        format expected by `ResponseGenerator`, including representing execution steps and calculating
        success rate.
        
        :param resultados_herramientas: The `resultados_herramientas` parameter is expected to be a list of
        tuples, where each tuple contains three elements:
        :type resultados_herramientas: List[Tuple[str, str, str]]
        :return: The function `_convert_results_to_execution_format` returns a dictionary containing
        information about the execution results of a set of tools. The dictionary includes keys such as
        'completed_steps', 'failed_steps', 'total_steps', 'execution_time', and 'success_rate'. The
        'completed_steps' and 'failed_steps' keys contain lists of `ExecutionStep` objects representing the
        steps that were successfully completed and the steps
        """
        """Convierte los resultados del default_agent al formato esperado por ResponseGenerator"""
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class ExecutionStep:
            """Representa un paso de ejecución"""
            description: str
            tool_name: str
            query: str
            result: Optional[str] = None
            error: Optional[str] = None
        
        execution_results = {
            'completed_steps': [],
            'failed_steps': [],
            'total_steps': len(resultados_herramientas),
            'execution_time': 0.0,
            'success_rate': 0.0
        }
        
        try:
            for funcion, consulta, resultado in resultados_herramientas:
                step = ExecutionStep(
                    description=f"Ejecutar {funcion}",
                    tool_name=funcion,
                    query=consulta,
                    result=resultado if resultado and not resultado.startswith("Error:") else None,
                    error=resultado if resultado and resultado.startswith("Error:") else None
                )
                
                if step.error:
                    execution_results['failed_steps'].append(step)
                else:
                    execution_results['completed_steps'].append(step)
            
            # Calcular tasa de éxito
            completed = len(execution_results['completed_steps'])
            total = execution_results['total_steps']
            execution_results['success_rate'] = (completed / total) if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error converting results to execution format: {e}")
        
        return execution_results

    def _generate_normal_response(self) -> str:
        """Generar respuesta normal sin herramientas"""
        return self.response_generator._generate_normal_response(self.model)
    
    def _display_processing_stats(self, resultados_herramientas: List[Tuple[str, str, str]]):
        """Mostrar estadísticas del procesamiento"""
        try:
            if not resultados_herramientas:
                return
            
            stats_msg = f"\n{Fore.CYAN}📊 Estadísticas del procesamiento:{Style.RESET_ALL}\n"
            stats_msg += f"   • Herramientas ejecutadas: {len(resultados_herramientas)}\n"
            
            # Contar herramientas únicas
            herramientas_unicas = set()
            for funcion, _, _ in resultados_herramientas:
                herramientas_unicas.add(funcion)
            
            stats_msg += f"   • Herramientas únicas utilizadas: {len(herramientas_unicas)}\n"
            stats_msg += f"   • Herramientas: {', '.join(herramientas_unicas)}\n"
            
            print(stats_msg)
            # logger.info(f"Estadísticas: {len(resultados_herramientas)} herramientas ejecutadas")
            safe_emit_status(self.socket, f"✅ Proceso completado: {len(resultados_herramientas)} herramientas ejecutadas")
            
        except Exception as e:
            logger.error(f"Error displaying processing stats: {e}")
    
    def _safe_emit_status(self, message: str, message_type: str = 'info'):
        """Enviar estado de manera segura usando SocketResponseHandler"""
        safe_emit_status(self.socket, message, message_type)


    
    def get_tools_info(self) -> dict:
        """Obtener información de herramientas disponibles"""
        try:
            return self.need_analyzer._get_available_tools_dict()
        except Exception as e:
            logger.error(f"Error getting tools info: {e}")
            return {}
    
    def get_processing_summary(self) -> dict:
        """Obtener resumen del procesamiento realizado"""
        try:
            summary = {
                "agent_type": "default",
                "timestamp": self.fecha.isoformat(),
                "original_prompt": self.original_prompt,
                "tools_available": len(self.tools) if hasattr(self, 'tools') else 0,
                "max_iterations": self.max_iterations,
                "output_console": self.output_console
            }
            
            # Agregar información de herramientas activas
            if hasattr(self, 'tools_manager'):
                summary["active_tools"] = self.tools_manager.get_active_tools()
                summary["tools_enabled"] = self.tools_manager.is_tools_enabled()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting processing summary: {e}")
            return {"error": str(e)}
