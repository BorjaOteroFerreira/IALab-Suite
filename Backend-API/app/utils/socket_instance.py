"""
@Author: Borja Otero Ferreira
Socket Instance Provider - Módulo para almacenar y proporcionar la instancia socketio
"""
import traceback
from app.utils.logger import logger

# Variable global para almacenar la instancia socketio
_socketio_instance = None

def set_socketio(socketio):
    """
    Almacena la instancia de socketio para uso global
    
    Args:
        socketio: La instancia de socketio a almacenar
    """
    global _socketio_instance
    _socketio_instance = socketio
    logger.info("SocketIO instance stored in global provider")

def get_socketio():
    """
    Recupera la instancia almacenada de socketio
    
    Returns:
        La instancia de socketio almacenada o None si no está disponible
    """
    return _socketio_instance

def emit_safely(event, data, namespace=None, room=None, **kwargs):
    """
    Emite un evento usando la instancia socketio de forma segura
    
    Args:
        event: El nombre del evento a emitir
        data: Los datos a enviar
        namespace: El namespace al que emitir (por defecto '/test')
        room: La sala específica a la que emitir (opcional)
        **kwargs: Argumentos adicionales para el método emit
        
    Returns:
        bool: True si se emitió correctamente, False en caso contrario
    """
    try:
        socketio = get_socketio()
        if socketio:
            # Usar el namespace por defecto si no se especifica
            if namespace is None:
                namespace = '/test'
                
            # Emitir el evento
            if room:
                socketio.emit(event, data, namespace=namespace, room=room, **kwargs)
            else:
                socketio.emit(event, data, namespace=namespace, **kwargs)
            return True
        else:
            logger.warning(f"No se pudo emitir '{event}': instancia socketio no disponible")
            return False
    except Exception as e:
        logger.error(f"Error al emitir evento '{event}': {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return False
