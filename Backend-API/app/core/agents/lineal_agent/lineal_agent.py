"""
@Author: Borja Otero Ferreira
Agente Autónomo - Sistema de procesamiento de herramientas con planificación automática
Detecta tareas, planifica pasos y ejecuta de forma autónoma.
"""
import datetime
import queue
import threading
import os
from typing import Any, Optional
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
from ..task_planner import TaskPlanner
from ..task_executor import TaskExecutor
from ..response_generator import ResponseGenerator
from ..utils import get_available_tools_dict, safe_emit_status

load_dotenv()

# Configurar API keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
os.environ["YOUTUBE_API_KEY"] = YOUTUBE_API_KEY
os.environ["SERPER_API_KEY"] = SERPER_API_KEY

class LinealAgent:
    """
    Sistema de procesamiento de herramientas con planificación tradicional
    Genera un plan completo al inicio y lo ejecuta secuencialmente
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
        
        # Inicializar el registry de herramientas
        self._initialize_tools()
        
        # Verificar si las herramientas están habilitadas
        if hasattr(self, 'tools_manager') and not self.tools_manager.is_tools_enabled():
            logger.warning("🔧 Las herramientas están deshabilitadas globalmente.")
            self.final_response = self._generate_normal_response()
            return
        
        # Variables para el procesamiento tradicional
        self.current_plan: Optional[TaskPlan] = None
        self.max_planning_iterations = 5
        self.max_execution_iterations = 10
        
        # Inicializar componentes modulares del agente tradicional
        self.task_analyzer = TaskAnalyzer(self.model, self.tools_manager, self.tool_registry)
        self.task_planner = TaskPlanner(self.model, self.tools_manager, self.tool_registry)
        self.task_executor = TaskExecutor(self.tools_manager, self.tool_registry, self.socket, self.assistant, self.max_execution_iterations)
        self.response_generator = ResponseGenerator(self.model, self.socket, self.response_queue, self.original_prompt, self.assistant)
        
        # Iniciar el procesamiento tradicional
        logger.info("📋 Inicializando Agente Tradicional")
        self.final_response = self._traditional_processing()
    
    def _initialize_tools(self):
        """Inicializar el registry de herramientas"""
        try:
            from tools.tool_registry import ToolRegistry
            from app.core.tools_manager import tools_manager
            
            if hasattr(tools_manager, '_registry') and tools_manager._registry:
                logger.info("🔧 Using existing tool registry from ToolsManager")
                self.tool_registry = tools_manager._registry
            else:
                logger.info("🔧 Creating new ToolRegistry in agent")
                self.tool_registry = ToolRegistry()
                try:
                    self.tool_registry.discover_tools()
                except Exception as e:
                    logger.error(f"Error during tool discovery: {e}")
                tools_manager.initialize_registry(self.tool_registry)
            
            self.tools_manager = tools_manager
            self.tools = get_available_tools_dict(self.tool_registry)
            logger.info(f"🔧 Traditional Agent: {len(self.tools)} tools available")
            
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler
            
        except Exception as e:
            logger.error(f"Error initializing tools in traditional agent: {e}")
            self.tools = {}
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler

    def _traditional_processing(self) -> str:
        """Procesamiento tradicional con plan rígido completo"""
        try:
            # Paso 1: Analizar la tarea del usuario
            self._safe_emit_status("🧠 Analizando la tarea solicitada...")
            task_analysis = self.task_analyzer.analyze_user_task(self.original_prompt)
            
            if not task_analysis:
                self._safe_emit_status("⚠️ No se pudo analizar la tarea. Generando respuesta directa...")
                return self._generate_normal_response()
            
            # Paso 2: Crear plan de ejecución completo
            self._safe_emit_status("📋 Creando plan de ejecución completo...")
            self.current_plan = self.task_planner.create_execution_plan(task_analysis, self.original_prompt)
            
            if not self.current_plan or not self.current_plan.steps:
                self._safe_emit_status("❌ No se pudo crear un plan de ejecución válido")
                return self._generate_normal_response()
            
            # Paso 3: Mostrar plan completo al usuario
            self.task_planner.display_execution_plan(self.current_plan, self._safe_emit_status)
            
            # Paso 4: Ejecutar el plan completo
            self._safe_emit_status("🚀 Ejecutando plan de tareas...")
            execution_results = self.task_executor.execute_plan(self.current_plan, self._safe_emit_status)
            
            # Paso 5: Generar respuesta final
            self._safe_emit_status("📝 Generando respuesta final...")
            final_response = self.response_generator.generate_final_response(execution_results, self._safe_emit_status)
            
            # Paso 6: Mostrar estadísticas
            self.task_executor.display_execution_stats(execution_results, self._safe_emit_status)
            
            
            return final_response
            
        except Exception as e:
            from .utils import clean_error_message
            error_clean = clean_error_message(str(e))
            logger.error(f"Error en procesamiento tradicional: {error_clean}")
            self._safe_emit_status(f"❌ Error en Agente Tradicional: {error_clean}")
            return self._generate_normal_response()

    def _generate_normal_response(self) -> str:
        """Genera una respuesta normal sin herramientas"""
        return self.response_generator.generate_normal_response()

    def _emit_status(self, message: str):
        """Emite un mensaje de estado al socket"""
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
        logger.info(message)
        from app.core.socket_handler import SocketResponseHandler
        SocketResponseHandler.emit_console_output(self.socket, message, 'info')

    def _safe_emit_status(self, message: str):
        """Emite mensaje de estado de forma segura, manejando errores de encoding"""
        safe_emit_status(self.socket, message, self._emit_status)

    def get_response(self) -> str:
        """Obtiene la respuesta final"""
        return getattr(self, 'final_response', '')

    def get_mode_description(self) -> str:
        """Retorna una descripción del modo tradicional"""
        return "📋 Modo Tradicional: El agente genera un plan completo al inicio y lo ejecuta secuencialmente"

    def __del__(self):
        """Destructor para limpiar recursos"""
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
            
            # Limpiar referencias para evitar errores al finalizar
            if hasattr(self, 'tool_registry'):
                self.tool_registry = None
            if hasattr(self, 'tools_manager'):
                self.tools_manager = None
            if hasattr(self, 'socket'):
                self.socket = None
            
        except Exception:
            # Evitar que errores en el destructor causen problemas
            pass

