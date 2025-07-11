"""
@Author: Borja Otero Ferreira
Paquete del agente autónomo modularizado
"""
from .default_agent import DefaultAgent
from .default_agent.default_agent import DefaultAgent
from .default_agent.config import DefaultAgentConfig
from .default_agent.default_need_analyzer import DefaultNeedAnalyzer
from .default_agent.default_tool_executor import DefaultToolExecutor
from .default_agent.default_response_generator import DefaultResponseGenerator
from .adaptive_agent.adaptive_agent import AdaptiveAgent
from .adaptive_agent.adaptive_planner import AdaptiveTaskPlanner
from .models import TaskStatus, TaskStep, TaskPlan
from .adaptive_agent.task_analyzer import TaskAnalyzer
from .adaptive_agent.task_planner import TaskPlanner
from .adaptive_agent.task_executor import TaskExecutor
from .agent_registry import agent_registry, AgentRegistry, AgentInfo, AgentType
from . import utils

# Inicializar el registro de agentes al importar el módulo
# Eliminado: doble inicialización innecesaria

__all__ = [
    'DefaultAgent',
    'DefaultAgentConfig',
    'DefaultNeedAnalyzer',
    'DefaultToolExecutor',
    'DefaultResponseGenerator',
    'AdaptiveAgent',
    'TaskStatus',
    'TaskStep', 
    'TaskPlan',
    'TaskAnalyzer',
    'TaskPlanner',
    'AdaptiveTaskPlanner',
    'TaskExecutor',
    'agent_registry',
    'AgentRegistry',
    'AgentInfo',
    'AgentType',
    'utils'
]
