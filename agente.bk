"""
@Author: Borja Otero Ferreira
Agente Autónomo - Sistema de procesamiento de herramientas con planificación automática
Detecta tareas, planifica pasos y ejecuta de forma autónoma.
"""
import copy
import datetime
import queue
import re
import threading
import time
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from colorama import Fore, Style
try:
    import pyttsx3
except ImportError:
    pass

from app.utils.logger import logger
from dotenv import load_dotenv
load_dotenv()

# Configurar API keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
os.environ["YOUTUBE_API_KEY"] = YOUTUBE_API_KEY
os.environ["SERPER_API_KEY"] = SERPER_API_KEY

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskStep:
    """Representa un paso individual en la ejecución de una tarea"""
    id: str
    description: str
    tool_name: str
    query: str
    dependencies: List[str]
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2

@dataclass
class TaskPlan:
    """Representa un plan completo de ejecución de tareas"""
    task_description: str
    steps: List[TaskStep]
    context: Dict[str, Any]
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    status: TaskStatus = TaskStatus.PENDING

class Agent:
    """
    Sistema de procesamiento de herramientas con planificación automática
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
            self.final_response = self._generate_normal_response(model)
            return
        
        # Variables para el procesamiento autónomo
        self.current_plan: Optional[TaskPlan] = None
        self.execution_context: Dict[str, Any] = {}
        self.max_planning_iterations = 5
        self.max_execution_iterations = 10
        
        # Iniciar el procesamiento autónomo
        self.final_response = self._autonomous_processing()
    
    def _initialize_tools(self):
        """Inicializar el registry de herramientas"""
        try:
            from tools.tool_registry import ToolRegistry
            from app.core.tools_manager import tools_manager
            
            if hasattr(tools_manager, '_registry') and tools_manager._registry:
                logger.info("🔧 Using existing tool registry from ToolsManager")
                self.tool_registry = tools_manager._registry
            else:
                logger.info("🔧 Creating new ToolRegistry in Cortex")
                self.tool_registry = ToolRegistry()
                try:
                    self.tool_registry.discover_tools()
                except Exception as e:
                    logger.error(f"Error during tool discovery: {e}")
                tools_manager.initialize_registry(self.tool_registry)
            
            self.tools_manager = tools_manager
            self.tools = self._get_available_tools_dict()
            logger.info(f"🔧 Tools initialized: {len(self.tools)} tools available")
            
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler
            
        except Exception as e:
            logger.error(f"Error initializing tools: {e}")
            self.tools = {}
            from app.core.socket_handler import SocketResponseHandler
            self.socket_handler = SocketResponseHandler

    def _autonomous_processing(self) -> str:
        """Procesamiento autónomo completo: análisis, planificación y ejecución"""
        try:
            # Paso 1: Analizar la tarea del usuario
            self._safe_emit_status("🧠 Analizando la tarea solicitada...")
            task_analysis = self._analyze_user_task()
            
            if not task_analysis:
                return self._generate_normal_response(self.model)
            
            # Paso 2: Crear plan de ejecución
            self._safe_emit_status("📋 Creando plan de ejecución...")
            self.current_plan = self._create_execution_plan(task_analysis)
            
            if not self.current_plan or not self.current_plan.steps:
                self._safe_emit_status("❌ No se pudo crear un plan de ejecución válido")
                return self._generate_normal_response(self.model)
            
            # Paso 3: Mostrar plan al usuario
            self._display_execution_plan()
            
            # Paso 4: Ejecutar el plan
            self._safe_emit_status("🚀 Ejecutando plan de tareas...")
            execution_results = self._execute_plan()
            
            # Paso 5: Generar respuesta final
            self._safe_emit_status("📝 Generando respuesta final...")
            final_response = self._generate_final_response(execution_results)
            
            return final_response
            
        except Exception as e:
            error_clean = self._clean_error_message(str(e))
            logger.error(f"Error en procesamiento autónomo: {error_clean}")
            self._safe_emit_status(f"❌ Error en procesamiento: Problema interno")
            return self._generate_normal_response(self.model)

    def _analyze_user_task(self) -> Optional[Dict[str, Any]]:
        """Analiza la tarea del usuario para determinar si necesita procesamiento autónomo"""
        try:
            # Obtener el último mensaje del usuario
            user_message = ""
            for message in reversed(self.original_prompt):
                if message['role'] == 'user':
                    user_message = message['content']
                    break
            
            if not user_message:
                return None
            
            # Crear prompt para análisis de tarea
            analysis_prompt = self._create_task_analysis_prompt(user_message)
            
            # Obtener análisis del modelo
            analysis_response = ""
            for chunk in self.model.create_chat_completion(messages=analysis_prompt, max_tokens=800, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    analysis_response += chunk['choices'][0]['delta']['content']
            
            # Parsear la respuesta del análisis
            task_analysis = self._parse_task_analysis(analysis_response)
            
            if task_analysis and task_analysis.get('requires_tools', False):
                self._emit_status(f"📋 Tarea detectada: {task_analysis.get('task_type', 'compleja')}")
                return task_analysis
            
            return None
            
        except Exception as e:
            logger.error(f"Error analizando tarea: {e}")
            return None

    def _create_task_analysis_prompt(self, user_message: str) -> List[Dict]:
        """Crea el prompt para análizar la tarea del usuario"""
        active_tools = []
        if hasattr(self, 'tools_manager'):
            active_tools = self.tools_manager.get_active_tools()
        
        tools_info = "Herramientas disponibles:\n"
        for tool_name in active_tools:
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools_info += f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}\n"
        
        analysis_prompt = [
            {
                "role": "system",
                "content": f"""Eres un asistente experto en análisis de tareas. Tu trabajo es determinar si una solicitud del usuario requiere el uso de herramientas externas y planificación de pasos.

{tools_info}

Analiza la solicitud del usuario y determina:
1. Si requiere herramientas externas (requires_tools: true/false)
2. El tipo de tarea (task_type: simple/research/analysis/creative/multi_step)
3. La complejidad (complexity: low/medium/high)
4. Los objetivos principales (objectives: lista de objetivos)
5. Las herramientas necesarias (tools_needed: lista de herramientas)

Responde ÚNICAMENTE en formato JSON válido:
{{
    "requires_tools": boolean,
    "task_type": "string",
    "complexity": "string",
    "objectives": ["objetivo1", "objetivo2"],
    "tools_needed": ["herramienta1", "herramienta2"],
    "reasoning": "explicación breve"
}}

Ejemplos de tareas que requieren herramientas:
- Buscar información actualizada
- Obtener precios de criptomonedas
- Encontrar videos específicos
- Investigar temas complejos
- Análisis de datos externos

Ejemplos de tareas que NO requieren herramientas:
- Explicaciones teóricas
- Escritura creativa
- Cálculos matemáticos simples
- Consejos generales"""
            },
            {
                "role": "user",
                "content": f"Analiza esta solicitud: {user_message}"
            }
        ]
        
        return analysis_prompt

    def _parse_task_analysis(self, analysis_response: str) -> Optional[Dict[str, Any]]:
        """Parsea la respuesta del análisis de tarea"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            analysis = json.loads(json_str)
            
            # Validar estructura mínima
            required_fields = ['requires_tools', 'task_type', 'complexity']
            if not all(field in analysis for field in required_fields):
                return None
            
            return analysis
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parseando análisis de tarea: {e}")
            return None

    def _create_execution_plan(self, task_analysis: Dict[str, Any]) -> Optional[TaskPlan]:
        """Crea un plan de ejecución detallado basado en el análisis"""
        try:
            # Crear prompt para planificación
            planning_prompt = self._create_planning_prompt(task_analysis)
            
            # Obtener plan del modelo
            plan_response = ""
            for chunk in self.model.create_chat_completion(messages=planning_prompt, max_tokens=1200, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    plan_response += chunk['choices'][0]['delta']['content']
            
            # Parsear el plan
            parsed_plan = self._parse_execution_plan(plan_response, task_analysis)
            
            return parsed_plan
            
        except Exception as e:
            logger.error(f"Error creando plan de ejecución: {e}")
            return None

    def _create_planning_prompt(self, task_analysis: Dict[str, Any]) -> List[Dict]:
        """Crea el prompt para planificación de ejecución"""
        active_tools = []
        if hasattr(self, 'tools_manager'):
            active_tools = self.tools_manager.get_active_tools()
        
        tools_info = "Herramientas disponibles:\n"
        for tool_name in active_tools:
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools_info += f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}\n"
        
        user_message = ""
        for message in reversed(self.original_prompt):
            if message['role'] == 'user':
                user_message = message['content']
                break
        
        planning_prompt = [
            {
                "role": "system",
                "content": f"""Eres un planificador experto. Tu trabajo es crear un plan detallado de ejecución para completar la tarea del usuario.

{tools_info}

Análisis de la tarea:
- Tipo: {task_analysis.get('task_type', 'unknown')}
- Complejidad: {task_analysis.get('complexity', 'unknown')}
- Objetivos: {task_analysis.get('objectives', [])}
- Herramientas necesarias: {task_analysis.get('tools_needed', [])}

Crea un plan paso a paso en formato JSON:
{{
    "task_description": "descripción clara de la tarea",
    "steps": [
        {{
            "id": "step_1",
            "description": "descripción del paso",
            "tool_name": "nombre_herramienta",
            "query": "consulta específica",
            "dependencies": ["step_anterior"],
            "reasoning": "por qué este paso es necesario"
        }}
    ],
    "success_criteria": "cómo saber si la tarea se completó exitosamente"
}}

Reglas importantes:
1. Solo usa herramientas disponibles en la lista
2. Ordena los pasos lógicamente
3. Especifica dependencias entre pasos
4. Haz consultas específicas y claras
5. Máximo 8 pasos por plan
6. Cada paso debe tener un propósito claro"""
            },
            {
                "role": "user",
                "content": f"Crea un plan para: {user_message}"
            }
        ]
        
        return planning_prompt

    def _parse_execution_plan(self, plan_response: str, task_analysis: Dict[str, Any]) -> Optional[TaskPlan]:
        """Parsea la respuesta del plan de ejecución"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            plan_data = json.loads(json_str)
            
            # Crear objetos TaskStep
            steps = []
            for i, step_data in enumerate(plan_data.get('steps', [])):
                step = TaskStep(
                    id=step_data.get('id', f'step_{i+1}'),
                    description=step_data.get('description', 'Sin descripción'),
                    tool_name=step_data.get('tool_name', ''),
                    query=step_data.get('query', ''),
                    dependencies=step_data.get('dependencies', []),
                    status=TaskStatus.PENDING
                )
                steps.append(step)
            
            # Crear TaskPlan
            task_plan = TaskPlan(
                task_description=plan_data.get('task_description', 'Tarea sin descripción'),
                steps=steps,
                context={'analysis': task_analysis, 'success_criteria': plan_data.get('success_criteria', '')},
                created_at=datetime.datetime.now(),
                status=TaskStatus.PENDING
            )
            
            return task_plan
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parseando plan de ejecución: {e}")
            return None

    def _display_execution_plan(self):
        """Muestra el plan de ejecución al usuario"""
        if not self.current_plan:
            return
        
        plan_text = f"📋 **Plan de Ejecución**\n\n"
        plan_text += f"**Tarea:** {self.current_plan.task_description}\n\n"
        plan_text += f"**Pasos a ejecutar:**\n"
        
        for i, step in enumerate(self.current_plan.steps, 1):
            plan_text += f"{i}. **{step.description}**\n"
            plan_text += f"   - Herramienta: `{step.tool_name}`\n"
            plan_text += f"   - Consulta: `{step.query}`\n"
            if step.dependencies:
                plan_text += f"   - Depende de: {', '.join(step.dependencies)}\n"
            plan_text += "\n"
        
        self._emit_status(plan_text)
        logger.info(f"Plan de ejecución mostrado: {len(self.current_plan.steps)} pasos")

    def _execute_plan(self) -> Dict[str, Any]:
        """Ejecuta el plan de tareas paso a paso"""
        if not self.current_plan:
            return {}
        
        execution_results = {
            'completed_steps': [],
            'failed_steps': [],
            'total_steps': len(self.current_plan.steps),
            'success_rate': 0.0,
            'execution_time': 0.0
        }
        
        start_time = time.time()
        
        try:
            # Ejecutar pasos en orden, respetando dependencias
            for iteration in range(self.max_execution_iterations):
                # Verificar si se debe detener
                if self.assistant and getattr(self.assistant, 'stop_emit', False):
                    self._safe_emit_status("🛑 Ejecución detenida por el usuario")
                    break
                
                # Buscar pasos listos para ejecutar
                ready_steps = self._get_ready_steps()
                if not ready_steps:
                    break
                
                # Ejecutar pasos listos
                for step in ready_steps:
                    if self.assistant and getattr(self.assistant, 'stop_emit', False):
                        break
                    
                    self._execute_step(step)
                    
                    if step.status == TaskStatus.COMPLETED:
                        execution_results['completed_steps'].append(step)
                    elif step.status == TaskStatus.FAILED:
                        execution_results['failed_steps'].append(step)
                
                # Verificar si todos los pasos están completos
                if all(step.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED] 
                       for step in self.current_plan.steps):
                    break
            
            # Calcular estadísticas
            if execution_results['total_steps'] > 0:
                execution_results['success_rate'] = len(execution_results['completed_steps']) / execution_results['total_steps']
            execution_results['execution_time'] = time.time() - start_time
            
            # Actualizar estado del plan
            if execution_results['success_rate'] > 0.5:
                self.current_plan.status = TaskStatus.COMPLETED
            else:
                self.current_plan.status = TaskStatus.FAILED
            
            self.current_plan.completed_at = datetime.datetime.now()
            
            return execution_results
            
        except Exception as e:
            error_clean = self._clean_error_message(str(e))
            logger.error(f"Error ejecutando plan: {error_clean}")
            execution_results['error'] = error_clean
            return execution_results

    def _get_ready_steps(self) -> List[TaskStep]:
        """Obtiene los pasos que están listos para ejecutar"""
        ready_steps = []
        
        for step in self.current_plan.steps:
            if step.status != TaskStatus.PENDING:
                continue
            
            # Verificar dependencias
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_step = self._find_step_by_id(dep_id)
                if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_steps.append(step)
        
        return ready_steps

    def _find_step_by_id(self, step_id: str) -> Optional[TaskStep]:
        """Encuentra un paso por su ID"""
        for step in self.current_plan.steps:
            if step.id == step_id:
                return step
        return None

    def _execute_step(self, step: TaskStep):
        """Ejecuta un paso individual"""
        try:
            step.status = TaskStatus.IN_PROGRESS
            
            self._safe_emit_status(f"🔄 Ejecutando: {step.description}")
            logger.info(f"Ejecutando paso: {step.id} - {step.description}")
            
            # Verificar si la herramienta está disponible
            if not self._is_tool_available(step.tool_name):
                step.status = TaskStatus.FAILED
                step.error = f"Herramienta {step.tool_name} no está disponible"
                self._safe_emit_status(f"❌ {step.error}")
                return
            
            # Ejecutar la herramienta
            result = self._execute_tool(step.tool_name, step.query)
            
            # Validar resultado - manejar casos especiales como tuplas
            result_valid = False
            result_text = None
            
            if result is not None:
                if isinstance(result, tuple):
                    # Si es una tupla, tomar el primer elemento como resultado de texto
                    result_text = str(result[0]) if result[0] is not None else ""
                elif isinstance(result, str):
                    result_text = result
                else:
                    result_text = str(result)
                
                # Verificar si es un resultado exitoso
                if result_text and not result_text.startswith("Error"):
                    result_valid = True
            
            if result_valid:
                step.status = TaskStatus.COMPLETED
                step.result = result_text
                self._safe_emit_status(f"✅ Completado: {step.description}")
                
                # Almacenar resultado en contexto para pasos posteriores
                self.execution_context[step.id] = {
                    'result': result_text,
                    'tool_name': step.tool_name,
                    'query': step.query
                }
            else:
                step.retry_count += 1
                if step.retry_count <= step.max_retries:
                    # Reintentar
                    step.status = TaskStatus.PENDING
                    self._safe_emit_status(f"🔄 Reintentando: {step.description} (intento {step.retry_count + 1})")
                else:
                    step.status = TaskStatus.FAILED
                    step.error = result_text or "Error desconocido"
                    self._safe_emit_status(f"❌ Falló: {step.description} - Error de procesamiento")
                    
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = self._clean_error_message(str(e))
            self._safe_emit_status(f"❌ Error ejecutando {step.description}: Error interno")
            logger.error(f"Error ejecutando paso {step.id}: {step.error}")

    def _is_tool_available(self, tool_name: str) -> bool:
        """Verifica si una herramienta está disponible"""
        if not hasattr(self, 'tools_manager'):
            return False
        
        return self.tools_manager.is_tool_active(tool_name)

    def _execute_tool(self, tool_name: str, query: str) -> Optional[str]:
        """Ejecuta una herramienta específica"""
        try:
            # Usar el mismo método que el Cortex original
            resultado_ejecucion = self.tool_registry.execute_tool(tool_name, query)
            print(resultado_ejecucion)
            if not resultado_ejecucion.success:
                # Limpiar mensajes de error de caracteres problemáticos
                error_clean = self._clean_error_message(resultado_ejecucion.error)
                return f"Error: {error_clean}"
            
            resultado = resultado_ejecucion.data
            
            # Manejo especial para herramientas que devuelven múltiples valores
            if tool_name == "video_search_tool" and isinstance(resultado, tuple):
                resultado_texto, ids = resultado
                # Emitir los IDs para el frontend
                try:
                    from app.core.socket_handler import SocketResponseHandler
                    SocketResponseHandler.emit_utilities_data(self.socket, {"ids": ids})
                except Exception as e:
                    logger.warning(f"Error emitiendo datos de utilidades: {e}")
                
                # Usar solo el texto del resultado
                resultado = resultado_texto
            
            # Limpiar resultado de caracteres problemáticos
            if isinstance(resultado, str):
                resultado = self._clean_text_content(resultado)
            else:
                # Convertir a string si no lo es
                resultado = str(resultado) if resultado is not None else ""
            
            # Enviar resultado al socket
            self._emit_tool_result(tool_name, query, resultado)
            
            return resultado
            
        except Exception as e:
            error_msg = self._clean_error_message(f"Error ejecutando {tool_name}: {str(e)}")
            logger.error(error_msg)
            return error_msg

    def _generate_final_response(self, execution_results: Dict[str, Any]) -> str:
        """Genera la respuesta final basada en los resultados de ejecución"""
        try:
            self._safe_emit_status("📝 Consolidando resultados y generando respuesta final...")
            
            # Preparar prompt final con todos los resultados
            final_prompt = self._create_final_response_prompt(execution_results)
            
            # Generar respuesta final
            response_final = self._stream_final_response(final_prompt)
            
            # Mostrar estadísticas de ejecución
            self._display_execution_stats(execution_results)
            
            return response_final
            
        except Exception as e:
            error_clean = self._clean_error_message(str(e))
            logger.error(f"Error generando respuesta final: {error_clean}")
            
            # Fallback: crear respuesta simple con los resultados
            try:
                fallback_response = self._create_fallback_response(execution_results)
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_console_output(self.socket, fallback_response, 'assistant')
                SocketResponseHandler.emit_finalization_signal(self.socket, 0, 0)
                return fallback_response
            except Exception:
                return "Error: No se pudo generar la respuesta final."

    def _create_final_response_prompt(self, execution_results: Dict[str, Any]) -> List[Dict]:
        """Crea el prompt para la respuesta final"""
        try:
            prompt_final = copy.deepcopy(self.original_prompt)
            
            # Consolidar todos los resultados
            resultados_consolidados = "Resultados de la ejecución del plan:\n"
            
            # Pasos completados
            completed_steps = execution_results.get('completed_steps', [])
            if completed_steps:
                resultados_consolidados += "\n✅ PASOS COMPLETADOS:\n"
                for step in completed_steps:
                    resultados_consolidados += f"• {step.description}\n"
                    resultados_consolidados += f"  Herramienta: {step.tool_name}\n"
                    resultados_consolidados += f"  Consulta: {step.query}\n"
                    if step.result:
                        result_preview = step.result[:500] + "..." if len(step.result) > 500 else step.result
                        # Limpiar el resultado antes de añadirlo
                        clean_result = self._clean_text_content(result_preview)
                        resultados_consolidados += f"  Resultado: {clean_result}\n"
            
            # Pasos fallidos
            failed_steps = execution_results.get('failed_steps', [])
            if failed_steps:
                resultados_consolidados += "\n❌ PASOS FALLIDOS:\n"
                for step in failed_steps:
                    clean_error = self._clean_text_content(step.error or "Error desconocido")
                    resultados_consolidados += f"• {step.description}: {clean_error}\n"
            
            # Instrucciones para la respuesta final
            instrucciones_finales = """
Responde en Markdown con formato profesional, limpio y compacto.

Utiliza toda la información obtenida para proporcionar una respuesta completa y útil.

IMPORTANTE - Reglas de formato:
- Evita saltos de línea excesivos - máximo 1 línea en blanco entre secciones
- Usa formato compacto y profesional
- Incrusta imágenes con ![descripción](url) 
- Enlaces de YouTube sin formato markdown, solo el URL
- Organiza la información de manera clara y estructurada sin espaciado excesivo
- Incluye enlaces e imágenes relevantes encontradas
- Responde completamente en español
- NO uses múltiples saltos de línea consecutivos
- Mantén un formato limpio y legible sin espacios innecesarios

Si algunos pasos fallaron, menciona qué información no se pudo obtener pero proporciona la mejor respuesta posible con la información disponible.
            """
            
            # Añadir mensajes al prompt
            prompt_final.append({"role": "assistant", "content": "He completado la ejecución del plan de tareas."})
            prompt_final.append({"role": "user", "content": resultados_consolidados + instrucciones_finales})
            
            return prompt_final
            
        except Exception as e:
            logger.error(f"Error creando prompt final: {e}")
            # Fallback: crear prompt mínimo
            return copy.deepcopy(self.original_prompt)

    def _stream_final_response(self, prompt: List[Dict]) -> str:
        """Stream de la respuesta final al socket"""
        response_completa = ''
        
        try:
            # Calcular tokens del usuario
            user_question = ""
            for message in reversed(self.original_prompt):
                if message['role'] == 'user':
                    user_question = message['content']
                    break
            
            tokensInput = user_question.encode()
            tokens = self.model.tokenize(tokensInput)
            total_user_tokens = len(tokens)
            
            # Función segura para verificar stop condition
            def safe_stop_condition():
                try:
                    return self.assistant and getattr(self.assistant, 'stop_emit', False)
                except Exception:
                    return False
            
            # Stream de la respuesta
            from app.core.socket_handler import SocketResponseHandler
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=self.model,
                messages=prompt,
                socket=self.socket,
                max_tokens=8192,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=self.response_queue,
                link_remover_func=self._remove_links,
                stop_condition=safe_stop_condition
            )
            
            # Formatear la respuesta antes de enviarla
            response_completa = self._format_final_response(response_completa)
            
            self.response_queue.put(None)
            SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
            
            return response_completa
            
        except Exception as e:
            error_clean = self._clean_error_message(str(e))
            logger.error(f"Error en stream de respuesta final: {error_clean}")
            
            # Fallback: enviar respuesta directamente
            try:
                from app.core.socket_handler import SocketResponseHandler
                fallback_response = "Lo siento, hubo un problema al generar la respuesta final. Los resultados están disponibles en las estadísticas de ejecución."
                SocketResponseHandler.emit_console_output(self.socket, fallback_response, 'assistant')
                SocketResponseHandler.emit_finalization_signal(self.socket, 0, 0)
                return fallback_response
            except Exception:
                return "Error al generar respuesta final"

    def _create_fallback_response(self, execution_results: Dict[str, Any]) -> str:
        """Crea una respuesta de respaldo cuando el streaming falla"""
        try:
            response = "# Resumen de Ejecución\n"
            
            # Mostrar pasos completados
            if execution_results.get('completed_steps'):
                response += "\n## ✅ Pasos Completados\n"
                for step in execution_results['completed_steps']:
                    response += f"**{step.description}**\n"
                    if step.result:
                        preview = step.result[:300] + "..." if len(step.result) > 300 else step.result
                        clean_preview = self._clean_text_content(preview)
                        response += f"- Resultado: {clean_preview}\n"
            
            # Mostrar pasos fallidos
            if execution_results.get('failed_steps'):
                response += "\n## ❌ Pasos Fallidos\n"
                for step in execution_results['failed_steps']:
                    response += f"**{step.description}**\n"
                    clean_error = self._clean_text_content(step.error or "Error desconocido")
                    response += f"- Error: {clean_error}\n"
            
            # Estadísticas
            total_steps = execution_results.get('total_steps', 0)
            completed = len(execution_results.get('completed_steps', []))
            success_rate = (completed / total_steps * 100) if total_steps > 0 else 0
            
            response += f"\n## 📊 Estadísticas\n"
            response += f"- Total de pasos: {total_steps}\n"
            response += f"- Pasos completados: {completed}\n"
            response += f"- Tasa de éxito: {success_rate:.1f}%\n"
            response += f"- Tiempo de ejecución: {execution_results.get('execution_time', 0):.2f}s"
            
            # Limpiar la respuesta completa de saltos de línea excesivos
            return self._clean_text_content(response)
            
        except Exception as e:
            logger.error(f"Error creando respuesta de respaldo: {e}")
            return "Se completó la ejecución, pero hubo problemas al generar la respuesta final."
            
        except Exception as e:
            logger.error(f"Error creando respuesta de respaldo: {e}")
            return "Se completó la ejecución, pero hubo problemas al generar la respuesta final."

    def _display_execution_stats(self, execution_results: Dict[str, Any]):
        """Muestra estadísticas de ejecución"""
        try:
            stats_text = f"\n📊 **Estadísticas de Ejecución**\n"
            stats_text += f"- Total de pasos: {execution_results.get('total_steps', 0)}\n"
            stats_text += f"- Pasos completados: {len(execution_results.get('completed_steps', []))}\n"
            stats_text += f"- Pasos fallidos: {len(execution_results.get('failed_steps', []))}\n"
            stats_text += f"- Tasa de éxito: {execution_results.get('success_rate', 0):.1%}\n"
            stats_text += f"- Tiempo de ejecución: {execution_results.get('execution_time', 0):.2f}s\n"
            
            self._safe_emit_status(stats_text)
        except Exception as e:
            logger.error(f"Error mostrando estadísticas: {e}")
            self._safe_emit_status("📊 Estadísticas de ejecución completadas")

    def _emit_status(self, message: str):
        """Emite un mensaje de estado al socket"""
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
        logger.info(message)
        from app.core.socket_handler import SocketResponseHandler
        SocketResponseHandler.emit_console_output(self.socket, message, 'info')

    def _emit_tool_result(self, tool_name: str, query: str, result: str):
        """Emite el resultado de una herramienta al socket"""
        self._safe_emit_tool_result(tool_name, query, result)

    def _generate_normal_response(self, model: Any) -> str:
        """Genera una respuesta normal sin herramientas"""
        try:
            # Calcular tokens del usuario
            user_question = ""
            for message in reversed(self.original_prompt):
                if message['role'] == 'user':
                    user_question = message['content']
                    break
            
            tokensInput = user_question.encode()
            tokens = model.tokenize(tokensInput)
            total_user_tokens = len(tokens)
            
            # Función segura para verificar stop condition
            def safe_stop_condition():
                try:
                    return self.assistant and getattr(self.assistant, 'stop_emit', False)
                except Exception:
                    return False
            
            # Stream de la respuesta usando el mismo sistema que las respuestas con herramientas
            from app.core.socket_handler import SocketResponseHandler
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=model,
                messages=self.original_prompt,
                socket=self.socket,
                max_tokens=1200,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=self.response_queue,
                link_remover_func=self._remove_links,
                stop_condition=safe_stop_condition
            )
            
            # Formatear la respuesta antes de enviarla
            response_completa = self._format_final_response(response_completa)
            
            # Señales de finalización
            self.response_queue.put(None)
            SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
            
            return response_completa
            
        except Exception as e:
            logger.error(f"Error generando respuesta normal: {e}")
            
            # Fallback en caso de error
            try:
                from app.core.socket_handler import SocketResponseHandler
                error_msg = "Lo siento, hubo un problema al generar la respuesta."
                SocketResponseHandler.emit_console_output(self.socket, error_msg, 'assistant')
                SocketResponseHandler.emit_finalization_signal(self.socket, 0, 0)
                return error_msg
            except Exception:
                return f"Error generando respuesta normal: {str(e)}"

    def _get_available_tools_dict(self) -> Dict[str, Any]:
        """Obtiene un diccionario de herramientas disponibles"""
        tools_dict = {}
        try:
            if hasattr(self, 'tool_registry'):
                for tool_name in self.tool_registry.list_tools():
                    tool_info = self.tool_registry.get_tool_info(tool_name)
                    if tool_info:
                        tools_dict[tool_name] = tool_info
            return tools_dict
        except Exception as e:
            logger.error(f"Error obteniendo herramientas disponibles: {e}")
            return {}

    def _remove_links(self, text: str) -> str:
        """Remueve enlaces de texto"""
        if not text:
            return text
        
        # Remover enlaces web
        text = re.sub(r'https?://[^\s\]]+', '', text)
        # Remover enlaces de YouTube sin protocolo
        text = re.sub(r'www\.youtube\.com[^\s\]]+', '', text)
        text = re.sub(r'youtube\.com[^\s\]]+', '', text)
        
        return text.strip()

    def _clean_text_content(self, text: str) -> str:
        """Limpia contenido de texto de caracteres problemáticos y saltos de línea excesivos"""
        if not text:
            return text
        
        try:
            # Remover caracteres de control y no imprimibles (excepto saltos de línea normales)
            import string
            allowed_chars = set(string.printable)
            cleaned_text = ''.join(char for char in text if char in allowed_chars)
            
            # Remover secuencias de caracteres extraños (preservar saltos de línea)
            import re
            cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_text)  # Solo ASCII
            
            # Limpiar saltos de línea excesivos (pero preservar formato)
            cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Máximo 2 saltos de línea
            cleaned_text = re.sub(r'\r\n', '\n', cleaned_text)  # Normalizar saltos de línea
            cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Normalizar espacios horizontales
            cleaned_text = re.sub(r'[ \t]+\n', '\n', cleaned_text)  # Remover espacios al final de línea
            
            return cleaned_text.strip()
        except Exception as e:
            logger.warning(f"Error limpiando texto: {e}")
            return "Contenido no disponible debido a problemas de encoding"

    def _clean_error_message(self, error_msg: str) -> str:
        """Limpia mensajes de error de caracteres problemáticos"""
        if not error_msg:
            return "Error desconocido"
        
        try:
            # Convertir a string si no lo es
            error_str = str(error_msg)
            
            # Remover caracteres problemáticos
            cleaned = error_str.encode('ascii', 'ignore').decode('ascii')
            
            # Simplificar mensajes de parser muy largos
            if "ParserRejectedMarkup" in cleaned or "expected name token" in cleaned:
                return "Error: Contenido web no válido o corrupto. No se pudo extraer información."
            
            # Truncar mensajes muy largos
            if len(cleaned) > 500:
                cleaned = cleaned[:500] + "..."
            
            return cleaned
        except Exception:
            return "Error: Problema de encoding al procesar respuesta"

    def _safe_emit_status(self, message: str):
        """Emite mensaje de estado de forma segura, manejando errores de encoding"""
        try:
            clean_message = self._clean_text_content(message)
            self._emit_status(clean_message)
        except Exception as e:
            # Fallback para emisión de estado
            try:
                fallback_msg = f"Estado: {str(e)[:100]}"
                print(f"{Fore.CYAN}{fallback_msg}{Style.RESET_ALL}")
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_console_output(self.socket, fallback_msg, 'info')
            except Exception:
                pass  # Si falla todo, simplemente continuar

    def _safe_emit_tool_result(self, tool_name: str, query: str, result: str):
        """Emite resultado de herramienta de forma segura"""
        try:
            clean_result = self._clean_text_content(result)
            preview = clean_result[:200] + "..." if len(clean_result) > 200 else clean_result
            message = f"🔧 {tool_name} -> {preview}"
            
            from app.core.socket_handler import SocketResponseHandler
            SocketResponseHandler.emit_console_output(self.socket, message, 'tool')
        except Exception as e:
            # Fallback
            try:
                fallback_msg = f"🔧 {tool_name} -> Resultado disponible"
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_console_output(self.socket, fallback_msg, 'tool')
            except Exception:
                pass

    def get_response(self) -> str:
        """Obtiene la respuesta final"""
        return getattr(self, 'final_response', '')

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

    def _format_final_response(self, response: str) -> str:
        """Formatea la respuesta final eliminando saltos de línea excesivos y mejorando la presentación"""
        if not response:
            return response
        
        try:
            # Limpiar la respuesta de caracteres problemáticos
            formatted_response = self._clean_text_content(response)
            
            # Aplicar reglas específicas de formateo
            import re
            
            # Eliminar más de 2 saltos de línea consecutivos
            formatted_response = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_response)
            
            # Normalizar espacios después de puntuación
            formatted_response = re.sub(r'([.!?])\s{2,}', r'\1 ', formatted_response)
            
            # Eliminar espacios al final de las líneas
            formatted_response = re.sub(r' +\n', '\n', formatted_response)
            
            # Asegurar formato correcto de listas
            formatted_response = re.sub(r'\n+(\s*[-*•]\s)', r'\n\1', formatted_response)
            
            # Asegurar formato correcto de títulos
            formatted_response = re.sub(r'\n+(#+\s)', r'\n\n\1', formatted_response)
            
            # Eliminar espacios al inicio y final
            formatted_response = formatted_response.strip()
            
            return formatted_response
            
        except Exception as e:
            logger.warning(f"Error formateando respuesta final: {e}")
            return response