"""
@Author: Borja Otero Ferreira
Ejecutor de tareas y pasos para el agente autónomo
"""
import time
from typing import Dict, Any, List, Optional
from ..models import TaskPlan, TaskStep, TaskStatus
from ..utils import clean_error_message, safe_emit_tool_result
from app.utils.logger import logger


class TaskExecutor:
    """Ejecuta planes de tareas paso a paso"""
    
    def __init__(self, tools_manager, tool_registry, socket, assistant=None, max_execution_iterations=10):
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
        self.socket = socket
        self.assistant = assistant
        self.max_execution_iterations = max_execution_iterations
        self.execution_context = {}
    
    def execute_plan(self, current_plan: TaskPlan, emit_status_func) -> Dict[str, Any]:
        """Ejecuta el plan de tareas paso a paso"""
        if not current_plan:
            return {}
        
        execution_results = {
            'completed_steps': [],
            'failed_steps': [],
            'total_steps': len(current_plan.steps),
            'success_rate': 0.0,
            'execution_time': 0.0
        }
        
        start_time = time.time()
        
        try:
            # Ejecutar pasos en orden, respetando dependencias
            for iteration in range(self.max_execution_iterations):
                # Verificar si se debe detener
                if self.assistant and getattr(self.assistant, 'stop_emit', False):
                    emit_status_func("🛑 Ejecución detenida por el usuario")
                    break
                
                # Buscar pasos listos para ejecutar
                ready_steps = self._get_ready_steps(current_plan)
                if not ready_steps:
                    break
                
                # Ejecutar pasos listos
                for step in ready_steps:
                    if self.assistant and getattr(self.assistant, 'stop_emit', False):
                        break
                    
                    self._execute_step(step, emit_status_func)
                    
                    if step.status == TaskStatus.COMPLETED:
                        execution_results['completed_steps'].append(step)
                    elif step.status == TaskStatus.FAILED:
                        execution_results['failed_steps'].append(step)
                
                # Verificar si todos los pasos están completos
                if all(step.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED] 
                       for step in current_plan.steps):
                    break
            
            # Calcular estadísticas
            if execution_results['total_steps'] > 0:
                execution_results['success_rate'] = len(execution_results['completed_steps']) / execution_results['total_steps']
            execution_results['execution_time'] = time.time() - start_time
            
            # Actualizar estado del plan
            if execution_results['success_rate'] > 0.5:
                current_plan.status = TaskStatus.COMPLETED
            else:
                current_plan.status = TaskStatus.FAILED
            
            current_plan.completed_at = time.time()
            
            return execution_results
            
        except Exception as e:
            error_clean = clean_error_message(str(e))
            logger.error(f"Error ejecutando plan: {error_clean}")
            execution_results['error'] = error_clean
            return execution_results

    def _get_ready_steps(self, current_plan: TaskPlan) -> List[TaskStep]:
        """Obtiene los pasos que están listos para ejecutar"""
        ready_steps = []
        
        for step in current_plan.steps:
            if step.status != TaskStatus.PENDING:
                continue
            
            # Verificar dependencias
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_step = self._find_step_by_id(current_plan, dep_id)
                if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_steps.append(step)
        
        return ready_steps

    def _find_step_by_id(self, current_plan: TaskPlan, step_id: str) -> Optional[TaskStep]:
        """Encuentra un paso por su ID"""
        for step in current_plan.steps:
            if step.id == step_id:
                return step
        return None

    def _execute_step(self, step: TaskStep, emit_status_func):
        """Ejecuta un paso individual"""
        try:
            step.status = TaskStatus.IN_PROGRESS
            
            emit_status_func(f"🔄 Ejecutando: {step.description}")
            logger.info(f"Ejecutando paso: {step.id} - {step.description}")
            
            # Verificar si la herramienta está disponible
            if not self._is_tool_available(step.tool_name):
                step.status = TaskStatus.FAILED
                step.error = f"Herramienta {step.tool_name} no está disponible"
                emit_status_func(f"❌ {step.error}")
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
                emit_status_func(f"✅ Completado: {step.description}")
                
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
                    emit_status_func(f"🔄 Reintentando: {step.description} (intento {step.retry_count + 1})")
                else:
                    step.status = TaskStatus.FAILED
                    step.error = result_text or "Error desconocido"
                    emit_status_func(f"❌ Falló: {step.description} - Error de procesamiento")
                    
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = clean_error_message(str(e))
            emit_status_func(f"❌ Error ejecutando {step.description}: Error interno")
            logger.error(f"Error ejecutando paso {step.id}: {step.error}")

    def _is_tool_available(self, tool_name: str) -> bool:
        """Verifica si una herramienta está disponible"""
        if not self.tools_manager:
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
                error_clean = clean_error_message(resultado_ejecucion.error)
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
            from ..utils import clean_text_content
            if isinstance(resultado, str):
                resultado = clean_text_content(resultado)
            else:
                # Convertir a string si no lo es
                resultado = str(resultado) if resultado is not None else ""
            
            # Enviar resultado al socket
            safe_emit_tool_result(self.socket, tool_name, query, resultado)
            
            return resultado
            
        except Exception as e:
            error_msg = clean_error_message(f"Error ejecutando {tool_name}: {str(e)}")
            logger.error(error_msg)
            return error_msg

    def display_execution_stats(self, execution_results: Dict[str, Any], emit_status_func):
        """Muestra estadísticas de ejecución"""
        try:
            stats_text = f"\n📊 **Estadísticas de Ejecución**\n"
            stats_text += f"- Total de pasos: {execution_results.get('total_steps', 0)}\n"
            stats_text += f"- Pasos completados: {len(execution_results.get('completed_steps', []))}\n"
            stats_text += f"- Pasos fallidos: {len(execution_results.get('failed_steps', []))}\n"
            stats_text += f"- Tasa de éxito: {execution_results.get('success_rate', 0):.1%}\n"
            stats_text += f"- Tiempo de ejecución: {execution_results.get('execution_time', 0):.2f}s\n"
            
            emit_status_func(stats_text)
        except Exception as e:
            logger.error(f"Error mostrando estadísticas: {e}")
            emit_status_func("📊 Estadísticas de ejecución completadas")
