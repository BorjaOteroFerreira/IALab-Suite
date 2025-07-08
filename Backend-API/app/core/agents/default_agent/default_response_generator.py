"""
@Author: Borja Otero Ferreira
Default Response Generator - Generador de respuestas finales para el agente default
Migrado desde la lógica de generación de respuestas de Cortex
"""
from typing import Any, List, Tuple
from colorama import Fore, Style
import queue
import threading

from app.utils.logger import logger
from .config import DefaultAgentConfig


class DefaultResponseGenerator:
    """
    Generador de respuestas finales para el agente default
    Migrado desde Cortex.generar_respuesta_final
    """
    
    def __init__(self, model, socket, response_queue, original_prompt, assistant, config: DefaultAgentConfig):
        self.model = model
        self.socket = socket
        self.response_queue = response_queue
        self.original_prompt = original_prompt
        self.assistant = assistant
        self.config = config
        self.engine_lock = threading.Lock()
    
    def generar_respuesta_final(self, resultados_herramientas: List[Tuple[str, str, str]], emit_status_callback=None) -> str:
        """
        Genera la respuesta final incorporando los resultados de todas las herramientas
        Migrado desde Cortex.generar_respuesta_final
        """
        salida = '[>] Generando respuesta final incorporando todos los resultados...'
        print(f"{Fore.GREEN}{salida}{Style.RESET_ALL}")
        logger.info(salida)
        
        if emit_status_callback:
            emit_status_callback(salida)
        else:
            self._enviar_a_consola(salida, 'info')

        try:
            # Crear el prompt para generar la respuesta final
            final_prompt = self._crear_prompt_respuesta_final(resultados_herramientas)

            # Emitir la respuesta final al frontend usando el socket (stream)
            from app.core.socket_handler import SocketResponseHandler
            user_question = ""
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
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=self.model,
                messages=final_prompt,
                socket=self.socket,
                max_tokens=8192,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=self.response_queue,
                stop_condition=safe_stop_condition
            )
            SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
            final_response = response_completa.strip()
            if not final_response or final_response.strip() == "":
                final_response = self._generar_respuesta_fallback(resultados_herramientas)
            logger.info("Respuesta final generada exitosamente")
            return final_response
        except Exception as e:
            logger.error(f"Error generando respuesta final: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._generar_respuesta_fallback(resultados_herramientas)
    
    def _crear_prompt_respuesta_final(self, resultados_herramientas: List[Tuple[str, str, str]]) -> List[dict]:
        """
        Crear el prompt para generar la respuesta final
        """
        instrucciones = (
            "Responde en Markdown.\n"
            "Tus respuestas deben estar bien maquetadas, agradables a la vista y fáciles de leer.\n"
            "Incrusta las imágenes con este formato ![dominio](url_imagen).\n"
            "No incluyas imágenes o mapas si no te las han facilitado las herramientas.\n"
            "IMPORTANTE: Los videos de youtube debes insertarlos solo como enlace aplanado, sin formato markdown.\n"
            "Después de ':' añade un salto de línea y un espacio antes de continuar, salvo que sea el primer carácter de la línea.\n"
            "Utiliza toda la información proporcionada por las herramientas para responder al usuario.\n"
            "A continuación tienes toda la informacion recopilada por las herramentas\n\n"
        )
        info_consolidada = ""
        if resultados_herramientas:
            for funcion, query, resultado in resultados_herramientas:
                info_consolidada += f"Resultados de {funcion} para '{query}':\n{resultado}\n\n"
        info_consolidada += (
            "Inserta los enlaces e imágenes relevantes en tu respuesta y responde en completo español. "
            "Organiza la información de manera coherente y clara para el usuario."
        )
        # Añadir mensaje assistant como en Cortex
        messages = [
            {"role": "system", "content": "Eres un asistente experto que integra información de múltiples fuentes para dar respuestas completas y útiles. Tu objetivo es crear una respuesta bien estructurada."},
            {"role": "user", "content": instrucciones + info_consolidada}
        ]
        return messages
    
    def _generar_respuesta_fallback(self, resultados_herramientas: List[Tuple[str, str, str]]) -> str:
        """
        Generar una respuesta de fallback si hay error en la generación principal
        """
        if not resultados_herramientas:
            return "No se pudo obtener información adicional para responder a tu consulta."
        
        respuesta_fallback = f"Basándome en la información recopilada sobre tu consulta '{self.original_prompt}':\n\n"
        
        for i, (funcion, query, resultado) in enumerate(resultados_herramientas, 1):
            respuesta_fallback += f"**Información {i}:**\n"
            respuesta_fallback += f"{resultado}\n\n"
        
        respuesta_fallback += "Espero que esta información sea útil para responder a tu consulta."
        
        return respuesta_fallback
    
    def _generate_normal_response(self, model: Any) -> str:
        """
        Generar respuesta normal sin herramientas
        Migrado desde Cortex._generate_normal_response
        """
        try:
            logger.info("Generando respuesta normal sin herramientas")

            # Crear prompt simple para respuesta directa
            messages = [
                {"role": "system", "content": "Eres un asistente útil. Responde de manera clara y precisa basándote en tu conocimiento."},
                {"role": "user", "content": self.original_prompt}
            ]

            # Calcular tokens de entrada
            user_question = self.original_prompt if isinstance(self.original_prompt, str) else ""
            tokensInput = user_question.encode()
            tokens = self.model.tokenize(tokensInput)
            total_user_tokens = len(tokens)

            def safe_stop_condition():
                try:
                    return self.assistant and getattr(self.assistant, 'stop_emit', False)
                except Exception:
                    return False

            from app.core.socket_handler import SocketResponseHandler
            response_completa, total_assistant_tokens = SocketResponseHandler.stream_chat_completion(
                model=self.model,
                messages=messages,
                socket=self.socket,
                max_tokens=8192,
                user_tokens=total_user_tokens,
                process_line_breaks=True,
                response_queue=self.response_queue,
                stop_condition=safe_stop_condition
            )
            SocketResponseHandler.emit_finalization_signal(self.socket, total_user_tokens, total_assistant_tokens)
            logger.info("Respuesta normal generada exitosamente")
            return response_completa.strip()

        except Exception as e:
            logger.error(f"Error generando respuesta normal: {e}")
            return f"Lo siento, no pude generar una respuesta adecuada. Error: {e}"
    
    def _enviar_a_consola(self, mensaje: str, rol: str):
        """Enviar mensaje a consola usando SocketResponseHandler"""
        if self.config.ENABLE_SOCKET_EMISSION:
            try:
                from app.core.socket_handler import SocketResponseHandler
                SocketResponseHandler.emit_console_output(self.socket, mensaje, rol)
            except Exception as e:
                logger.error(f"Error emitting to socket: {e}")

