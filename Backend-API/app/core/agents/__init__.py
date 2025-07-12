"""
@Author: Borja Otero Ferreira
Paquete del agente autónomo modularizado
"""
from .agent_registry import agent_registry, AgentRegistry, AgentInfo, AgentType
from . import utils

__all__ = [
    'agent_registry',
    'AgentRegistry',
    'AgentInfo',
    'AgentType',
    'utils'
]
