"""
@Author: Borja Otero Ferreira
Utilidades y funciones auxiliares para el agente autónomo
"""
import re
import string
from app.utils.logger import logger


def clean_text_content(text: str) -> str:
    """Limpia contenido de texto de caracteres problemáticos y saltos de línea excesivos"""
    if not text:
        return text
    
    try:
        # Remover caracteres de control y no imprimibles (excepto saltos de línea normales)
        allowed_chars = set(string.printable)
        cleaned_text = ''.join(char for char in text if char in allowed_chars)
        
        # Remover secuencias de caracteres extraños (preservar saltos de línea)
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


def clean_error_message(error_msg: str) -> str:
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


def remove_links(text: str) -> str:
    """Remueve enlaces de texto"""
    if not text:
        return text
    
    # Remover enlaces web
    text = re.sub(r'https?://[^\s\]]+', '', text)
    # Remover enlaces de YouTube sin protocolo
    text = re.sub(r'www\.youtube\.com[^\s\]]+', '', text)
    text = re.sub(r'youtube\.com[^\s\]]+', '', text)
    
    return text.strip()


def format_final_response(response: str) -> str:
    """Formatea la respuesta final eliminando saltos de línea excesivos y mejorando la presentación"""
    if not response:
        return response
    
    try:
        # Limpiar la respuesta de caracteres problemáticos
        formatted_response = clean_text_content(response)
        
        # Aplicar reglas específicas de formateo
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


def safe_emit_status(socket, message: str, message_type: str = 'info'):
    """Emite mensaje de estado de forma segura con tipo de mensaje"""
    try:
        clean_message = clean_text_content(message)
        from app.core.socket_handler import SocketResponseHandler
        SocketResponseHandler.emit_console_output(socket, clean_message, message_type)
    except Exception as e:
        # Fallback para emisión de estado
        try:
            fallback_msg = f"Estado: {str(e)[:100]}"
            from colorama import Fore, Style
            print(f"{Fore.CYAN}{fallback_msg}{Style.RESET_ALL}")
            from app.core.socket_handler import SocketResponseHandler
            SocketResponseHandler.emit_console_output(socket, fallback_msg, 'info')
        except Exception:
            pass  # Si falla todo, simplemente continuar


def safe_emit_tool_result(socket, tool_name: str, query: str, result: str):
    """Emite resultado de herramienta de forma segura"""
    try:
        clean_result = clean_text_content(result)
        preview = clean_result[:200] + "..." if len(clean_result) > 200 else clean_result
        message = f"🔧 {tool_name} -> {preview}"
        
        from app.core.socket_handler import SocketResponseHandler
        SocketResponseHandler.emit_console_output(socket, message, 'tool')
    except Exception as e:
        # Fallback
        try:
            fallback_msg = f"🔧 {tool_name} -> Resultado disponible"
            from app.core.socket_handler import SocketResponseHandler
            SocketResponseHandler.emit_console_output(socket, fallback_msg, 'tool')
        except Exception:
            pass


def get_available_tools_dict(tool_registry) -> dict:
    """Obtiene un diccionario de herramientas disponibles"""
    tools_dict = {}
    try:
        if tool_registry:
            for tool_name in tool_registry.list_tools():
                tool_info = tool_registry.get_tool_info(tool_name)
                if tool_info:
                    tools_dict[tool_name] = tool_info
        return tools_dict
    except Exception as e:
        logger.error(f"Error obteniendo herramientas disponibles: {e}")
        return {}
