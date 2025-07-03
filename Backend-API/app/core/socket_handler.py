"""
@Author: Borja Otero Ferreira
Socket Response Handler - Clase centralizada para el envío de respuestas al frontend
"""
import traceback
from app.utils.logger import logger
# Importar el proveedor de instancias socketio
from app.utils import socket_instance

class SocketResponseHandler:
    """
    Clase estática para centralizar el envío de respuestas al frontend por socket.
    """
    
    @staticmethod
    def emit_streaming_response(socket, content, user_tokens=None, assistant_token_count=None, finished=False):
        """
        Emite una respuesta de streaming al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            content (str): Contenido de la respuesta
            user_tokens (int, optional): Tokens del usuario (solo se envía al inicio)
            assistant_token_count (int, optional): Número de tokens del assistant para este chunk
            finished (bool): Indica si la respuesta ha terminado
        """
        response_data = {
            'content': content,
            'finished': finished
        }
        
        # Solo incluir tokens del usuario si se proporcionan (al inicio del stream)
        if user_tokens is not None:
            response_data['user_tokens'] = user_tokens
            
        # Solo incluir tokens del assistant si se proporcionan (para conteo en tiempo real)
        if assistant_token_count is not None:
            response_data['assistant_token_count'] = assistant_token_count
        
        socket.emit('assistant_response', response_data, namespace='/test')
    
    @staticmethod
    def emit_streaming_response_legacy(socket, content, total_user_tokens=0, total_assistant_tokens=0, finished=False):
        """
        Método legacy para compatibilidad con el código actual
        """
        response_data = {
            'content': content,
            'total_user_tokens': total_user_tokens,
            'total_assistant_tokens': total_assistant_tokens,
            'finished': finished
        }
        
        socket.emit('assistant_response', response_data, namespace='/test')
    
    @staticmethod
    def emit_finalization_signal(socket, total_user_tokens=0, total_assistant_tokens=0):
        """
        Emite la señal de finalización al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            total_user_tokens (int): Total de tokens del usuario
            total_assistant_tokens (int): Total de tokens del asistente
        """
        finalization_data = {
            'content': '',
            'total_user_tokens': total_user_tokens,
            'total_assistant_tokens': total_assistant_tokens,
            'finished': True
        }
        
        socket.emit('assistant_response', finalization_data, namespace='/test')
    
    @staticmethod
    def emit_error_response(socket, error_message):
        """
        Emite una respuesta de error al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            error_message (str): Mensaje de error
        """
        error_data = {
            'content': error_message,
            'finished': True,
            'error': True
        }
        
        socket.emit('assistant_response', error_data, namespace='/test')
    
    @staticmethod
    def emit_console_output(socket, message, role='info'):
        """
        Emite output de consola al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            message (str): Mensaje a mostrar en consola
            role (str): Tipo de mensaje ('info', 'pensamiento', 'tool', etc.)
        """
        console_data = {
            'content': message,
            'role': role
        }
        
        socket.emit('output_console', console_data, namespace='/test')
    
    @staticmethod
    def emit_utilities_data(socket, data):
        """
        Emite datos de utilidades (como IDs de YouTube) al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            data (dict): Datos de utilidades
        """
        socket.emit('utilidades', data, namespace='/test')
    
    @staticmethod
    def stream_chat_completion(model, messages, socket, max_tokens=1024, 
                              user_tokens=None, process_line_breaks=False, 
                              response_queue=None, link_remover_func=None, 
                              stop_condition=None):
        """
        Maneja el streaming de completions de chat de forma unificada
        
        Args:
            model: Instancia del modelo para hacer la completion
            messages: Lista de mensajes para la completion
            socket: Instancia del socket para enviar la respuesta
            max_tokens (int): Máximo número de tokens para la respuesta
            user_tokens (int, optional): Tokens del usuario (se envían al inicio)
            process_line_breaks (bool): Si procesar saltos de línea individualmente
            response_queue (queue.Queue, optional): Cola para almacenar líneas procesadas
            link_remover_func (callable, optional): Función para eliminar enlaces de las líneas
            stop_condition (callable, optional): Función que retorna True para detener el streaming
            
        Returns:
            tuple: (response_completa, total_assistant_tokens)
        """
        import time
        
        response_completa = ""
        total_assistant_tokens = 0
        linea = ""
        
        # Enviar tokens del usuario al inicio de la respuesta
        if user_tokens is not None:
            SocketResponseHandler.emit_streaming_response(
                socket,
                '',  # Sin contenido aún
                user_tokens=user_tokens,
                finished=False
            )
        
        try:
            for chunk in model.create_chat_completion(messages=messages, max_tokens=max_tokens, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    # Verificar condición de parada si se proporciona
                    if stop_condition and stop_condition():
                        break
                        
                    fragmento_response = chunk['choices'][0]['delta']['content']
                    response_completa += fragmento_response
                    total_assistant_tokens += 1
                    
                    # Procesar saltos de línea si se requiere
                    if process_line_breaks and response_queue is not None:
                        for char in fragmento_response:
                            linea += char
                            if char == '\n':
                                if link_remover_func:
                                    linea = link_remover_func(linea)
                                if linea.strip():
                                    response_queue.put(linea.strip())
                                linea = ''
                    
                    # Enviar respuesta al frontend
                    SocketResponseHandler.emit_streaming_response(
                        socket,
                        fragmento_response,
                        assistant_token_count=1,  # Un token por chunk
                        finished=False
                    )
                    time.sleep(0.01)
            
            # Procesar línea final si hay contenido restante
            if process_line_breaks and linea and response_queue is not None:
                if link_remover_func:
                    linea = link_remover_func(linea)
                if linea.strip():
                    response_queue.put(linea.strip())
            
            return response_completa, total_assistant_tokens
            
        except Exception as e:
            print(f"Error en stream_chat_completion: {e}")
            return response_completa, total_assistant_tokens
    
    @staticmethod
    def send_to_console(message, socket):
        """
        Envía un mensaje a la consola del frontend 
        Args:
            message (str): Mensaje a mostrar en la consola
            socket: Instancia del socket para enviar el mensaje
        """
       
        SocketResponseHandler.emit_console_output(socket, message, role='info')

    @staticmethod
    def emit_tools_registry(socket, tools_data):
        """
        Emite la información del registry de herramientas al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta
            tools_data (dict): Información de todas las herramientas disponibles
        """
        # Asegurarse de que los datos sean serializables
        try:
            from app.api.tools_controller import make_json_serializable
            serializable_data = make_json_serializable(tools_data)
            socket.emit('tools_registry', serializable_data, namespace='/test')
        except Exception as e:
            logger.error(f"Error al emitir registry de herramientas: {e}")
            # Intentar enviar una versión simplificada si falla la serialización
            try:
                simplified_data = {
                    'tools_enabled': tools_data.get('tools_enabled', False),
                    'total_available': tools_data.get('total_available', 0),
                    'total_selected': tools_data.get('total_selected', 0),
                    'active_tools': list(tools_data.get('active_tools', [])),
                    'available_tools': {}  # Versión vacía para evitar errores
                }
                socket.emit('tools_registry', simplified_data, namespace='/test')
            except Exception as inner_e:
                logger.error(f"Error al emitir versión simplificada: {inner_e}")
    
    @staticmethod
    def emit_tools_selection_update(socket, selected_tools):
        """
        Emite una actualización de herramientas seleccionadas al frontend
        
        Args:
            socket: Instancia del socket para enviar la respuesta (puede ser socketio completo o un namespace)
            selected_tools (list): Lista de nombres de herramientas seleccionadas
        """
        try:
            # Asegurar que los datos sean serializables
            from app.api.tools_controller import make_json_serializable
            serializable_data = make_json_serializable(selected_tools)
            
            # Detectar si es el objeto socketio completo o un namespace específico
            if hasattr(socket, 'emit'):
                # Es un objeto con método emit (puede ser socketio o namespace)
                if 'namespace' in socket.emit.__code__.co_varnames:
                    # Es socketio, necesita namespace
                    socket.emit('tools_selection_update', serializable_data, namespace='/test')
                else:
                    # Es un namespace específico, no necesita namespace
                    socket.emit('tools_selection_update', serializable_data)
            else:
                # Fallback, intentar usar la instancia global de socketio
                logger.warning("Socket object doesn't have emit method, using fallback")
                socketio = socket_instance.get_socketio()
                if socketio:
                    socketio.emit('tools_selection_update', serializable_data, namespace='/test')
                else:
                    logger.error("No hay instancia de socketio disponible para emisión fallback")
                
        except Exception as e:
            logger.error(f"Error al emitir actualización de herramientas: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Intentar enviar una versión simplificada si falla
            try:
                if hasattr(socket, 'emit'):
                    socket.emit('tools_selection_update', [], namespace='/test')
            except Exception as inner_e:
                logger.error(f"Error al emitir actualización simplificada: {inner_e}")

    @staticmethod
    def emit_tools_update(selected_tools=None, registry_data=None):
        """
        Método auxiliar para emitir actualizaciones de herramientas usando el proveedor global de socketio
        
        Args:
            selected_tools (list, optional): Lista de herramientas seleccionadas
            registry_data (dict, optional): Datos del registro de herramientas
        
        Returns:
            bool: True si se emitió correctamente al menos una actualización
        """
        socketio = socket_instance.get_socketio()
        if not socketio:
            logger.warning("No se puede emitir actualizaciones de herramientas: socketio no disponible")
            return False
            
        success = False
        
        # Emitir actualización de herramientas seleccionadas si se proporcionan
        if selected_tools is not None:
            try:
                from app.api.tools_controller import make_json_serializable
                serializable_data = make_json_serializable(selected_tools)
                socketio.emit('tools_selection_update', serializable_data, namespace='/test')
                logger.info(f"Emitida actualización de herramientas seleccionadas: {len(selected_tools)} herramientas")
                success = True
            except Exception as e:
                logger.error(f"Error al emitir actualización de herramientas seleccionadas: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Emitir actualización del registro de herramientas si se proporcionan
        if registry_data is not None:
            try:
                from app.api.tools_controller import make_json_serializable
                serializable_data = make_json_serializable(registry_data)
                socketio.emit('tools_registry', serializable_data, namespace='/test')
                logger.info(f"Emitida actualización del registro de herramientas")
                success = True
            except Exception as e:
                logger.error(f"Error al emitir actualización del registro de herramientas: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                
        return success
