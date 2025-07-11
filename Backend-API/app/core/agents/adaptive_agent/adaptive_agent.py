"""
@Author: Borja Otero Ferreira
Agente Adaptativo - Sistema de procesamiento de herramientas con planificación deliberativa
Piensa paso a paso como un humano, ajustando el plan dinámicamente
"""
import datetime
import queue
import threading
import os
from typing import Any, Optional, Dict
from colorama import Fore, Style

try:
    import pyttsx3
except ImportError:
    pass

from app.utils.logger import logger
from dotenv import load_dotenv

# Importar módulos del agente
from ..models import TaskPlan
from ..task_analyzer import TaskAnalyzer
from .adaptive_planner import AdaptiveTaskPlanner
from ..response_generator import ResponseGenerator
from ..utils import get_available_tools_dict, safe_emit_status
from .config import AdaptiveAgentConfig
from app.core.socket_handler import SocketResponseHandler

load_dotenv()

# Configurar API keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
os.environ["YOUTUBE_API_KEY"] = YOUTUBE_API_KEY
os.environ["SERPER_API_KEY"] = SERPER_API_KEY


class AdaptiveAgent:
    """
    Sistema de procesamiento de herramientas con planificación adaptativa y deliberativa
    Piensa paso a paso como un humano, reflexionando y ajustando dinámicamente
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
        
        # Configuración específica del agente adaptativo
        self.config = AdaptiveAgentConfig()
        self.max_iterations = self.config.MAX_ADAPTIVE_ITERATIONS
        self.reflection_enabled = self.config.REFLECTION_ENABLED
        
        # Inicializar el registry de herramientas
        self._initialize_tools()
        
        # Verificar si las herramientas están habilitadas
        if hasattr(self, 'tools_manager') and not self.tools_manager.is_tools_enabled():
            logger.warning("Las herramientas están deshabilitadas globalmente.")
            self.final_response = self._generate_normal_response()
            return
        
        # Variables para el procesamiento adaptativo
        self.current_plan: Optional[TaskPlan] = None
        self.execution_context = {}  # Contexto acumulado durante la ejecución
        
        # Inicializar componentes modulares del agente adaptativo
        self.task_analyzer = TaskAnalyzer(self.model, self.tools_manager, self.tool_registry)
        self.adaptive_planner = AdaptiveTaskPlanner(self.model, self.tools_manager, self.tool_registry, self.socket, self.assistant)
        self.response_generator = ResponseGenerator(self.model, self.socket, self.response_queue, self.original_prompt, self.assistant)
        
        # Iniciar el procesamiento adaptativo
        logger.info("Inicializando Agente Adaptativo")
        self.final_response = self._adaptive_processing()
    
    def _initialize_tools(self):
        """Inicializar el registry de herramientas para el agente adaptativo"""
        try:
            from tools.tool_registry import ToolRegistry
            from app.core.tools_manager import tools_manager
            
            if hasattr(tools_manager, '_registry') and tools_manager._registry:
                logger.info("Adaptive Agent: Using existing tool registry from ToolsManager")
                self.tool_registry = tools_manager._registry
            else:
                logger.info("Adaptive Agent: Creating new ToolRegistry")
                self.tool_registry = ToolRegistry()
                try:
                    self.tool_registry.discover_tools()
                except Exception as e:
                    logger.error(f"Error during tool discovery in adaptive agent: {e}")
                tools_manager.initialize_registry(self.tool_registry)
            
            self.tools_manager = tools_manager
            self.tools = get_available_tools_dict(self.tool_registry)
            logger.info(f"Adaptive Agent: {len(self.tools)} tools available")
            
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler
            
        except Exception as e:
            logger.error(f"Error initializing tools in adaptive agent: {e}")
            self.tools = {}
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler

    def _adaptive_processing(self) -> str:
        """Procesamiento con planificación adaptativa y deliberativa"""
        try:
            # Paso 1: Analizar la tarea del usuario
            self._safe_emit_status("🧠 Analizando la tarea solicitada...", 'info')
            task_analysis = self.task_analyzer.analyze_user_task(self.original_prompt)
            
            if not task_analysis:
                self._safe_emit_status("⚠️ No se pudo analizar la tarea. Generando respuesta directa...")
                return self._generate_normal_response()
            
            # Paso 2: Ejecutar planificación adaptativa (el planificador ya envía la respuesta por streaming)
            self._safe_emit_status("🎯 Iniciando planificación", 'info')
            execution_results = self.adaptive_planner.run_adaptive_plan(
                task_analysis, 
                self.original_prompt, 
                self._safe_emit_status
            )
            # Paso 3: Emitir la señal de finalización tras el streaming
            from app.core.socket_handler import SocketResponseHandler
            SocketResponseHandler.emit_finalization_signal(self.socket)
            return execution_results.get('final_prompt', '')
        except Exception as e:
            from ..utils import clean_error_message
            error_clean = clean_error_message(str(e))
            logger.error(f"Error en procesamiento adaptativo: {error_clean}")
            self._safe_emit_status(f"❌ Error en Agente Adaptativo: {error_clean}")
            return self._generate_normal_response()

    def _display_adaptive_summary(self, execution_results: Dict[str, Any]):
        """Muestra un resumen de la experiencia adaptativa"""
        try:
            summary_text = "\n🎯 **RESUMEN**\n\n"
            
            # Información sobre adaptaciones
            adaptations = execution_results.get('adaptations_made', 0)
            if adaptations > 0:
                summary_text += f"🧠 **Reflexiones realizadas:** {adaptations}\n"
                summary_text += f"💡 **Adaptaciones dinámicas:** El agente ajustó su estrategia {adaptations} veces\n"
            
            # Información sobre el proceso de pensamiento
            reflections = execution_results.get('reflections', [])
            if reflections:
                last_reflection = reflections[-1] if reflections else {}
                confidence = last_reflection.get('confidence_level', 'desconocido')
                summary_text += f"🎭 **Nivel de confianza final:** {confidence}\n"
            
            # Información sobre eficiencia
            success_rate = execution_results.get('success_rate', 0)
            if success_rate > 0.8:
                summary_text += f"✅ **Eficiencia alta:** {success_rate:.1%} de pasos exitosos\n"
            elif success_rate > 0.5:
                summary_text += f"⚡ **Eficiencia media:** {success_rate:.1%} de pasos exitosos\n"
            else:
                summary_text += f"🔄 **Proceso exploratorio:** {success_rate:.1%} de pasos exitosos\n"
            
            # Tiempo total
            execution_time = execution_results.get('execution_time', 0)
            summary_text += f"⏱️ **Tiempo de procesamiento:** {execution_time:.1f} segundos\n"

            
            self._safe_emit_status(summary_text)
            
        except Exception as e:
            logger.error(f"Error mostrando resumen adaptativo: {e}")

    def _generate_normal_response(self) -> str:
        """Genera una respuesta normal sin herramientas"""
        return self.response_generator.generate_normal_response()

    def _emit_status(self, message: str):
        """Emite un mensaje de estado al socket"""
        print(f"{Fore.MAGENTA}[ADAPTATIVO]{Style.RESET_ALL} {message}")
        logger.info(f"[ADAPTATIVO] {message}")
        SocketResponseHandler.emit_console_output(self.socket, message, 'info')

    def _safe_emit_status(self, message: str, type: str = 'info'):
        """Emite mensaje de estado de forma segura, manejando errores de encoding"""
        SocketResponseHandler.emit_console_output(self.socket, message,  type)


    def get_response(self) -> str:
        """Obtiene la respuesta final"""
        return getattr(self, 'final_response', '')

    def get_agent_info(self) -> Dict[str, Any]:
        """Obtiene información sobre el agente adaptativo"""
        config = AdaptiveAgentConfig.get_config()
        return {
            "type": "adaptive",
            "name": "Agente Adaptativo",
            "description": "Planificación incremental y deliberativa paso a paso",
            "features": [
                "Reflexión continua",
                "Adaptación dinámica",
                "Pensamiento contextual",
                "Optimización de recursos"
            ],
            "config": config,
            "tools_available": len(self.tools) if hasattr(self, 'tools') else 0,
            "max_iterations": self.max_iterations,
            "reflection_enabled": self.reflection_enabled
        }

    def get_execution_context(self) -> Dict[str, Any]:
        """Obtiene el contexto de ejecución actual"""
        return {
            "current_plan": self.current_plan.task_description if self.current_plan else None,
            "execution_context": self.execution_context,
            "planner_context": getattr(self.adaptive_planner, 'execution_context', {}),
            "last_processed": self.fecha.isoformat()
        }

    def update_config(self, **kwargs):
        """Actualiza la configuración del agente adaptativo"""
        if 'max_iterations' in kwargs:
            self.max_iterations = kwargs['max_iterations']
            AdaptiveAgentConfig.MAX_ADAPTIVE_ITERATIONS = kwargs['max_iterations']
        
        if 'reflection_enabled' in kwargs:
            self.reflection_enabled = kwargs['reflection_enabled']
            AdaptiveAgentConfig.REFLECTION_ENABLED = kwargs['reflection_enabled']
        
        if 'reflection_verbosity' in kwargs:
            AdaptiveAgentConfig.set_reflection_verbosity(kwargs['reflection_verbosity'])
        
        logger.info(f"Configuración del agente adaptativo actualizada: {kwargs}")

    def __del__(self):
        """Destructor para limpiar recursos del agente adaptativo"""
        try:
            if hasattr(self, 'response_queue'):
                # Limpiar la cola de respuestas de forma segura
                try:
                    while not self.response_queue.empty():
                        try:
                            self.response_queue.get_nowait()
                        except:
                            break
                except:
                    pass
            
            # Limpiar referencias específicas del agente adaptativo
            if hasattr(self, 'adaptive_planner'):
                self.adaptive_planner = None
            if hasattr(self, 'execution_context'):
                self.execution_context.clear()
            if hasattr(self, 'tool_registry'):
                self.tool_registry = None
            if hasattr(self, 'tools_manager'):
                self.tools_manager = None
            if hasattr(self, 'socket'):
                self.socket = None
            if hasattr(self, 'config'):
                self.config = None
            
        except Exception:
            pass
