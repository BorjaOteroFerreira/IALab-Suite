"""
@Author: Borja Otero Ferreira
Generador de respuestas finales para el agente autónomo
"""
import copy
from typing import Dict, Any, List
from .utils import clean_text_content, format_final_response
from app.utils.logger import logger


class ResponseGenerator:
    """Genera respuestas finales basadas en los resultados de ejecución"""
    
    def __init__(self, model, socket, response_queue, original_prompt, assistant=None):
        self.model = model
        self.socket = socket
        self.response_queue = response_queue
        self.original_prompt = original_prompt
        self.assistant = assistant
    
    def generate_final_response(self, execution_results: Dict[str, Any], emit_status_func) -> str:
        """Genera la respuesta final basada en los resultados de ejecución y la envía por streaming al usuario"""
        try:
            emit_status_func("📝 Consolidando resultados y generando respuesta final...")

            prompt_final = copy.deepcopy(self.original_prompt)

            # Extraer el contexto de la conversación (última pregunta del usuario)
            user_question = ""
            for message in reversed(self.original_prompt):
                if message['role'] == 'user':
                    user_question = message['content']
                    break

            # Consolidar solo los resultados devueltos por las tools usadas
            resultados_tools = "Resultados obtenidos por las herramientas:\n"
            tool_results = execution_results.get('tool_results', [])
            if tool_results:
                for idx, result in enumerate(tool_results, 1):
                    if isinstance(result, dict):
                        tool_name = result.get('tool_name', f"Tool {idx}")
                        output = result.get('output', str(result))
                        resultados_tools += f"• [{tool_name}]: {clean_text_content(str(output))}\n"
                    else:
                        resultados_tools += f"• {clean_text_content(str(result))}\n"
            else:
                completed_steps = execution_results.get('completed_steps', [])
                for step in completed_steps:
                    if hasattr(step, 'result') and step.result:
                        resultados_tools += f"• {clean_text_content(str(step.result))}\n"

            # Añadir la respuesta final del planificador
            respuesta_final_planificador = execution_results.get('final_response', '')

            # Instrucciones para la respuesta final
            instrucciones_finales = """
Responde en Markdown con formato profesional, limpio y compacto ya que esta es tu respuesta final.
Utiliza toda la información obtenida para proporcionar una respuesta completa y útil.
IMPORTANTE - Reglas de formato:
- Evita saltos de línea excesivos.
- Usa formato profesional y compacto.
- Incrusta imágenes con ![descripción](url) 
- Enlaces de YouTube sin formato markdown, solo el URL
- Organiza la información de manera clara y estructurada sin espaciado excesivo
- Incluye enlaces e imágenes relevantes encontradas
- NO uses múltiples saltos de línea consecutivos
- Mantén un formato limpio y legible sin espacios innecesarios
Si algunos pasos fallaron, proporciona la mejor respuesta posible con la información disponible.
            """

            # Construir el mensaje final: contexto + respuesta del planificador + resultados de tools + instrucciones
            mensaje_final = f"# Pregunta del usuario\n{user_question}\n\n# Respuesta del planificador\n{respuesta_final_planificador}\n\n# Resultados de herramientas\n{resultados_tools}\n\n{instrucciones_finales}"

            # Añadir mensajes al prompt
            prompt_final.append({"role": "assistant", "content": "He completado la ejecución del plan de tareas."})
            prompt_final.append({"role": "user", "content": mensaje_final})

            # Stream de la respuesta enriquecida usando el socket
            response_final = self._stream_final_response(prompt_final)

            return response_final
        except Exception as e:
            error_clean = clean_text_content(str(e))
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

    def generate_normal_response(self) -> str:
        """Genera una respuesta normal sin herramientas"""
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
            
            # Stream de la respuesta usando el mismo sistema que las respuestas con herramientas
            from app.core.socket_handler import SocketResponseHandler
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=self.model,
                messages=self.original_prompt,
                socket=self.socket,
                max_tokens=1200,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=self.response_queue,
                stop_condition=safe_stop_condition
            )
            
            # Formatear la respuesta antes de enviarla
            response_completa = format_final_response(response_completa)
            
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
                        clean_result = clean_text_content(result_preview)
                        resultados_consolidados += f"  Resultado: {clean_result}\n"
            
            # Pasos fallidos
            failed_steps = execution_results.get('failed_steps', [])
            if failed_steps:
                resultados_consolidados += "\n❌ PASOS FALLIDOS:\n"
                for step in failed_steps:
                    clean_error = clean_text_content(step.error or "Error desconocido")
                    resultados_consolidados += f"• {step.description}: {clean_error}\n"
            
            # Instrucciones para la respuesta final
            instrucciones_finales = """
Responde en Markdown con formato profesional, limpio y compacto ya que esta es tu respuesta final.
Utiliza toda la información obtenida para proporcionar una respuesta completa y útil.
IMPORTANTE - Reglas de formato:
- Evita saltos de línea excesivos.
- Usa formato profesional y compacto.
- Incrusta imágenes con ![descripción](url) 
- Enlaces de YouTube sin formato markdown, solo el URL
- Organiza la información de manera clara y estructurada sin espaciado excesivo
- Incluye enlaces e imágenes relevantes encontradas
- NO uses múltiples saltos de línea consecutivos
- Mantén un formato limpio y legible sin espacios innecesarios
Si algunos pasos fallaron, proporciona la mejor respuesta posible con la información disponible.
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
                stop_condition=safe_stop_condition
            )
            
            # Formatear la respuesta antes de enviarla
            response_completa = format_final_response(response_completa)
            
            self.response_queue.put(None)
            SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
            
            return response_completa
            
        except Exception as e:
            error_clean = clean_text_content(str(e))
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
                        clean_preview = clean_text_content(preview)
                        response += f"- Resultado: {clean_preview}\n"
            
            # Mostrar pasos fallidos
            if execution_results.get('failed_steps'):
                response += "\n## ❌ Pasos Fallidos\n"
                for step in execution_results['failed_steps']:
                    response += f"**{step.description}**\n"
                    clean_error = clean_text_content(step.error or "Error desconocido")
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
            return clean_text_content(response)
            
        except Exception as e:
            logger.error(f"Error creando respuesta de respaldo: {e}")
            return "Se completó la ejecución, pero hubo problemas al generar la respuesta final."
