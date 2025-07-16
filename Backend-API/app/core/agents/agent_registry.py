"""
@Author: Borja Otero Ferreira
Registro de agentes - Sistema centralizado para gestionar agentes disponibles
"""
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum
import inspect
from app.utils.logger import logger


class AgentType(Enum):
    """Tipos de agentes disponibles"""
    DEFAULT = "default"
    ADAPTIVE = "adaptive" 
    LINEAL = "lineal"


@dataclass
class AgentInfo:
    """Información sobre un agente"""
    name: str
    display_name: str
    description: str
    agent_type: AgentType
    agent_class: Type
    config_class: Type = None
    icon: str = "🤖"
    is_active: bool = True


class AgentRegistry:
    """
    Registro centralizado de agentes disponibles
    Permite registrar, descubrir y seleccionar agentes dinámicamente
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._current_agent: Optional[str] = None
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Inicializa los agentes por defecto del sistema"""
        try:
            # Importar aquí para evitar dependencias circulares
            from .default_agent.default_agent import DefaultAgent
            from .default_agent.config import DefaultAgentConfig
            from .adaptive_agent.adaptive_agent import AdaptiveAgent
            from .adaptive_agent.config import AdaptiveAgentConfig
            
            # Registrar agente por defecto
            self.register_agent(AgentInfo(
                name="default",
                display_name="Agente Estándar",
                description="Agente base para conversaciones normales sin planificacion de tareas",
                agent_type=AgentType.DEFAULT,
                agent_class=DefaultAgent,
                config_class=DefaultAgentConfig,
                icon="💬"
            ))
            
            # Registrar agente adaptativo
            self.register_agent(AgentInfo(
                name="adaptive",
                display_name="Agente Adaptativo",
                description="Agente inteligente que planifica paso a paso como un humano",
                agent_type=AgentType.ADAPTIVE,
                agent_class=AdaptiveAgent,
                config_class=AdaptiveAgentConfig,
                icon="🧠"
            ))
            
  
            
            # Establecer agente por defecto
            self._current_agent = "adaptive"
            
            logger.info(f"Agentes registrados: {list(self._agents.keys())}")
            print(f" AGENTES REGISTRADOS: {list(self._agents.keys())}")
            print(f" AGENTE ACTUAL: {self._current_agent}")
            
        except Exception as e:
            logger.error(f"Error inicializando agentes por defecto: {e}")
    
    def register_agent(self, agent_info: AgentInfo):
        """Registra un nuevo agente en el sistema"""
        try:
            self._agents[agent_info.name] = agent_info
            logger.info(f"Agente '{agent_info.name}' registrado exitosamente")
        except Exception as e:
            logger.error(f"Error registrando agente '{agent_info.name}': {e}")
    
    def get_agent_info(self, agent_name: str) -> Optional[AgentInfo]:
        """Obtiene información sobre un agente específico"""
        return self._agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Obtiene todos los agentes registrados"""
        return self._agents.copy()
    
    def get_active_agents(self) -> Dict[str, AgentInfo]:
        """Obtiene solo los agentes activos"""
        return {name: info for name, info in self._agents.items() if info.is_active}
    
    def set_current_agent(self, agent_name: str) -> bool:
        """Establece el agente actual"""
        if agent_name in self._agents:
            self._current_agent = agent_name
            logger.info(f"Agente actual establecido: {agent_name}")
            return True
        else:
            logger.warning(f"Agente '{agent_name}' no encontrado")
            return False
    
    def get_current_agent(self) -> Optional[str]:
        """Obtiene el agente actual"""
        return self._current_agent
    
    def create_agent(self, agent_name: str, *args, **kwargs):
        """Crea una instancia del agente especificado"""
        agent_info = self._agents.get(agent_name)
        if not agent_info:
            raise ValueError(f"Agente '{agent_name}' no encontrado")
        
        if not agent_info.is_active:
            raise ValueError(f"Agente '{agent_name}' no está activo")
        
        try:
            # Crear instancia del agente
            agent_instance = agent_info.agent_class(*args, **kwargs)
            logger.info(f"Instancia del agente '{agent_name}' creada exitosamente")
            return agent_instance
        except Exception as e:
            logger.error(f"Error creando instancia del agente '{agent_name}': {e}")
            raise
    
    def get_agent_for_frontend(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de agentes formateada para el frontend"""
        agents_list = []
        
        for name, info in self.get_active_agents().items():
            agents_list.append({
                'id': name,
                'name': info.display_name,
                'description': info.description,
                'icon': info.icon,
                'type': info.agent_type.value,
                'is_current': name == self._current_agent
            })
        
        return agents_list
    
    def activate_agent(self, agent_name: str) -> bool:
        """Activa un agente"""
        if agent_name in self._agents:
            self._agents[agent_name].is_active = True
            logger.info(f"Agente '{agent_name}' activado")
            return True
        return False
    
    def deactivate_agent(self, agent_name: str) -> bool:
        """Desactiva un agente"""
        if agent_name in self._agents:
            self._agents[agent_name].is_active = False
            logger.info(f"Agente '{agent_name}' desactivado")
            return True
        return False


# Instancia global del registro
agent_registry = AgentRegistry()
