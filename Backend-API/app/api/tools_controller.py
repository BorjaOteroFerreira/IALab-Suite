"""
@Author: Borja Otero Ferreira
Tools Controller - Maneja las API relacionadas con herramientas
"""

from flask import request, jsonify
from app.utils.logger import logger
from app.core.tools_manager import tools_manager
from app.core.mcp_registry import MCPRegistry
import json
import traceback  # Importar aquí para evitar ImportError más adelante
from enum import Enum
# Importar el proveedor de instancias socketio
from app.utils import socket_instance


def make_json_serializable(obj):
    """
    Convierte objetos no serializables a JSON en formatos compatibles
    
    Args:
        obj: El objeto a convertir
        
    Returns:
        Un objeto serializable a JSON
    """
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, Enum):
        # Convertir enums a su valor string
        return obj.value
    elif hasattr(obj, '__dict__'):
        # Convertir objetos personalizados a diccionarios
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    else:
        return obj


class ToolsController:
    """Controlador para endpoints de herramientas"""
    
    @staticmethod
    def get_available_tools():
        """Obtener todas las herramientas disponibles"""
        try:
            # Verificar si el tools_manager está inicializado correctamente
            if not hasattr(tools_manager, '_registry') or not tools_manager._registry:
                # Intentar inicializar el registro si no existe
                try:
                    from tools.tool_registry import ToolRegistry
                    registry = ToolRegistry()
                    registry.discover_tools()
                    tools_manager.initialize_registry(registry)
                    logger.info("Tools registry initialized on-demand")
                except Exception as e:
                    logger.error(f"Failed to initialize tools registry: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Error inicializando registro de herramientas: {str(e)}'
                    }), 500
            
            # Obtener el resumen de herramientas y convertirlo a formato serializable
            tools_summary = tools_manager.get_tools_summary()
            # Convertir a formato JSON serializable
            serializable_summary = make_json_serializable(tools_summary)
            logger.info(f"Returning tools summary: {len(serializable_summary.get('available_tools', {}))} tools available")
            
            return jsonify({
                'success': True,
                'data': serializable_summary
            })
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error obteniendo herramientas disponibles: {str(e)}'
            }), 500
    
    @staticmethod
    def get_selected_tools():
        """Obtener las herramientas seleccionadas actualmente"""
        try:
            selected_tools = tools_manager.get_selected_tools()
            return jsonify({
                'success': True,
                'data': {
                    'selected_tools': selected_tools,
                    'tools_enabled': tools_manager.is_tools_enabled()
                }
            })
        except Exception as e:
            logger.error(f"Error getting selected tools: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @staticmethod
    def set_selected_tools():
        """Establecer las herramientas seleccionadas"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            selected_tools = data.get('selected_tools', [])
            if not isinstance(selected_tools, list):
                return jsonify({
                    'success': False,
                    'error': 'selected_tools must be a list'
                }), 400
            
            # Validar que todas las herramientas sean strings válidos
            validated_tools = [str(tool) for tool in selected_tools if tool]
            
            # Establecer las herramientas seleccionadas
            tools_manager.set_selected_tools(validated_tools)
            
            # Obtener las herramientas realmente seleccionadas (puede ser diferente si algunas no son válidas)
            actual_selected_tools = tools_manager.get_selected_tools()
            
            # Emitir actualización a través de socket si está disponible
            serializable_data = make_json_serializable(actual_selected_tools)
            if socket_instance.emit_safely('tools_selection_update', serializable_data):
                logger.info(f"Emitida actualización de herramientas: {len(actual_selected_tools)} herramientas seleccionadas")
            else:
                logger.warning("No se pudo emitir actualización de herramientas por socket")
            
            # Preparar respuesta serializable
            selected_tools_data = make_json_serializable(actual_selected_tools)
            
            return jsonify({
                'success': True,
                'data': {
                    'selected_tools': selected_tools_data,
                    'message': f'Selected {len(actual_selected_tools)} tools'
                }
            })
        except Exception as e:
            logger.error(f"Error setting selected tools: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @staticmethod
    def refresh_tools():
        """Refrescar la lista de herramientas"""
        try:
            # Reinicializar completamente el registro de herramientas
            try:
                from tools.tool_registry import ToolRegistry
                registry = ToolRegistry()
                registry.discover_tools()
                tools_manager.initialize_registry(registry)
                logger.info("Tools registry completely reinitialized")
            except Exception as e:
                logger.error(f"Error reinitializing tools registry: {e}")
                tools_manager.refresh_tools()
                logger.info("Using existing registry for refresh")
            
            # Obtener el resumen actualizado y convertirlo a formato serializable
            tools_summary = tools_manager.get_tools_summary()
            serializable_summary = make_json_serializable(tools_summary)
            
            # Emitir actualización a todos los clientes conectados
            from app.core.socket_handler import SocketResponseHandler
            socketio = socket_instance.get_socketio()
            if socketio:
                SocketResponseHandler.emit_tools_registry(socketio, serializable_summary)
                logger.info("Tools registry update broadcast to all clients")
            else:
                logger.warning("No se pudo emitir actualización de registry: instancia socketio no disponible")
            
            return jsonify({
                'success': True,
                'data': serializable_summary,
                'message': 'Herramientas actualizadas correctamente'
            })
        except Exception as e:
            logger.error(f"Error refreshing tools: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error actualizando herramientas: {str(e)}'
            }), 500
    
    @staticmethod
    def get_mcp_tools():
        """Obtener todas las herramientas MCP gratuitas (mock)"""
        try:
            mcp_registry = MCPRegistry()
            mcp_tools_summary = mcp_registry.get_tools_summary()
            return jsonify({
                'success': True,
                'data': mcp_tools_summary
            })
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error obteniendo herramientas MCP: {str(e)}'
            }), 500
    
    @staticmethod
    def get_selected_remote_tools():
        """Obtener las herramientas remotas MCP seleccionadas actualmente (usando MCPRegistry)"""
        try:
            mcp_registry = MCPRegistry()
            selected = mcp_registry.get_selected_tools()
            return jsonify({'success': True, 'data': {'selected_remote_tools': selected}})
        except Exception as e:
            logger.error(f"Error getting selected remote tools: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @staticmethod
    def set_selected_remote_tools():
        """Establecer las herramientas remotas MCP seleccionadas (usando MCPRegistry)"""
        try:
            data = request.get_json()
            if not data or 'selected_remote_tools' not in data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            selected = data['selected_remote_tools']
            mcp_registry = MCPRegistry()
            mcp_registry.set_selected_tools(selected)
            return jsonify({'success': True, 'data': {'selected_remote_tools': mcp_registry.get_selected_tools()}})
        except Exception as e:
            logger.error(f"Error setting selected remote tools: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


# Instancia del controlador
tools_controller = ToolsController()
