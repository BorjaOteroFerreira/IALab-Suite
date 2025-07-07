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
            
            # Generar la respuesta final usando create_chat_completion como en Cortex
            response_content = ""
            for chunk in self.model.create_chat_completion(messages=final_prompt, max_tokens=1024, stream=True):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        response_content += delta['content']
            
            final_response = response_content.strip()
            
            # Verificar que la respuesta no esté vacía
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
        # Construir información de resultados
        resultados_info = ""
        if resultados_herramientas:
            resultados_info = "\n## INFORMACIÓN RECOPILADA:\n\n"
            for i, (funcion, query, resultado) in enumerate(resultados_herramientas, 1):
                resultados_info += f"**Fuente {i} ({funcion}):**\n"
                resultados_info += f"Consulta: {query}\n"
                resultados_info += f"Resultado: {resultado}\n\n"
        
        # Instrucciones para la respuesta final
        instrucciones = """
## INSTRUCCIONES PARA LA RESPUESTA:
    Responde en Markdown.
    1.Tus respuestas deben estar bien maquetadas, deben ser agradables a la vista y fáciles de leer.
    2.Incrusta las imágenes con este formato ![dominio](url_imagen) sin olvidar la exclamación al inicio.
    3.No incluyas imagenes o mapas si no te las han facilitado las herramientas.
    4.IMPORTANTE: Los videos de youtube debes insertarlos sin formato markdown, solo el enlace aplanado.
    5.Despues del caracter ':' debes añadir un salto de linea y un espacio antes de continuar con el texto  a no ser que sea el primer caracter de la línea, en ese caso elimina el caracter ':' y comienza directamente con el texto.
    6.Utiliza esta información proporcionada por las herramientas para responder al usuario

## CONSULTA ORIGINAL:
"""
        
        # Construir el prompt completo
        prompt_content = instrucciones + f"{self.original_prompt}\n" + resultados_info
        
        messages = [
            {"role": "system", "content": "Eres un asistente experto que integra información de múltiples fuentes para dar respuestas completas y útiles. Tu objetivo es crear una respuesta cohesiva y bien estructurada."},
            {"role": "user", "content": prompt_content}
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
            
            # Generar respuesta usando create_chat_completion
            response_content = ""
            for chunk in model.create_chat_completion(messages=messages, max_tokens=1024, stream=True):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        response_content += delta['content']
            
            logger.info("Respuesta normal generada exitosamente")
            return response_content.strip()
            
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
    
    def hablar_response(self, response: str):
        """
        Función para hablar la respuesta usando TTS
        Migrado desde Cortex.hablar_response
        """
        if not self.config.VOICE_RESPONSE_ENABLED:
            return
            
        try:
            # Importar pyttsx3 solo cuando sea necesario
            import pyttsx3
            
            # Limitar la longitud del texto a hablar
            max_length = 500  # caracteres
            if len(response) > max_length:
                response = response[:max_length] + "..."
            
            with self.engine_lock:
                try:
                    engine = pyttsx3.init()
                    
                    # Configurar velocidad y volumen
                    engine.setProperty('rate', 150)  # velocidad de habla
                    engine.setProperty('volume', 0.8)  # volumen (0.0 a 1.0)
                    
                    # Configurar voz en español si está disponible
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        if 'spanish' in voice.name.lower() or 'es' in voice.id.lower():
                            engine.setProperty('voice', voice.id)
                            break
                    
                    # Hablar el texto
                    engine.say(response)
                    engine.runAndWait()
                    engine.stop()
                    
                except Exception as e:
                    logger.error(f"Error en TTS engine: {e}")
                    
        except ImportError:
            logger.warning("pyttsx3 no está disponible para TTS")
        except Exception as e:
            logger.error(f"Error en hablar_response: {e}")
