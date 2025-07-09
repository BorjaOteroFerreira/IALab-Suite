"""
@Author: Borja Otero Ferreira
Tools Manager - Gestiona la selección y estado de herramientas para el asistente
"""

from typing import List, Dict, Any, Optional
import threading
from enum import Enum
from app.utils.logger import logger


class ToolsManager:
    """
    Singleton para gestionar la selección de herramientas activas
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ToolsManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._selected_tools: List[str] = []
            self._available_tools: Dict[str, Dict[str, Any]] = {}
            self._tools_enabled: bool = False
            self._registry = None
            self._initialized = True
            logger.info("Tools manager initialized with assistant service")
    
    def initialize_registry(self, tool_registry):
        """Inicializar con el registry de herramientas"""
        self._registry = tool_registry
        self._update_available_tools()
        logger.info(f"ToolsManager: Registry inicializado con {len(self._available_tools)} herramientas")
    
    def _update_available_tools(self):
        """Actualizar la lista de herramientas disponibles desde el registry"""
        if not self._registry:
            return
            
        self._available_tools = {}
        for tool_name in self._registry.list_tools():
            tool_info = self._registry.get_tool_info(tool_name)
            if tool_info:
                tool_instance = self._registry.get_tool(tool_name)
                self._available_tools[tool_name] = {
                    "name": tool_info.get("name", tool_name),
                    "description": tool_info.get("description", "Sin descripción"),
                    "category": tool_info.get("category", "utility"),
                    "available": tool_info.get("available", False),
                    "requires_api_key": tool_info.get("requires_api_key", False),
                    "parameters": tool_info.get("parameters", {}),
                    "usage_example": tool_info.get("usage_example", None),
                    "metadata": tool_instance.metadata if tool_instance else None
                }
        
        # Si no hay herramientas seleccionadas, seleccionar todas las disponibles por defecto
        if not self._selected_tools:
            self._selected_tools = [
                tool_name for tool_name, info in self._available_tools.items() 
                if info["available"]
            ]
    
    def set_tools_enabled(self, enabled: bool):
        """Habilitar o deshabilitar el uso de herramientas"""
        self._tools_enabled = enabled
        logger.info(f"ToolsManager: Tools {'habilitado' if enabled else 'deshabilitado'}")
    
    def is_tools_enabled(self) -> bool:
        """Verificar si las herramientas están habilitadas"""
        return self._tools_enabled
    
    def set_selected_tools(self, tool_names: List[str]):
        """Establecer las herramientas seleccionadas"""
        # Filtrar solo herramientas que existen y están disponibles
        valid_tools = [
            name for name in tool_names 
            if name in self._available_tools and self._available_tools[name]["available"]
        ]
        
        # Verificar si ha cambiado la selección
        tools_changed = set(self._selected_tools) != set(valid_tools)
        
        self._selected_tools = valid_tools
        logger.info(f"ToolsManager: Herramientas seleccionadas: {self._selected_tools}")
        
    
    
    
    def get_selected_tools(self) -> List[str]:
        """Obtener las herramientas seleccionadas"""
        return self._selected_tools.copy()
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todas las herramientas disponibles con su información"""
        return self._available_tools.copy()
    
    def get_active_tools(self) -> List[str]:
        """Obtener herramientas que están habilitadas Y seleccionadas Y disponibles"""
        if not self._tools_enabled:
            return []
            
        # Filtrar las herramientas que están seleccionadas y disponibles
        active_tools = [
            tool_name for tool_name in self._selected_tools 
            if tool_name in self._available_tools and 
            self._available_tools[tool_name]["available"]
        ]
        return active_tools
    
    def is_tool_active(self, tool_name: str) -> bool:
        """Verificar si una herramienta específica está activa"""
        return (self._tools_enabled and 
                tool_name in self._selected_tools and 
                tool_name in self._available_tools and 
                self._available_tools[tool_name]["available"])
    
    def get_tools_info_for_model(self) -> str:
        """Generar información detallada de herramientas para el modelo (solo las activas)"""
        if not self.is_tools_enabled():
            return "No hay herramientas disponibles."
        
        active_tools = self.get_active_tools()
        if not active_tools:
            return "No hay herramientas seleccionadas."
        
        instructions = "HERRAMIENTAS DISPONIBLES:\n"
        instructions += "="*60 + "\n\n"
        
        for i, tool_name in enumerate(active_tools, 1):
            tool_info = self._available_tools.get(tool_name)
            if not tool_info:
                continue
                
            instructions += f"{i}. HERRAMIENTA: {tool_info['name']}\n"
            instructions += f"   Identificador: '{tool_name}'\n"
            instructions += f"   Descripción: {tool_info['description']}\n"
            
            # Agregar parámetros si existen
            if tool_info.get('parameters'):
                instructions += f"   Parámetros:\n"
                for param_name, param_desc in tool_info['parameters'].items():
                    instructions += f"     - {param_name}: {param_desc}\n"
            
            # Agregar ejemplos de uso si existen
            usage_example = tool_info.get('usage_example')
            if usage_example:
                instructions += f"   Ejemplos de uso:\n"
                
                if isinstance(usage_example, dict):
                    for example_key, example_value in usage_example.items():
                        if isinstance(example_value, list):
                            instructions += f"     {example_key}:\n"
                            for item in example_value:
                                instructions += f"       • {item}\n"
                        else:
                            instructions += f"     {example_key}: {example_value}\n"
                elif isinstance(usage_example, str):
                    instructions += f"     {usage_example}\n"
                elif isinstance(usage_example, list):
                    for example in usage_example:
                        instructions += f"     • {example}\n"
            
            instructions += "\n" + "-"*50 + "\n\n"
        
        instructions += "INSTRUCCIONES DE USO:\n"
        instructions += "Para usar una herramienta, utiliza el formato:\n"
        instructions += '{"tool": "nombre_herramienta", "query": "tu_consulta"}\n\n'
        instructions += "Donde:\n"
        instructions += "- 'nombre_herramienta' es el identificador de la herramienta\n"
        instructions += "- 'tu_consulta' es la consulta o parámetros necesarios\n\n"
        
        return instructions
    
    def get_tools_info_for_model_simple(self) -> str:
        """Generar información simplificada de herramientas para el modelo (formato original)"""
        if not self.is_tools_enabled():
            return "No hay herramientas disponibles."
        
        active_tools = self.get_active_tools()
        if not active_tools:
            return "No hay herramientas seleccionadas."
        
        instructions = "Funciones disponibles:\n"
        for tool_name in active_tools:
            tool_info = self._available_tools.get(tool_name)
            if tool_info:
                instructions += f"[Funcion: '{tool_name}', query: '{tool_info['description']}']\n"
        
        return instructions
    
    def refresh_tools(self):
        """Refrescar la lista de herramientas desde el registry"""
        if self._registry:
            self._registry.reload_tools()
            self._update_available_tools()
            logger.info("ToolsManager: Herramientas refrescadas")
    
    def get_tools_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado actual de herramientas"""
        tools = self.get_available_tools()
        
        # Procesar las herramientas para asegurar que category siempre sea un string
        processed_tools = {}
        for name, tool_info in tools.items():
            processed_tool = dict(tool_info)  # Copia del diccionario
            # Convertir category si es un Enum
            if isinstance(processed_tool.get('category'), Enum):
                processed_tool['category'] = processed_tool['category'].value
            # Manejar metadata si existe
            if 'metadata' in processed_tool and processed_tool['metadata']:
                if hasattr(processed_tool['metadata'], 'category') and isinstance(processed_tool['metadata'].category, Enum):
                    # Crear una copia de metadata como diccionario
                    metadata_dict = {}
                    for key, value in processed_tool['metadata'].__dict__.items():
                        if isinstance(value, Enum):
                            metadata_dict[key] = value.value
                        else:
                            metadata_dict[key] = value
                    processed_tool['metadata'] = metadata_dict
            processed_tools[name] = processed_tool
        
        return {
            "tools_enabled": self._tools_enabled,
            "total_available": len(self._available_tools),
            "total_selected": len(self._selected_tools),
            "active_tools": self.get_active_tools(),
            "available_tools": processed_tools
        }


# Instancia global del gestor de herramientas
tools_manager = ToolsManager()