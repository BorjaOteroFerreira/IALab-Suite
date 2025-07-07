"""
@Author: Borja Otero Ferreira
Agent Controller - API endpoints para gestión de agentes
"""
from flask import Blueprint, jsonify, request
from app.core.agents.agent_registry import agent_registry
from app.utils.logger import logger

agent_controller = Blueprint('agent_controller', __name__)


@agent_controller.route('/api/agents', methods=['GET'])
def get_available_agents():
    """Obtiene la lista de agentes disponibles"""
    try:
        # Importar aquí para evitar problemas de inicialización
        from app.core.agents.agent_registry import agent_registry
        
        # Verificar que el registro esté inicializado
        if not agent_registry._agents:
            agent_registry._initialize_default_agents()
        
        agents = agent_registry.get_agent_for_frontend()
        current_agent = agent_registry.get_current_agent()
        
        logger.info(f"Enviando {len(agents)} agentes al frontend")
        
        return jsonify({
            'success': True,
            'agents': agents,
            'current_agent': current_agent
        })
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agent_controller.route('/api/agents/current', methods=['GET'])
def get_current_agent():
    """Obtiene el agente actualmente seleccionado"""
    try:
        from app.core.agents.agent_registry import agent_registry
        
        # Verificar que el registro esté inicializado
        if not agent_registry._agents:
            agent_registry._initialize_default_agents()
            
        current = agent_registry.get_current_agent()
        agent_info = agent_registry.get_agent_info(current) if current else None
        
        return jsonify({
            'success': True,
            'current_agent': current,
            'agent_info': {
                'name': agent_info.display_name,
                'description': agent_info.description,
                'icon': agent_info.icon,
                'type': agent_info.agent_type.value
            } if agent_info else None
        })
    except Exception as e:
        logger.error(f"Error obteniendo agente actual: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agent_controller.route('/api/agents/select', methods=['POST'])
def select_agent():
    """Selecciona un agente específico"""
    try:
        from app.core.agents.agent_registry import agent_registry
        
        data = request.get_json()
        agent_name = data.get('agent_name')
        
        if not agent_name:
            return jsonify({
                'success': False,
                'error': 'agent_name es requerido'
            }), 400
        
        # Verificar que el registro esté inicializado
        if not agent_registry._agents:
            agent_registry._initialize_default_agents()
        
        # Verificar que el agente existe
        agent_info = agent_registry.get_agent_info(agent_name)
        if not agent_info:
            return jsonify({
                'success': False,
                'error': f'Agente {agent_name} no encontrado'
            }), 404
        
        # Seleccionar el agente
        success = agent_registry.set_current_agent(agent_name)
        
        if success:
            logger.info(f"Agente seleccionado manualmente: {agent_name}")
            return jsonify({
                'success': True,
                'message': f'Agente {agent_info.display_name} seleccionado',
                'agent_info': {
                    'name': agent_info.display_name,
                    'description': agent_info.description,
                    'icon': agent_info.icon,
                    'type': agent_info.agent_type.value
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al seleccionar el agente'
            }), 500
            
    except Exception as e:
        logger.error(f"Error seleccionando agente: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agent_controller.route('/api/agents/auto-detect', methods=['POST'])
def auto_detect_agent():
    """Detecta automáticamente el mejor agente para el contexto dado"""
    try:
        from app.core.agents.agent_registry import agent_registry
        
        data = request.get_json()
        context = data.get('context', {})
        
        # Verificar que el registro esté inicializado
        if not agent_registry._agents:
            agent_registry._initialize_default_agents()
        
        # Auto-detectar el agente
        detected_agent = agent_registry.auto_detect_agent(context)
        agent_info = agent_registry.get_agent_info(detected_agent)
        
        # Establecer como agente actual
        agent_registry.set_current_agent(detected_agent)
        
        logger.info(f"Agente auto-detectado: {detected_agent} para contexto: {context}")
        
        return jsonify({
            'success': True,
            'detected_agent': detected_agent,
            'agent_info': {
                'name': agent_info.display_name,
                'description': agent_info.description,
                'icon': agent_info.icon,
                'type': agent_info.agent_type.value
            } if agent_info else None,
            'context_used': context
        })
        
    except Exception as e:
        logger.error(f"Error en auto-detección de agente: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agent_controller.route('/api/agents/test', methods=['GET'])
def test_agents():
    """Endpoint de prueba para verificar que el sistema de agentes funciona"""
    try:
        from app.core.agents.agent_registry import agent_registry
        
        # Forzar inicialización
        agent_registry._initialize_default_agents()
        
        # Obtener información básica
        agents_count = len(agent_registry._agents)
        current_agent = agent_registry.get_current_agent()
        available_agents = list(agent_registry._agents.keys())
        
        return jsonify({
            'success': True,
            'message': 'Sistema de agentes funcionando correctamente',
            'agents_count': agents_count,
            'current_agent': current_agent,
            'available_agents': available_agents,
            'registry_initialized': bool(agent_registry._agents)
        })
        
    except Exception as e:
        logger.error(f"Error en test de agentes: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
