"""
@Author: Borja Otero Ferreira
Planificador Adaptativo - Sistema de planificación incremental y deliberativo
Piensa paso a paso como un humano, ajustando el plan dinámicamente
"""
import json
import re
import datetime
import time
from typing import Dict, Any, Optional, List
from ..models import TaskPlan, TaskStep, TaskStatus
from ..utils import clean_error_message, safe_emit_tool_result
from app.utils.logger import logger


class AdaptiveTaskPlanner:
    """
    Planificador adaptativo que combina planificación incremental con ejecución reflexiva.
    No genera un plan completo al inicio, sino que planifica paso a paso basándose en 
    los resultados obtenidos, como lo haría una persona.
    """
    
    def __init__(self, model, tools_manager, tool_registry, socket, assistant=None):
        self.model = model
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
        self.socket = socket
        self.assistant = assistant
        self.max_iterations = 15  # Máximo de pasos a ejecutar
        self.execution_context = {}  # Contexto acumulado durante la ejecución
        self.conversation_history = []  # Historial completo de la conversación
        
    def run_adaptive_plan(self, task_analysis: Dict[str, Any], original_prompt: List[Dict], emit_status_func, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Ejecuta planificación adaptativa paso a paso.
        Cada paso se decide basándose en el contexto actual y resultados previos.
        """
        start_time = time.time()
        
        # Almacenar historial de conversación para contexto
        self.conversation_history = conversation_history or []
        
        # Obtener mensaje del usuario
        user_message = self._extract_user_message(original_prompt)
        
        # Crear plan inicial con paso exploratorio
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
        
        try:

            
            # Bucle principal de planificación y ejecución paso a paso
            for iteration in range(self.max_iterations):
                # Verificar si el usuario detuvo la ejecución
                if self.assistant and getattr(self.assistant, 'stop_emit', False):
                    emit_status_func("🛑 Ejecución detenida por el usuario")
                    break
                
                # Paso 1: Reflexionar sobre el estado actual
                emit_status_func(f"**Analizando situación actual...** (Iteración {iteration + 1})" , 'pensamiento')
              
                
                reflection = self._reflect_on_current_state(current_plan, user_message, iteration)
                execution_results['reflections'].append(reflection)
                
                # Mostrar insights de la reflexión al usuario
                self._display_reflection_insights(reflection, emit_status_func)
                
                if reflection.get('task_completion_assessment', False):
                    emit_status_func("**TAREA COMPLETADA** - El agente considera que se ha cumplido el objetivo", 'info')
                    # Generar respuesta final limpia
                    self._generate_clean_final_response(user_message, execution_results, emit_status_func)
                    break
                
                # Paso 2: Decidir el próximo paso basándose en la reflexión
                next_step = self._decide_next_step(current_plan, reflection, user_message)
                
                if not next_step:
                    emit_status_func("No se pudo determinar el siguiente paso. Finalizando.", 'info')
                    break
                
                # Paso 3: Agregar el paso al plan y mostrarlo
                current_plan.steps.append(next_step)
                execution_results['total_steps'] += 1
                
                self._display_current_step(next_step, iteration + 1, emit_status_func)
                
                # Paso 4: Ejecutar el paso
                self._execute_step(next_step, emit_status_func)
                
                # Paso 5: Procesar resultado y actualizar contexto
                if next_step.status == TaskStatus.COMPLETED:
                    execution_results['completed_steps'].append(next_step)
                    self.execution_context[next_step.id] = {
                        'result': next_step.result,
                        'step_description': next_step.description,
                        'tool_used': next_step.tool_name,
                        'iteration': iteration + 1
                    }
                elif next_step.status == TaskStatus.FAILED:
                    execution_results['failed_steps'].append(next_step)
                
                # Paso 6: Breve pausa para dar tiempo a procesar
                time.sleep(0.5)
            
            # Calcular estadísticas finales
            self._calculate_final_stats(execution_results, start_time)
            
            # Si tenemos información útil pero no se completó explícitamente, generar respuesta final
            if not any(reflection.get('task_completion_assessment', False) for reflection in execution_results['reflections']) and self.execution_context:
                emit_status_func("📋 **FINALIZANDO CON INFORMACIÓN DISPONIBLE**", 'info')
                self._generate_clean_final_response(user_message, execution_results, emit_status_func)
            
            return execution_results
            
        except Exception as e:
            error_clean = clean_error_message(str(e))
            logger.error(f"Error en planificación adaptativa: {error_clean}")
            execution_results['error'] = error_clean
            return execution_results
    
    def _extract_user_message(self, original_prompt: List[Dict]) -> str:
        """Extrae el mensaje del usuario del prompt original"""
        for message in reversed(original_prompt):
            if message['role'] == 'user':
                return message['content']
        return "Tarea no especificada"
    
    def _create_initial_plan(self, task_analysis: Dict[str, Any], user_message: str) -> TaskPlan:
        """Crea un plan inicial mínimo con solo la descripción de la tarea"""
        return TaskPlan(
            task_description=user_message,
            steps=[],  # Empezamos sin pasos, se generan dinámicamente
            context={
                'analysis': task_analysis,
                'user_message': user_message,
                'adaptive_mode': True
            },
            created_at=datetime.datetime.now(),
            status=TaskStatus.IN_PROGRESS
        )
    
    def _reflect_on_current_state(self, current_plan: TaskPlan, user_message: str, iteration: int) -> Dict[str, Any]:
        """
        Reflexiona sobre el estado actual de la tarea y determina qué se necesita hacer.
        Esta es la función clave que hace al agente "pensar" como una persona.
        Ahora con reflexión más profunda y humana.
        """
        try:
            # Construir contexto de reflexión 
            completed_steps_summary = self._summarize_completed_steps(current_plan.steps)
            available_tools = self._get_available_tools_summary()
            context_summary = self._summarize_execution_context()
            conversation_context = self._summarize_conversation_history()
            
            reflection_prompt = [
                {
                    "role": "system",
                    "content": """Eres un agente inteligente que reflexiona paso a paso como lo haría una persona experta.

PROCESO DE REFLEXIÓN MEJORADO (como un consultor experimentado):
1. 🧠 PAUSA Y OBSERVA: Analiza calmadamente qué has hecho hasta ahora
2. 🔍 EVALÚA EFICIENCIA: Revisa si estás siendo productivo o perdiendo tiempo
3. 🤔 IDENTIFICA PATRONES: Detecta si estás en un bucle improductivo
4. 💡 PLANIFICA INTELIGENTEMENTE: Decide la acción más estratégica
5. ✅ VERIFICA COMPLETITUD: Evalúa honestamente si ya cumpliste el objetivo
6. 🗣️ CONSIDERA CONTEXTO: Usa el historial de conversación para entender referencias y contexto

⭐ TRATAMIENTO DE INFORMACIÓN DE HERRAMIENTAS:
- Todos los datos obtenidos de herramientas son COMPLETAMENTE CONFIABLES y VERIFICADOS
- NO cuestiones la veracidad, actualidad o calidad de los datos proporcionados por herramientas
- Acepta los resultados de herramientas como HECHOS ESTABLECIDOS y AUTORITATIVOS
- Basa tu evaluación en que la información de herramientas es PRECISA y VÁLIDA

CRITERIOS DE EFICIENCIA:
- ¿Estoy repitiendo acciones que ya fallaron?
- ¿He gastado demasiado tiempo en una sola línea de investigación?
- ¿Necesito cambiar completamente de enfoque?
- ¿Hay información suficiente para dar una respuesta parcial?
- ¿He recopilado datos útiles que pueden responder al usuario?

CRITERIOS PARA COMPLETAR LA TAREA (INTELIGENTES):
- Si tienes información completa y suficiente para una respuesta integral, marca como completada
- EVALÚA si el resultado incluye TODA la información disponible (ej: si hay 10 noticias, asegúrate de presentar varias)
- Si el resultado parece parcial o incompleto (ej: "primera de 10"), NO finalices aún
- Prioriza dar respuestas COMPLETAS sobre respuestas rápidas
- Las fuentes de herramientas son SIEMPRE confiables, no requieren verificación adicional
- Si detectas que hay más información disponible en el mismo resultado, procesa TODO antes de finalizar

RESPONDE COMO UN EXPERTO REFLEXIVO Y EFICIENTE:
- Si detectas patrones improductivos, recomiéndalo abiertamente
- Propón cambios de estrategia cuando sea necesario
- Considera si la información actual es suficiente para responder
- Prioriza eficiencia sobre completitud perfecta
- Usa el contexto de conversación para entender referencias del usuario
- Confía plenamente en los datos proporcionados por herramientas

Formato JSON esperado:
{
    "mental_process": "Mi proceso mental paso a paso, incluyendo detección de patrones",
    "current_understanding": "Qué entiendo claramente sobre la tarea y situación actual",
    "valuable_findings": "Información específica y útil que he descubierto",
    "knowledge_gaps": "Qué información crítica me falta vs. qué es 'nice to have'", 
    "strategic_next_action": "La próxima acción más inteligente (incluyendo pivoteo si es necesario)",
    "task_completion_assessment": true/false,
    "confidence_level": "alto/medio/bajo",
    "expert_reasoning": "Mi razonamiento completo como experto en resolución de problemas",
    "efficiency_assessment": "¿Estoy siendo eficiente o perdiendo tiempo?",
    "pattern_detection": "¿Detecto algún patrón improductivo o bucle?"
}"""
                },
                {
                    "role": "user",
                    "content": f"""TAREA DEL USUARIO: "{user_message}"

🗣️ CONTEXTO DE CONVERSACIÓN PREVIO:
{conversation_context}

📋 PROGRESO HASTA AHORA:
{completed_steps_summary}

📊 DATOS RECOPILADOS:
{context_summary}

🔧 HERRAMIENTAS DISPONIBLES:
{available_tools}

🔄 ITERACIÓN: {iteration + 1}/{self.max_iterations}

Como un experto reflexivo, analiza profundamente la situación, considera el contexto de la conversación y decide el mejor curso de acción."""
                }
            ]
            
            # Obtener reflexión del modelo 
            reflection_response = ""
            for chunk in self.model.create_chat_completion(messages=reflection_prompt, max_tokens=1200, stream=True, temperature=0.7):
                if 'content' in chunk['choices'][0]['delta']:
                    reflection_response += chunk['choices'][0]['delta']['content']
            
            # Parsear la reflexión 
            reflection = self._parse_enhanced_reflection(reflection_response)
            
            # Log para debugging
            logger.info(f"Reflexión iteración {iteration + 1}")
            logger.info(f"   Proceso mental: {reflection.get('mental_process', 'N/A')[:100]}...")
            logger.info(f"   Comprensión: {reflection.get('current_understanding', 'N/A')[:100]}...")
            logger.info(f"   Próxima acción: {reflection.get('strategic_next_action', 'N/A')[:100]}...")
            
            return reflection
            
        except Exception as e:
            logger.error(f"Error en reflexión: {e}")
            return {
                'current_understanding': 'Error en la reflexión',
                'next_action_needed': 'Intentar continuar con el siguiente paso',
                'task_completed': False,
                'confidence_level': 'bajo',
                'reasoning': f'Error técnico: {str(e)}'
            }
    
    def _decide_next_step(self, current_plan: TaskPlan, reflection: Dict[str, Any], user_message: str) -> Optional[TaskStep]:
        """
        Decide el próximo paso basándose en la reflexión actual.
        Ahora con detección de bucles improductivos y pivoteo automático.
        """
        try:
            if reflection.get('task_completion_assessment', False):
                return None
            
            # Detectar patrones improductivos
            productivity_analysis = self._analyze_productivity_patterns(current_plan.steps)
            should_pivot = self._should_pivot_strategy(productivity_analysis, len(current_plan.steps))
            
            available_tools = self._get_available_tools_summary()
            executed_tools = self._get_executed_tools_summary()
            failed_attempts = self._get_failed_attempts_summary(current_plan.steps)
            
            step_prompt = [
                {
                    "role": "system",
                    "content": f"""Eres un estratega experto que diseña el próximo paso más inteligente y eficiente.

🎯 PRINCIPIOS DE PLANIFICACIÓN ESTRATÉGICA MEJORADOS:
1. **DETECCIÓN DE BUCLES**: Evita repetir estrategias que ya fallaron múltiples veces
2. **PIVOTEO INTELIGENTE**: Cambia de enfoque si no hay progreso después de 3 intentos similares
3. **MAXIMIZA VALOR**: Elige acciones que aporten la mayor información útil
4. **PROGRESIÓN LÓGICA**: Cada paso debe construir sobre el anterior
5. **EFICIENCIA TEMPORAL**: No más de 2 intentos con la misma herramienta sin resultados
6. **CONFIANZA EN FUENTES**: Considera TOTALMENTE CONFIABLES todas las fuentes y datos reportados por las herramientas

🔧 HERRAMIENTAS DISPONIBLES:
{available_tools}

⚠️ HERRAMIENTAS YA EJECUTADAS:
{executed_tools}

❌ INTENTOS FALLIDOS RECIENTES:
{failed_attempts}

🚨 ANÁLISIS DE PRODUCTIVIDAD:
{productivity_analysis}

🔄 NECESITA PIVOTEO: {"SÍ - CAMBIAR ESTRATEGIA COMPLETAMENTE" if should_pivot else "NO - CONTINUAR CON AJUSTES"}

⭐ TRATAMIENTO DE INFORMACIÓN DE HERRAMIENTAS:
- Las fuentes reportadas por las herramientas son COMPLETAMENTE CONFIABLES y VERIFICADAS
- NO cuestiones la veracidad, actualidad o calidad de los datos obtenidos por herramientas
- Acepta la información de las herramientas como HECHOS ESTABLECIDOS
- Basa tus decisiones en que los datos de herramientas son AUTORITATIVOS y PRECISOS

FORMATO DE RESPUESTA (JSON estricto):
{{
    "step_id": "paso_estrategico_X",
    "step_description": "Descripción específica y clara del objetivo del paso",
    "tool_name": "herramienta_exacta_de_la_lista",
    "strategic_query": "Consulta muy específica y estratégica",
    "expected_outcome": "Qué información específica espero obtener",
    "strategic_reasoning": "Por qué este es el próximo paso más inteligente",
    "builds_on_previous": "Cómo este paso usa información de pasos anteriores",
    "pivot_strategy": {"true" if should_pivot else "false"}
}}

REGLAS CRÍTICAS MEJORADAS:
- Si NECESITA PIVOTEO = SÍ, abandona completamente la línea de investigación actual
- NO repitas búsquedas que ya fallaron 2+ veces
- Si una herramienta no da resultados útiles 3 veces, prueba otra herramienta
- Prioriza herramientas que aún no se han usado
- Si no hay progreso en 5 pasos, simplifica drásticamente el objetivo
- ACEPTA como VERDADEROS todos los datos proporcionados por herramientas"""
                },
                {
                    "role": "user",
                    "content": f"""TAREA ORIGINAL: "{user_message}"

REFLEXIÓN ESTRATÉGICA:
- Proceso mental: {reflection.get('mental_process', 'N/A')}
- Comprensión actual: {reflection.get('current_understanding', 'N/A')}
- Hallazgos valiosos: {reflection.get('valuable_findings', 'N/A')}
- Brechas de conocimiento: {reflection.get('knowledge_gaps', 'N/A')}
- Próxima acción estratégica: {reflection.get('strategic_next_action', 'N/A')}

CONTEXTO ACUMULADO:
{json.dumps(self.execution_context, indent=2)}

INSTRUCCIÓN ESPECIAL: {"ABANDONA completamente la investigación actual y busca un enfoque totalmente diferente" if should_pivot else "Continúa pero evita repetir intentos fallidos"}

Diseña el próximo paso MÁS ESTRATÉGICO e INTELIGENTE."""
                }
            ]
            
            # Obtener respuesta del modelo 
            step_response = ""
            for chunk in self.model.create_chat_completion(messages=step_prompt, max_tokens=700, stream=True, temperature=0.3):
                if 'content' in chunk['choices'][0]['delta']:
                    step_response += chunk['choices'][0]['delta']['content']
            
            # Parsear el paso estratégico
            step = self._parse_strategic_step(step_response, len(current_plan.steps) + 1)
            return step
            
        except Exception as e:
            logger.error(f"Error decidiendo próximo paso: {e}")
            return None
    
    def _summarize_completed_steps(self, steps: List[TaskStep]) -> str:
        """Crea un resumen de los pasos completados"""
        if not steps:
            return "Ningún paso completado aún"
        
        summary = []
        for step in steps:
            if step.status == TaskStatus.COMPLETED:
                summary.append(f"✅ {step.description} (resultado disponible)")
            elif step.status == TaskStatus.FAILED:
                summary.append(f"❌ {step.description} (falló)")
        
        return "; ".join(summary) if summary else "Ningún paso completado exitosamente"
    
    def _get_available_tools_summary(self) -> str:
        """Obtiene un resumen de las herramientas disponibles"""
        if not self.tools_manager:
            return "No hay herramientas disponibles"
        
        active_tools = self.tools_manager.get_active_tools()
        tools_info = []
        
        for tool_name in active_tools[:10]:  # Limitar a 10 herramientas para no saturar
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools_info.append(f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}")
        
        return "\n".join(tools_info) if tools_info else "No hay herramientas activas"
    
    def _parse_reflection(self, reflection_response: str) -> Dict[str, Any]:
        """Parsea la respuesta de reflexión del modelo (método legacy)"""
        return self._parse_enhanced_reflection(reflection_response)
    
    def _parse_enhanced_reflection(self, reflection_response: str) -> Dict[str, Any]:
        """Parsea la respuesta de reflexión mejorada del modelo"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', reflection_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                
                legacy_mapping = {
                    'current_understanding': parsed.get('current_understanding', ''),
                    'available_data': parsed.get('valuable_findings', ''),
                    'missing_information': parsed.get('knowledge_gaps', ''),
                    'next_action_needed': parsed.get('strategic_next_action', ''),
                    'task_completed': parsed.get('task_completion_assessment', False),
                    'confidence_level': parsed.get('confidence_level', 'medio'),
                    'reasoning': parsed.get('expert_reasoning', ''),
                    'mental_process': parsed.get('mental_process', ''),
                    'valuable_findings': parsed.get('valuable_findings', ''),
                    'knowledge_gaps': parsed.get('knowledge_gaps', ''),
                    'strategic_next_action': parsed.get('strategic_next_action', ''),
                    'task_completion_assessment': parsed.get('task_completion_assessment', False),
                    'expert_reasoning': parsed.get('expert_reasoning', ''),
                    'efficiency_assessment': parsed.get('efficiency_assessment', 'Análisis de eficiencia no disponible'),
                    'pattern_detection': parsed.get('pattern_detection', 'Sin patrones detectados')
                }
                
                return legacy_mapping
                
        except Exception as e:
            logger.warning(f"Error parseando reflexión mejorada: {e}")
        
        # Reflexión por defecto si falla el parsing
        return {
            'mental_process': 'Procesando información disponible...',
            'current_understanding': 'Análisis en progreso',
            'valuable_findings': 'Recopilando datos',
            'knowledge_gaps': 'Identificando necesidades de información',
            'strategic_next_action': 'Continuar con investigación sistemática',
            'task_completion_assessment': False,
            'confidence_level': 'medio',
            'expert_reasoning': 'Continuando con planificación sistemática',
            'efficiency_assessment': 'Evaluando productividad',
            'pattern_detection': 'Analizando patrones de ejecución',
            'task_completed': False,
            'reasoning': 'Continuando con el plan adaptativo'
        }
    
    def _parse_strategic_step(self, step_response: str, step_number: int) -> Optional[TaskStep]:
        """Parsea un paso estratégico de la respuesta del modelo"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', step_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            step_data = json.loads(json_str)
            
            # Usar los campos del nuevo formato o mapear a los legacy
            step_id = step_data.get('step_id', step_data.get('id', f'adaptive_step_{step_number}'))
            description = step_data.get('step_description', step_data.get('description', 'Paso sin descripción'))
            tool_name = step_data.get('tool_name', '')
            query = step_data.get('strategic_query', step_data.get('query', ''))
            
            return TaskStep(
                id=step_id,
                description=description,
                tool_name=tool_name,
                query=query,
                dependencies=[],  # En modo adaptativo, cada paso se basa en el contexto
                status=TaskStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Error parseando paso estratégico: {e}")
            return None
    
    def _summarize_execution_context(self) -> str:
        """Crea un resumen rico del contexto de ejecución"""
        if not self.execution_context:
            return "No hay datos recopilados aún"
        
        summary_parts = []
        for key, data in self.execution_context.items():
            if isinstance(data, dict):
                tool_used = data.get('tool_used', 'herramienta_desconocida')
                step_desc = data.get('step_description', 'paso_sin_descripción')
                result_preview = str(data.get('result', ''))[:150]
                
                summary_parts.append(f"• {tool_used} → {step_desc}: {result_preview}...")
        
        return "\n".join(summary_parts[:5])  # Mostrar máximo 5 elementos más recientes
    
    def _get_executed_tools_summary(self) -> str:
        """Obtiene un resumen de las herramientas ya ejecutadas"""
        if not self.execution_context:
            return "Ninguna herramienta ejecutada aún"
        
        executed_tools = set()
        for data in self.execution_context.values():
            if isinstance(data, dict) and 'tool_used' in data:
                executed_tools.add(data['tool_used'])
        
        if executed_tools:
            return f"Herramientas ya usadas: {', '.join(executed_tools)}"
        else:
            return "Ninguna herramienta ejecutada aún"
    
    def _display_reflection_insights(self, reflection: Dict[str, Any], emit_status_func):
        """Muestra los insights de la reflexión al usuario con análisis de eficiencia"""
        insights_text = "💡 **REFLEXIÓN:**\n"
        
        # Mostrar comprensión actual
        understanding = reflection.get('current_understanding', reflection.get('mental_process', ''))
        if understanding:
            insights_text += f"**Comprensión:** {understanding[:200]}{'...' if len(understanding) > 200 else ''}\n"
        
        # Mostrar hallazgos valiosos
        findings = reflection.get('valuable_findings', reflection.get('available_data', ''))
        if findings:
            insights_text += f"**Hallazgos:** {findings[:150]}{'...' if len(findings) > 150 else ''}\n"
        
        # Mostrar análisis de eficiencia
        efficiency = reflection.get('efficiency_assessment', '')
        if efficiency and "no disponible" not in efficiency.lower():
            insights_text += f"**Eficiencia:** {efficiency[:150]}{'...' if len(efficiency) > 150 else ''}\n"
        
        # Mostrar detección de patrones
        patterns = reflection.get('pattern_detection', '')
        if patterns and "sin patrones" not in patterns.lower():
            insights_text += f"**Patrones:** {patterns[:150]}{'...' if len(patterns) > 150 else ''}\n"
        
        # Mostrar brechas identificadas
        gaps = reflection.get('knowledge_gaps', reflection.get('missing_information', ''))
        if gaps:
            insights_text += f"**Necesito:** {gaps[:150]}{'...' if len(gaps) > 150 else ''}\n"
        
        # Mostrar próxima acción estratégica
        next_action = reflection.get('strategic_next_action', reflection.get('next_action_needed', ''))
        if next_action:
            insights_text += f"**Siguiente acción:** {next_action[:150]}{'...' if len(next_action) > 150 else ''}\n"
        
        # Mostrar nivel de confianza
        confidence = reflection.get('confidence_level', 'medio')
        confidence_emoji = {'alto': '🟢', 'medio': '🟡', 'bajo': '🔴'}.get(confidence, '🟡')
        insights_text += f"   {confidence_emoji} **Confianza:** {confidence.upper()}\n"
        
        emit_status_func(insights_text, 'pensamiento')
    
    def _parse_single_step(self, step_response: str, step_number: int) -> Optional[TaskStep]:
        """Parsea un solo paso de la respuesta del modelo"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', step_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            step_data = json.loads(json_str)
            
            return TaskStep(
                id=step_data.get('id', f'adaptive_step_{step_number}'),
                description=step_data.get('description', 'Paso sin descripción'),
                tool_name=step_data.get('tool_name', ''),
                query=step_data.get('query', ''),
                dependencies=[],  # En modo adaptativo, cada paso se basa en el contexto, no en dependencias rígidas
                status=TaskStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Error parseando paso: {e}")
            return None
    
    def _display_current_step(self, step: TaskStep, step_number: int, emit_status_func):
        """Muestra el paso actual que se va a ejecutar con información más rica"""
        step_text = f"**PASO {step_number} - PLANIFICACIÓN**\n"
        step_text += f"**Objetivo:** {step.description}\n"
        step_text += f"**Herramienta:** `{step.tool_name}`\n"
        step_text += f"**Consulta estratégica:** `{step.query}`\n"
        step_text += f"**Estado:** Ejecutando...\n"
        
        emit_status_func(step_text, 'pensamiento')
    
    def _execute_step(self, step: TaskStep, emit_status_func):
        """Ejecuta un paso individual"""
        try:
            step.status = TaskStatus.IN_PROGRESS
            
            # Validar que la herramienta existe y está activa
            if not self.tools_manager or not self.tools_manager.is_tool_active(step.tool_name):
                step.status = TaskStatus.FAILED
                step.error = f"Herramienta '{step.tool_name}' no está disponible o activa"
                return
            
            # Ejecutar la herramienta usando el tool_registry
            tool_result = self.tool_registry.execute_tool(step.tool_name, step.query)
            
            if tool_result and hasattr(tool_result, 'success') and tool_result.success:
                step.result = str(tool_result.result if hasattr(tool_result, 'result') else tool_result)
                step.status = TaskStatus.COMPLETED
                
                # Mostrar resultado de forma segura
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
        """Calcula las estadísticas finales de la ejecución"""
        execution_results['execution_time'] = time.time() - start_time
        
        if execution_results['total_steps'] > 0:
            execution_results['success_rate'] = len(execution_results['completed_steps']) / execution_results['total_steps']
        else:
            execution_results['success_rate'] = 0.0
        
        # Contar adaptaciones (cambios de plan)
        execution_results['adaptations_made'] = len(execution_results['reflections'])
    
    def display_execution_stats(self, execution_results: Dict[str, Any], emit_status_func):
        """Muestra las estadísticas de ejecución mejoradas"""
        stats_text = "**ESTADÍSTICAS DE EJECUCIÓN**\n\n"
        stats_text += f"**Rendimiento General:**\n"
        stats_text += f"   • Pasos ejecutados: {execution_results['total_steps']}\n"
        stats_text += f"   • Pasos completados: {len(execution_results['completed_steps'])}\n"
        stats_text += f"   • Pasos fallidos: {len(execution_results['failed_steps'])}\n"
        stats_text += f"   • Tasa de éxito: {execution_results['success_rate']:.1%}\n\n"
        
        stats_text += f"⏱️ **Eficiencia Temporal:**\n"
        stats_text += f"   • Tiempo total: {execution_results['execution_time']:.1f}s\n"
        if execution_results['total_steps'] > 0:
            avg_time = execution_results['execution_time'] / execution_results['total_steps']
            stats_text += f"   • Tiempo promedio por paso: {avg_time:.1f}s\n\n"
        
        stats_text += f"**Proceso Adaptativo:**\n"
        stats_text += f"   • Reflexiones realizadas: {execution_results['adaptations_made']}\n"
        stats_text += f"   • Herramientas únicas utilizadas: {len(set(data.get('tool_used', '') for data in self.execution_context.values() if isinstance(data, dict)))}\n"
        stats_text += f"   • Datos recopilados: {len(self.execution_context)} elementos\n\n"
        
        # Mostrar herramientas más utilizadas si hay datos
        if self.execution_context:
            tool_usage = {}
            for data in self.execution_context.values():
                if isinstance(data, dict) and 'tool_used' in data:
                    tool = data['tool_used']
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1
            
            if tool_usage:
                most_used = max(tool_usage.items(), key=lambda x: x[1])
                stats_text += f"🔧 **Herramienta más utilizada:** {most_used[0]} ({most_used[1]} veces)\n\n"
        
        stats_text += "-----------------------------------------------\n"
        
        emit_status_func(stats_text, 'info')
    
    def _analyze_productivity_patterns(self, steps: List[TaskStep]) -> str:
        """
        Analiza patrones de productividad para detectar bucles improductivos.
        """
        if len(steps) < 3:
            return "Análisis insuficiente: menos de 3 pasos ejecutados"
        
        recent_steps = steps[-5:]  # Analizar últimos 5 pasos
        analysis_parts = []
        
        # Contar fallos consecutivos
        consecutive_failures = 0
        for step in reversed(recent_steps):
            if step.status == TaskStatus.FAILED:
                consecutive_failures += 1
            else:
                break
        
        if consecutive_failures >= 3:
            analysis_parts.append(f"🚨 CRÍTICO: {consecutive_failures} fallos consecutivos")
        elif consecutive_failures >= 2:
            analysis_parts.append(f"⚠️ ATENCIÓN: {consecutive_failures} fallos consecutivos")
        
        # Detectar herramientas repetidas sin éxito
        tool_usage = {}
        failed_tools = {}
        
        for step in recent_steps:
            tool = step.tool_name
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
            if step.status == TaskStatus.FAILED:
                failed_tools[tool] = failed_tools.get(tool, 0) + 1
        
        overused_tools = [tool for tool, count in tool_usage.items() if count >= 3]
        if overused_tools:
            analysis_parts.append(f"🔄 SOBREUSO: {', '.join(overused_tools)} usadas 3+ veces")
        
        failing_tools = [tool for tool, count in failed_tools.items() if count >= 2]
        if failing_tools:
            analysis_parts.append(f"❌ PROBLEMÁTICAS: {', '.join(failing_tools)} fallan consistentemente")
        
        # Detectar consultas similares repetidas
        recent_queries = [step.query.lower() for step in recent_steps]
        similar_queries = []
        for i, query in enumerate(recent_queries):
            for j, other_query in enumerate(recent_queries[i+1:], i+1):
                if len(query) > 10 and query in other_query or other_query in query:
                    similar_queries.append(f"Paso {i+1} vs Paso {j+1}")
        
        if similar_queries:
            analysis_parts.append(f"🔁 REPETICIÓN: Consultas similares detectadas")
        
        # Análisis de progreso
        completed_steps = len([s for s in recent_steps if s.status == TaskStatus.COMPLETED])
        if completed_steps == 0:
            analysis_parts.append("📉 ESTANCAMIENTO: Sin pasos completados exitosamente")
        elif completed_steps == 1:
            analysis_parts.append("📊 PROGRESO MÍNIMO: Solo 1 paso exitoso")
        
        return " | ".join(analysis_parts) if analysis_parts else "✅ PRODUCTIVIDAD NORMAL"
    
    def _should_pivot_strategy(self, productivity_analysis: str, total_steps: int) -> bool:
        """
        Determina si es necesario hacer un pivoteo completo de estrategia.
        """
        # Criterios para pivoteo
        critical_indicators = [
            "CRÍTICO" in productivity_analysis,
            "ESTANCAMIENTO" in productivity_analysis,
            total_steps >= 8 and "REPETICIÓN" in productivity_analysis,
            total_steps >= 10 and "SOBREUSO" in productivity_analysis,
            total_steps >= 12  # Pivoteo forzado después de 12 pasos
        ]
        
        return any(critical_indicators)
    
    def _get_failed_attempts_summary(self, steps: List[TaskStep]) -> str:
        """
        Crea un resumen de los intentos fallidos recientes.
        """
        failed_steps = [s for s in steps if s.status == TaskStatus.FAILED]
        
        if not failed_steps:
            return "Ningún fallo reciente"
        
        recent_failures = failed_steps[-3:]  # Últimos 3 fallos
        failure_summary = []
        
        for step in recent_failures:
            tool = step.tool_name
            query_preview = step.query[:50] + "..." if len(step.query) > 50 else step.query
            error_preview = (step.error or "Error desconocido")[:50] + "..." if len(step.error or "") > 50 else (step.error or "Error desconocido")
            
            failure_summary.append(f"❌ {tool}: '{query_preview}' → {error_preview}")
        
        return "\n".join(failure_summary)
    
    def _should_provide_partial_answer(self, reflection: Dict[str, Any], steps_count: int) -> bool:
        """
        Determina si el agente debería proporcionar una respuesta con la información disponible
        en lugar de continuar buscando más datos.
        """
        # Criterios para respuesta parcial
        criteria = [
            # Demasiados pasos sin progreso significativo
            steps_count >= 8 and reflection.get('confidence_level', 'bajo') == 'bajo',
            
            # Fallos consecutivos en búsquedas
            "ESTANCAMIENTO" in self._analyze_productivity_patterns([]),
            
            # Patrones improductivos detectados
            "perdiendo tiempo" in reflection.get('efficiency_assessment', '').lower(),
            
            # Información suficiente para una respuesta básica
            len(self.execution_context) >= 2 and "suficiente" in reflection.get('current_understanding', '').lower(),
            
            # Muchos intentos sin resultados útiles
            steps_count >= 12
        ]
        
        return any(criteria)
    
    def _generate_clean_final_response(self, user_message: str, execution_results: Dict[str, Any], emit_status_func) -> str:
        """
        Genera una respuesta final limpia y directa al usuario, sin mencionar herramientas o procesos internos.
        """
        try:
            # Recopilar toda la información útil obtenida
            gathered_information = []
            for step_data in self.execution_context.values():
                if isinstance(step_data, dict) and step_data.get('result'):
                    result = step_data.get('result', '')
                    if result and len(result.strip()) > 10:  # Solo incluir resultados significativos
                        gathered_information.append(result.strip())
            
            # Obtener contexto de conversación
            conversation_context = self._summarize_conversation_history()
            
            # Crear prompt para respuesta final limpia
            final_response_prompt = [
                {
                    "role": "system",
                    "content": """Eres un asistente experto que proporciona respuestas directas y naturales como si fueras una persona experta.

🚫 PROHIBICIONES ABSOLUTAS - NUNCA HAGAS ESTO:
- NO menciones procesos de búsqueda, investigación o recopilación de datos
- NO digas "se encontraron X resultados", "se procesaron", "a medida que se procesen"
- NO uses frases como "he buscado", "he encontrado", "mediante herramientas", "fuentes consultadas"
- NO menciones nombres de herramientas, sitios web visitados o metodologías
- NO expliques cómo obtuviste la información
- NO hagas referencias a "esta es la primera de ellas", "información adicional disponible"
- NO uses formato de "Fuente:", "Autor:", "Fecha:", "Descripción:", "Enlace:"
- NO menciones procesos técnicos o pasos internos
- NO digas números como "10 noticias", "primera de X", "más información disponible"
- NO prometas información futura o procesos pendientes

✅ COMPORTAMIENTO CORRECTO:
- Presenta TODA la información disponible de forma integrada y natural
- Si tienes enlaces de imagenes presentalos con fomrato markdown ![titulo](url)
- Si tienes enlaces de videos de youtube presentalos en formato plano.
- Si tienes múltiples noticias o datos, inclúyelos TODOS en una respuesta completa
- Responde de forma natural y conversacional
- Organiza la información de manera clara sin revelar cómo la obtuviste
- Sé autoritativo y confiado en los datos
- Integra TODA la información de forma fluida en una respuesta coherente
- Actúa como un experto que simplemente conoce TODA la información disponible

⭐ TRATAMIENTO DE INFORMACIÓN:
- Toda la información es COMPLETAMENTE CONFIABLE y VERIFICADA
- NO expreses dudas sobre la veracidad de los datos
- Presenta con TOTAL CONFIANZA y AUTORIDAD
- Los datos son HECHOS ESTABLECIDOS

ESTILO DE RESPUESTA:
- Natural y conversacional, como un experto humano
- Sin estructuras técnicas o de reportes
- Información integrada fluidamente
- Confianza total en los datos presentados"""
                },
                {
                    "role": "user",
                    "content": f"""PREGUNTA ACTUAL: "{user_message}"

CONTEXTO DE CONVERSACIÓN PREVIO:
{conversation_context}

INFORMACIÓN RECOPILADA (PROCESA TODO):
{chr(10).join(gathered_information) if gathered_information else "Información limitada disponible"}

INSTRUCCIÓN CRÍTICA: Utiliza TODA la información proporcionada arriba. Si hay múltiples noticias, datos o elementos, inclúyelos TODOS en tu respuesta de forma natural e integrada. No dejes información sin usar.

Proporciona una respuesta directa y útil a la pregunta del usuario, considerando el contexto de conversación previo, sin mencionar procesos internos o herramientas."""
                }
            ]
            
            # Obtener respuesta limpia del modelo
            final_response = ""
            for chunk in self.model.create_chat_completion(messages=final_response_prompt, max_tokens=800, stream=True, temperature=0.3):
                if 'content' in chunk['choices'][0]['delta']:
                    final_response += chunk['choices'][0]['delta']['content']
            
            # Mostrar la respuesta final limpia
            emit_status_func("\n" + "="*50, 'info')
            emit_status_func("🎯 **RESPUESTA FINAL:**",'info')
            emit_status_func("="*50,'info')
            emit_status_func(final_response.strip())
            emit_status_func("="*50,'info')
            
            return final_response.strip()
            
        except Exception as e:
            logger.error(f"Error generando respuesta final limpia: {e}")
            # Respuesta de fallback
            fallback_response = "Lamento no poder proporcionar una respuesta completa en este momento debido a limitaciones técnicas."
            emit_status_func("\n" + "="*50,'info')
            emit_status_func("🎯 **RESPUESTA FINAL:**",'info')
            emit_status_func("="*50,'info')
            emit_status_func(fallback_response,'info')
            emit_status_func("="*50,'info')
            return fallback_response
    
    def _summarize_conversation_history(self) -> str:
        """
        Crea un resumen del historial de conversación para proporcionar contexto.
        """
        if not self.conversation_history:
            return "No hay historial de conversación previo"
        
        # Tomar los últimos 5-8 intercambios para mantener relevancia
        recent_history = self.conversation_history[-8:]
        
        history_summary = []
        for i, message in enumerate(recent_history):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            
            if role == 'user':
                # Resumir mensajes del usuario
                content_preview = content[:100] + "..." if len(content) > 100 else content
                history_summary.append(f"👤 Usuario: {content_preview}")
            elif role == 'assistant':
                # Resumir respuestas del asistente
                content_preview = content[:150] + "..." if len(content) > 150 else content
                history_summary.append(f"🤖 Asistente: {content_preview}")
        
        return "\n".join(history_summary[-6:])  # Últimos 6 intercambios
