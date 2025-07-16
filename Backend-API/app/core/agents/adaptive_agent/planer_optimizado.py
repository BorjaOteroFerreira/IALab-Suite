"""
@Author: Borja Otero Ferreira
Planificador Adaptativo Optimizado - Versión con queries generadas por el modelo
El modelo decide directamente las queries más adecuadas y concisas para cada herramienta
"""
import json
import re
import datetime
import time
from typing import Dict, Any, Optional, List, Tuple
from ..models import TaskPlan, TaskStep, TaskStatus
from ..utils import clean_error_message, safe_emit_tool_result
from app.utils.logger import logger
from app.core.socket_handler import SocketResponseHandler

class OptimizedAdaptiveTaskPlanner:
    """
    Planificador adaptativo optimizado donde el modelo decide las queries directamente.
    Enfoque en queries concisas y adecuadas para cada herramienta específica.
    """
    
    def __init__(self, model, tools_manager, tool_registry, socket, assistant=None):
        self.model = model
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
        self.socket = socket
        self.assistant = assistant
        self.max_iterations = 12
        self.execution_context = {}
        self.conversation_history = []
        
        # Cacheo para evitar regenerar prompts
        self._tools_cache = None
        self._tools_cache_time = 0
        
        # Métricas para detección de patrones
        self.failure_count = 0
        self.consecutive_failures = 0
        self.tool_usage_count = {}
        self.last_successful_tool = None
        
        # Historial de queries para evitar repeticiones
        self.query_history = {}  # {tool_name: [query1, query2, ...]}
        self.successful_queries = {}  # {tool_name: [successful_queries]}
        self.failed_queries = {}  # {tool_name: [failed_queries]}
        
        # Información sobre herramientas para el modelo
        self.tool_descriptions = {
            'serper_search': 'Búsqueda web general. Usa términos específicos y concisos.',
            'serper_news': 'Noticias recientes. Usa keywords relevantes para noticias actuales.',
            'weather_tool': 'Información meteorológica. Usa nombres de ciudades o ubicaciones.',
            'calculator': 'Cálculos matemáticos. Usa expresiones matemáticas directas.',
            'web_scraper': 'Extracción de contenido web. Usa URLs específicas.',
            'image_search': 'Búsqueda de imágenes. Usa términos descriptivos visuales.'
        }
    
    def run_adaptive_plan(self, task_analysis: Dict[str, Any], original_prompt: List[Dict], 
                         emit_status_func, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Ejecuta planificación adaptativa optimizada con queries generadas por el modelo.
        """
        start_time = time.time()
        self.conversation_history = conversation_history or []
        
        user_message = self._extract_user_message(original_prompt)
        current_plan = self._create_initial_plan(task_analysis, user_message)
        
        execution_results = {
            'completed_steps': [],
            'failed_steps': [],
            'total_steps': 0,
            'success_rate': 0.0,
            'execution_time': 0.0,
            'adaptations_made': 0,
            'reflections': []
        }
        
        final_response_sent = False  # Nueva variable para controlar el envío de la respuesta final
        
        try:
            # Condición 1: Herramientas deshabilitadas globalmente
            if hasattr(self.tools_manager, 'is_tools_enabled') and not self.tools_manager.is_tools_enabled():
                emit_status_func("🔧 Las herramientas están deshabilitadas. Generando respuesta directa.", 'info')
                self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                return execution_results

            # Condición 2: No hay herramientas activas seleccionadas
            if hasattr(self.tools_manager, 'get_active_tools') and not self.tools_manager.get_active_tools():
                emit_status_func("🔧 No hay herramientas activas seleccionadas. Generando respuesta directa.", 'info')
                self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                return execution_results

            for iteration in range(self.max_iterations):
                # Condición 3: Señal de parada del usuario
                if self.assistant and getattr(self.assistant, 'stop_emit', False):
                    emit_status_func("🛑 Ejecución detenida por el usuario", 'info')
                    break
                
                # Reflexión lightweight cada 2 iteraciones o cuando hay problemas
                should_reflect = (iteration % 2 == 0 or 
                                self.consecutive_failures >= 2 or 
                                self._should_force_reflection(iteration))
                
                if should_reflect:
                    emit_status_func(f"💭 Evaluando progreso... (Iteración {iteration + 1})", 'pensamiento')
                    reflection = self._lightweight_reflection(current_plan, user_message, iteration)
                    execution_results['reflections'].append(reflection)
                    
                    if reflection.get('task_completed', False):
                        emit_status_func("✅ **TAREA COMPLETADA**", 'info')
                        self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                        final_response_sent = True  # Marcar como enviada
                        break
                else:
                    reflection = self._quick_assessment()
                
                # Decidir siguiente paso con query generada por el modelo
                next_step = self._decide_next_step_with_model_query(current_plan, reflection, user_message, iteration)
                
                # Condición 4: No se detectan más herramientas necesarias
                if not next_step:
                    emit_status_func("📝 Finalizando con información disponible", 'info')
                    self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                    final_response_sent = True  # Marcar como enviada
                    break
                
                # Ejecutar paso
                current_plan.steps.append(next_step)
                execution_results['total_steps'] += 1
                
                self._display_current_step_compact(next_step, iteration + 1, emit_status_func)
                self._execute_step(next_step, emit_status_func)
                
                # Actualizar métricas y historial
                self._update_metrics(next_step)
                self._update_query_history(next_step)
                
                # Procesar resultado
                if next_step.status == TaskStatus.COMPLETED:
                    execution_results['completed_steps'].append(next_step)
                    self._cache_result(next_step, iteration + 1)
                    self.consecutive_failures = 0
                elif next_step.status == TaskStatus.FAILED:
                    execution_results['failed_steps'].append(next_step)
                    self.consecutive_failures += 1
                    self.failure_count += 1
                
                # Parada temprana inteligente
                if self._should_stop_early(iteration, execution_results):
                    emit_status_func("🎯 Suficiente información recopilada", 'info')
                    self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                    final_response_sent = True  # Marcar como enviada
                    break
                
                # Condición 5: Se alcanza el máximo de iteraciones
                if iteration + 1 >= self.max_iterations:
                    emit_status_func(f"⏳ Se alcanzó el máximo de iteraciones ({self.max_iterations}). Generando respuesta final.", 'info')
                    self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                    final_response_sent = True
                    break

                time.sleep(0.3)
            
            self._calculate_final_stats(execution_results, start_time)
            self._display_execution_stats_compact(execution_results, emit_status_func)
            
            if (not final_response_sent and not any(r.get('task_completed', False) for r in execution_results['reflections']) and self.execution_context):
                emit_status_func("📋 **INFORMACIÓN RECOPILADA**", 'info')
                self._generate_clean_final_response(user_message, execution_results, emit_status_func)
            
            return execution_results
            
        except Exception as e:
            error_clean = clean_error_message(str(e))
            logger.error(f"Error en planificación: {error_clean}")
            execution_results['error'] = error_clean
            return execution_results
    
    def _decide_next_step_with_model_query(self, current_plan: TaskPlan, reflection: Dict[str, Any], 
                                          user_message: str, iteration: int) -> Optional[TaskStep]:
        """
        Decisión de paso donde el modelo genera la query directamente.
        """
        try:
            if reflection.get('task_completed', False):
                return None
            
            available_tools = self._get_cached_tools()
            
            if not available_tools:
                return None
            
            # Generar siguiente acción usando el modelo
            next_action = self._generate_next_action_with_model(
                user_message, available_tools, reflection, iteration
            )
            
            if not next_action or not next_action.get('tool_name') or not next_action.get('query'):
                return None
            
            # Verificar que la herramienta esté disponible
            if next_action['tool_name'] not in available_tools:
                return None
            
            # Verificar que no sea una query repetida
            if self._is_query_repeated(next_action['tool_name'], next_action['query']):
                # Dar una oportunidad al modelo para generar una query alternativa
                alternative_action = self._generate_alternative_query(
                    user_message, next_action['tool_name'], iteration
                )
                if alternative_action and alternative_action.get('query'):
                    next_action['query'] = alternative_action['query']
                else:
                    return None
            
            return TaskStep(
                id=f"step_{iteration + 1}",
                description=next_action.get('description', f"Usar {next_action['tool_name']}"),
                tool_name=next_action['tool_name'],
                query=next_action['query'],
                dependencies=[],
                status=TaskStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Error decidiendo paso: {e}")
            return None
    
    def _generate_next_action_with_model(self, user_message: str, available_tools: List[str], 
                                        reflection: Dict[str, Any], iteration: int) -> Dict[str, Any]:
        """
        Genera la próxima acción (herramienta + query) usando el modelo.
        """
        try:
            # Construir información del contexto actual
            context_info = self._build_context_for_model()
            
            # Construir información sobre herramientas disponibles
            tools_info = self._build_tools_info(available_tools)
            
            # Construir historial de queries para evitar repeticiones
            query_history_info = self._build_query_history_info()
            
            action_prompt = [
                {
                    "role": "system",
                    "content": """Eres un estratega de búsqueda de información. Tu trabajo es decidir la próxima acción más efectiva.

REGLAS IMPORTANTES:
1. Genera queries CONCISAS y ESPECÍFICAS para cada herramienta
2. Evita queries repetidas o muy similares
3. Adapta el lenguaje de la query a la herramienta específica
4. Usa máximo 3-5 palabras clave por query
5. Considera el contexto ya recopilado

RESPONDE SOLO EN JSON:
{
    "tool_name": "nombre_herramienta",
    "query": "query concisa y específica",
    "description": "breve descripción de qué esperas obtener",
    "reasoning": "por qué esta herramienta y query son apropiadas"
}"""
                },
                {
                    "role": "user",
                    "content": f"""TAREA ORIGINAL: {user_message}

HERRAMIENTAS DISPONIBLES:
{tools_info}

INFORMACIÓN YA RECOPILADA:
{context_info}

HISTORIAL DE QUERIES (evitar repetir):
{query_history_info}

SITUACIÓN ACTUAL:
- Iteración: {iteration + 1}/{self.max_iterations}
- Fallos consecutivos: {self.consecutive_failures}
- Estrategia recomendada: {reflection.get('next_strategy', 'continuar')}
- Debe pivotar: {reflection.get('should_pivot', False)}

¿Cuál es la próxima acción más efectiva? Genera una query concisa y específica."""
                }
            ]
            
            response = self._get_model_response(action_prompt, max_tokens=400)
            SocketResponseHandler.emit_console_output(self.socket, response, 'pensamiento')
            
            action = self._parse_json_response(response)
            
            # Validar que la respuesta contenga los campos necesarios
            if not action.get('tool_name') or not action.get('query'):
                logger.warning("Respuesta del modelo incompleta para acción")
                return {}
            
            return action
            
        except Exception as e:
            logger.error(f"Error generando acción con modelo: {e}")
            return {}
    
    def _generate_alternative_query(self, user_message: str, tool_name: str, iteration: int) -> Dict[str, Any]:
        """
        Genera una query alternativa cuando la original ya fue usada.
        """
        try:
            used_queries = self.query_history.get(tool_name, [])
            # Obtener descripción dinámica del tool_registry
            if self.tool_registry and hasattr(self.tool_registry, 'get_tool_description'):
                tool_info = self.tool_registry.get_tool_description(tool_name)
            else:
                tool_info = f"Herramienta '{tool_name}' (sin descripción)"

            alternative_prompt = [
                {
                    "role": "system",
                    "content": """Genera una query alternativa concisa y específica para la herramienta indicada.

REGLAS:
- Máximo 3-5 palabras clave
- Diferente a las queries ya usadas
- Específica para la herramienta
- Enfocada en obtener información útil

RESPONDE JSON:
{
    "query": "query alternativa concisa",
    "reasoning": "por qué esta query será efectiva"
}"""
                },
                {
                    "role": "user",
                    "content": f"""TAREA: {user_message}

HERRAMIENTA: {tool_name}
DESCRIPCIÓN: {tool_info}

QUERIES YA USADAS:
{chr(10).join(f"- {q}" for q in used_queries)}

Genera una query alternativa concisa y específica que no haya sido usada."""
                }
            ]
            response = self._get_model_response(alternative_prompt, max_tokens=200)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error generando query alternativa: {e}")
            return {}
    
    def _build_context_for_model(self) -> str:
        """
        Construye información del contexto para el modelo.
        """
        if not self.execution_context:
            return "Sin información recopilada aún"
        
        context_parts = []
        for step_id, step_data in list(self.execution_context.items())[-3:]:  # Últimos 3 pasos
            if isinstance(step_data, dict):
                tool_used = step_data.get('tool_used', 'desconocido')
                result_preview = step_data.get('result', '')[:100] + "..." if step_data.get('result') else 'Sin resultado'
                context_parts.append(f"• {tool_used}: {result_preview}")
        
        return "\n".join(context_parts)
    
    def _build_tools_info(self, available_tools: List[str]) -> str:
        """
        Construye información sobre herramientas disponibles para el modelo usando tool_manager y tool_registry.
        """
        tools_info = []
        for tool in available_tools:
            # Obtener descripción dinámica del tool_manager
            description = None
            if self.tools_manager and hasattr(self.tools_manager, 'get_tool_description'):
                try:
                    description = self.tools_manager.get_tool_description(tool)
                except Exception:
                    description = None
            # Si no está en tool_manager, buscar en tool_registry
            if not description and self.tool_registry and hasattr(self.tool_registry, 'get_tool_description'):
                try:
                    description = self.tool_registry.get_tool_description(tool)
                except Exception:
                    description = None
            if not description:
                description = f"Herramienta '{tool}' (sin descripción)"

            # Información sobre uso previo
            usage_count = self.tool_usage_count.get(tool, 0)
            success_count = len(self.successful_queries.get(tool, []))

            # Estado de la herramienta
            if usage_count == 0:
                status = "🆕 No usada"
            elif success_count > 0:
                status = f"✅ {success_count} éxitos de {usage_count} usos"
            else:
                status = f"❌ {usage_count} intentos fallidos"

            tools_info.append(f"• {tool}: {description} [{status}]")
        return "\n".join(tools_info)
    
    def _build_query_history_info(self) -> str:
        """
        Construye información del historial de queries para el modelo.
        """
        if not self.query_history:
            return "Sin queries previas"
        
        history_parts = []
        for tool_name, queries in self.query_history.items():
            if queries:
                recent_queries = queries[-2:] if len(queries) > 2 else queries
                history_parts.append(f"• {tool_name}: {', '.join(recent_queries)}")
        
        return "\n".join(history_parts)
    
    def _is_query_repeated(self, tool_name: str, query: str) -> bool:
        """
        Verifica si una query ya fue usada para una herramienta.
        """
        used_queries = self.query_history.get(tool_name, [])
        
        # Verificación exacta
        if query in used_queries:
            return True
        
        # Verificación de similitud (queries muy parecidas)
        for used_query in used_queries:
            if self._are_queries_similar(query, used_query):
                return True
        
        return False
    
    def _are_queries_similar(self, query1: str, query2: str, threshold: float = 0.8) -> bool:
        """
        Verifica si dos queries son muy similares.
        """
        # Normalizar queries
        q1_words = set(query1.lower().split())
        q2_words = set(query2.lower().split())
        
        # Calcular similitud de Jaccard
        intersection = len(q1_words & q2_words)
        union = len(q1_words | q2_words)
        
        if union == 0:
            return False
        
        similarity = intersection / union
        return similarity >= threshold
    
    def _update_query_history(self, step: TaskStep):
        """
        Actualiza el historial de queries para evitar repeticiones.
        """
        tool_name = step.tool_name
        query = step.query
        
        # Actualizar historial general
        if tool_name not in self.query_history:
            self.query_history[tool_name] = []
        self.query_history[tool_name].append(query)
        
        # Actualizar historial de éxito/fallo
        if step.status == TaskStatus.COMPLETED:
            if tool_name not in self.successful_queries:
                self.successful_queries[tool_name] = []
            self.successful_queries[tool_name].append(query)
            logger.info(f"Query exitosa registrada: {tool_name} -> {query}")
        elif step.status == TaskStatus.FAILED:
            if tool_name not in self.failed_queries:
                self.failed_queries[tool_name] = []
            self.failed_queries[tool_name].append(query)
            logger.info(f"Query fallida registrada: {tool_name} -> {query}")
    
    def _lightweight_reflection(self, current_plan: TaskPlan, user_message: str, iteration: int) -> Dict[str, Any]:
        """
        Reflexión optimizada que considera el historial de queries.
        """
        try:
            context = self._build_compact_context(current_plan.steps)
            
            # Información sobre queries
            total_queries = sum(len(queries) for queries in self.query_history.values())
            unique_tools = len(self.query_history)
            successful_queries = sum(len(queries) for queries in self.successful_queries.values())
            
            reflection_prompt = [
                {
                    "role": "system",
                    "content": """Eres un evaluador eficiente. Analiza el progreso y decide si continuar o finalizar.

EVALÚA:
1. ¿Tengo suficiente información para responder la pregunta original?
2. ¿El progreso es satisfactorio o estoy perdiendo tiempo?
3. ¿Necesito cambiar de estrategia?

RESPONDE JSON:
{
    "task_completed": true/false,
    "has_useful_info": true/false,
    "next_strategy": "descripción breve",
    "confidence": "high/medium/low",
    "should_pivot": true/false
}"""
                },
                {
                    "role": "user",
                    "content": f"""PREGUNTA ORIGINAL: {user_message}

PROGRESO ACTUAL: {context}

MÉTRICAS:
- Información recopilada: {len(self.execution_context)} elementos
- Queries ejecutadas: {total_queries} (éxitos: {successful_queries})
- Herramientas usadas: {unique_tools}
- Fallos consecutivos: {self.consecutive_failures}
- Iteración: {iteration + 1}/{self.max_iterations}

¿Debo continuar buscando información o tengo suficiente para responder?"""
                }
            ]
            
            response = self._get_model_response(reflection_prompt, max_tokens=300)
            SocketResponseHandler.emit_console_output(self.socket, response, 'pensamiento')
            reflection = self._parse_json_response(response)
            
            return reflection
            
        except Exception as e:
            logger.error(f"Error en reflexión: {e}")
            return {'task_completed': False, 'next_strategy': 'continuar', 'confidence': 'low'}
    
    # Métodos heredados sin cambios significativos
    def _quick_assessment(self) -> Dict[str, Any]:
        """Evaluación rápida basada en métricas."""
        has_useful_info = len(self.execution_context) > 0
        should_pivot = self.consecutive_failures >= 3
        
        return {
            'task_completed': False,
            'has_useful_info': has_useful_info,
            'should_pivot': should_pivot,
            'confidence': 'medium' if has_useful_info else 'low',
            'next_strategy': 'pivotar' if should_pivot else 'continuar'
        }
    
    def _get_cached_tools(self) -> List[str]:
        """Obtiene herramientas disponibles con cache."""
        current_time = time.time()
        
        if (self._tools_cache is None or 
            current_time - self._tools_cache_time > 30):
            
            if self.tools_manager:
                self._tools_cache = self.tools_manager.get_active_tools()
            else:
                self._tools_cache = []
            
            self._tools_cache_time = current_time
        
        return self._tools_cache or []
    
    def _update_metrics(self, step: TaskStep):
        """Actualiza métricas de uso de herramientas."""
        tool_name = step.tool_name
        self.tool_usage_count[tool_name] = self.tool_usage_count.get(tool_name, 0) + 1
        
        if step.status == TaskStatus.COMPLETED:
            self.last_successful_tool = tool_name
    
    def _cache_result(self, step: TaskStep, iteration: int):
        """Cachea el resultado de un paso exitoso."""
        self.execution_context[step.id] = {
            'result': step.result,
            'tool_used': step.tool_name,
            'iteration': iteration,
            'timestamp': time.time()
        }
    
    def _should_stop_early(self, iteration: int, execution_results: Dict[str, Any]) -> bool:
        """Determina si debe parar temprano basado en métricas."""
        if len(self.execution_context) >= 3 and iteration >= 3:
            return True
        
        if self.consecutive_failures >= 4:
            return True
        
        if iteration >= 6:
            recent_successes = len([s for s in execution_results['completed_steps'][-3:] 
                                  if s.status == TaskStatus.COMPLETED])
            return recent_successes == 0
        
        return False
    
    def _should_force_reflection(self, iteration: int) -> bool:
        """Determina si forzar reflexión basado en condiciones."""
        return (self.consecutive_failures >= 2 or 
                iteration >= 6 or 
                len(self.execution_context) >= 2)
    
    def _build_compact_context(self, steps: List[TaskStep]) -> str:
        """Construye contexto compacto de pasos."""
        if not steps:
            return "Sin pasos ejecutados"
        
        context_parts = []
        for step in steps[-3:]:
            status = "✅" if step.status == TaskStatus.COMPLETED else "❌"
            context_parts.append(f"{status} {step.tool_name}: {step.query}")
        
        return " | ".join(context_parts)
    
    def _get_model_response(self, messages: List[Dict], max_tokens: int = 8192) -> str:
        """Obtiene respuesta del modelo con streaming."""
        response = ""
        try:
            # Añadir '/no_think' al final del último mensaje del usuario
            if messages and messages[-1]['role'] == 'user':
                messages = messages.copy()
                messages[-1] = messages[-1].copy()
                messages[-1]['content'] = f"{messages[-1]['content'].rstrip()} /no_think"

            for chunk in self.model.create_chat_completion(
                messages=messages, 
                max_tokens=max_tokens, 
                stream=True, 
                temperature=0.1
            ):
                if 'content' in chunk['choices'][0]['delta']:
                    response += chunk['choices'][0]['delta']['content']
        except Exception as e:
            logger.error(f"Error obteniendo respuesta del modelo: {e}")
        
        return response
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta JSON con fallback."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"Error parseando JSON: {e}")
        
        return {
            'task_completed': False,
            'has_useful_info': len(self.execution_context) > 0,
            'next_strategy': 'continuar',
            'confidence': 'medium',
            'should_pivot': False
        }
    
    def _display_current_step_compact(self, step: TaskStep, step_number: int, emit_status_func):
        """Muestra información compacta del paso actual."""
        step_text = f"**🔍 PASO {step_number}:** {step.tool_name} → `{step.query}`"
        SocketResponseHandler.emit_console_output(self.socket, step_text, 'pensamiento')

    
    def _display_execution_stats_compact(self, execution_results: Dict[str, Any], emit_status_func):
        """Muestra estadísticas compactas."""
        stats = (f"📊 **ESTADÍSTICAS:** {len(execution_results['completed_steps'])} completados | "
                f"{len(execution_results['failed_steps'])} fallidos | "
                f"{execution_results['execution_time']:.1f}s")
        SocketResponseHandler.emit_console_output(self.socket, stats, 'info')
    
    def _extract_user_message(self, original_prompt: List[Dict]) -> str:
        """Extrae el mensaje del usuario del prompt original"""
        for message in reversed(original_prompt):
            if message['role'] == 'user':
                return message['content']
        return "Tarea no especificada"
    
    def _create_initial_plan(self, task_analysis: Dict[str, Any], user_message: str) -> TaskPlan:
        """Crea un plan inicial mínimo"""
        return TaskPlan(
            task_description=user_message,
            steps=[],
            context={
                'analysis': task_analysis,
                'user_message': user_message,
                'adaptive_mode': True,
                'optimized': True,
                'model_driven_queries': True
            },
            created_at=datetime.datetime.now(),
            status=TaskStatus.IN_PROGRESS
        )
    
    def _execute_step(self, step: TaskStep, emit_status_func):
        """Ejecuta un paso individual"""
        try:
            step.status = TaskStatus.IN_PROGRESS
            
            if not self.tools_manager or not self.tools_manager.is_tool_active(step.tool_name):
                step.status = TaskStatus.FAILED
                step.error = f"Herramienta '{step.tool_name}' no disponible"
                return
            
            tool_result = self.tool_registry.execute_tool(step.tool_name, step.query)
            
            if tool_result and hasattr(tool_result, 'success') and tool_result.success:
                step.result = str(tool_result.result if hasattr(tool_result, 'result') else tool_result)
                step.status = TaskStatus.COMPLETED
                safe_emit_tool_result(self.socket, step.tool_name, step.query, step.result)
            else:
                step.status = TaskStatus.FAILED
                error_msg = "La herramienta no devolvió un resultado válido"
                if tool_result and hasattr(tool_result, 'error'):
                    error_msg = str(tool_result.error)
                step.error = error_msg
                
        except Exception as e:
            error_clean = clean_error_message(str(e))
            step.status = TaskStatus.FAILED
            step.error = error_clean
            logger.error(f"Error ejecutando paso {step.id}: {error_clean}")
    
    def _calculate_final_stats(self, execution_results: Dict[str, Any], start_time: float):
        """Calcula estadísticas finales"""
        execution_results['execution_time'] = time.time() - start_time
        
        if execution_results['total_steps'] > 0:
            execution_results['success_rate'] = len(execution_results['completed_steps']) / execution_results['total_steps']
        else:
            execution_results['success_rate'] = 0.0
        
        execution_results['adaptations_made'] = len(execution_results['reflections'])
    
    def _generate_clean_final_response(self, user_message: str, execution_results: Dict[str, Any], emit_status_func) -> str:
        """
        Genera respuesta final optimizada con menos tokens.
        """
        try:
            # Permitir frenar la respuesta final si el usuario lo solicita
            if self.assistant and getattr(self.assistant, 'stop_emit', False):
                emit_status_func("Respuesta final detenida por el usuario", 'info')
                return "Respuesta final detenida por el usuario."
            # Recopilar información de forma más eficiente
            gathered_info = []
            images = []
            links = []
            
            for step_data in self.execution_context.values():
                if isinstance(step_data, dict) and step_data.get('result'):
                    result = step_data['result'].strip()
                    if len(result) > 10:
                        gathered_info.append(result)
                        images.extend(re.findall(r'(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp))', result, re.IGNORECASE))
                        links.extend(re.findall(r'(https?://[^\s]+)', result))
            # Prompt optimizado más corto
            final_prompt = [
                {
                    "role": "system",
                    "content": """Responde de forma profesional y directa. \n\nREGLAS:\n- NO menciones procesos de búsqueda\n- NO uses enlaces repetidos.\n- NO uses listas numeradas\n- Integra toda la información disponible\n- Imágenes: ![titulo](url)\n- Enlaces normales: [titulo](url)\n- YouTube/TikTok: texto plano sin formato\n- Sé autoritativo y confiado"""
                },
                {
                    "role": "user",
                    "content": f"""PREGUNTA: {user_message}\n\nINFORMACIÓN: {' '.join(gathered_info[:3])}\n\nIMÁGENES: {' '.join(images[:5])}\n\nENLACES: {' '.join(links[:5])}\n\nResponde integrando toda la información (imagenes, enlaces, etc) de forma natural. """
                }
            ]
            # Obtener el mensaje de usuario original para el cálculo de tokens
            user_question = user_message
            if hasattr(self, 'original_prompt'):
                for message in reversed(self.original_prompt):
                    if message['role'] == 'user':
                        user_question = message['content']
                        break
            tokensInput = user_question.encode()
            tokens = self.model.tokenize(tokensInput)
            total_user_tokens = len(tokens)
            def safe_stop_condition():
                try:
                    return self.assistant and getattr(self.assistant, 'stop_emit', False)
                except Exception:
                    return False
            response_queue = getattr(self, 'response_queue', None)
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=self.model,
                messages=final_prompt,
                socket=self.socket,
                max_tokens=8192,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=response_queue,
                stop_condition=safe_stop_condition
            )
            emit_status_func("🎯 **RESPUESTA FINAL ENVIADA**", 'info')
            execution_results['completed_steps'].append({
                'type': 'final_response',
                'result': '[Respuesta enviada por streaming]'
            })
            return response_completa
        except Exception as e:
            logger.error(f"Error generando respuesta final: {e}")
            fallback = "No pude generar una respuesta completa debido a limitaciones técnicas."
            emit_status_func(fallback, 'info')
            return fallback