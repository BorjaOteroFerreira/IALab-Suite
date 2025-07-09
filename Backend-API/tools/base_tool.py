"""
Base interface para todas las herramientas del sistema IALab Suite.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
from enum import Enum

class ToolCategory(Enum):
    """Categorías de herramientas disponibles"""
    SEARCH = "search"
    MEDIA = "media"
    FINANCE = "finance"
    IMAGE = "image"
    ANALYSIS = "analysis"
    UTILITY = "utility"

@dataclass
class ToolMetadata:
    """Metadatos de una herramienta"""
    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    author: str = "IALab Suite"
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    parameters: Dict[str, Any] = None
    usage_example: Optional[dict] = None  # <-- Añadido para soportar ejemplos de uso

class BaseTool(ABC):
    """
    Clase base abstracta para todas las herramientas.
    Todas las herramientas deben heredar de esta clase.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Retorna los metadatos de la herramienta"""
        pass
    
    @abstractmethod
    def execute(self, query: str, **kwargs) -> Any:
        """
        Ejecuta la herramienta con la consulta dada.
        
        Args:
            query (str): La consulta o entrada para la herramienta
            **kwargs: Parámetros adicionales específicos de la herramienta
            
        Returns:
            Any: El resultado de la ejecución de la herramienta
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_tool_name(cls) -> str:
        """Retorna el nombre único de la herramienta"""
        pass
    
    def validate_api_key(self) -> bool:
        """
        Valida si la herramienta tiene las claves API necesarias.
        
        Returns:
            bool: True si tiene las claves necesarias, False en caso contrario
        """
        if not self.metadata.requires_api_key:
            return True
        
        if self.metadata.api_key_env_var:
            import os
            return bool(os.getenv(self.metadata.api_key_env_var))
        
        return True
    
    def is_available(self) -> bool:
        """
        Verifica si la herramienta está disponible para usar.
        
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        return self.validate_api_key()
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Retorna información de uso de la herramienta.
        
        Returns:
            Dict[str, Any]: Información sobre cómo usar la herramienta
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "parameters": self.metadata.parameters or {},
            "requires_api_key": self.metadata.requires_api_key,
            "available": self.is_available()
        }

class ToolExecutionResult:
    """Resultado de la ejecución de una herramienta"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, metadata: Dict[str, Any] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = __import__('datetime').datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        if self.success:
            return str(self.data)
        else:
            return f"Error: {self.error}"
