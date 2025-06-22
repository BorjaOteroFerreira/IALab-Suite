"""
Sistema de registro y auto-discovery de herramientas para IALab Suite.
"""
import os
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from .base_tool import BaseTool, ToolCategory, ToolExecutionResult
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Registry singleton para herramientas que implementa auto-discovery
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._tools: Dict[str, Type[BaseTool]] = {}
            self._tool_instances: Dict[str, BaseTool] = {}
            self._categories: Dict[ToolCategory, List[str]] = {}
            self._discovery_paths: List[Path] = []
            ToolRegistry._initialized = True
    
    def add_discovery_path(self, path: str) -> None:
        """
        Añade un directorio para auto-discovery de herramientas.
        
        Args:
            path (str): Ruta del directorio a escanear
        """
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_dir():
            self._discovery_paths.append(path_obj)
            logger.info(f"Added discovery path: {path}")
        else:
            logger.warning(f"Discovery path does not exist: {path}")
    
    def discover_tools(self, tools_dir: str = None) -> int:
        """
        Descubre automáticamente herramientas en el directorio especificado.
        
        Args:
            tools_dir (str, optional): Directorio específico para escanear
            
        Returns:
            int: Número de herramientas descubiertas
        """
        if tools_dir:
            self.add_discovery_path(tools_dir)
        
        # Si no hay paths, usar el directorio actual de tools
        if not self._discovery_paths:
            current_dir = Path(__file__).parent
            self.add_discovery_path(str(current_dir))
        
        discovered_count = 0
        
        for discovery_path in self._discovery_paths:
            discovered_count += self._scan_directory(discovery_path)
        
        logger.info(f"Tool discovery completed. Found {discovered_count} tools.")
        return discovered_count
    
    def _scan_directory(self, directory: Path) -> int:
        """
        Escanea un directorio buscando herramientas.
        
        Args:
            directory (Path): Directorio a escanear
            
        Returns:
            int: Número de herramientas encontradas
        """
        count = 0
        
        # Buscar archivos Python que no sean __init__.py o base_tool.py
        for python_file in directory.glob("*.py"):
            if python_file.name in ["__init__.py", "base_tool.py", "tool_registry.py"]:
                continue
            
            try:
                count += self._load_tools_from_file(python_file)
            except Exception as e:
                logger.error(f"Error loading tools from {python_file}: {e}")
        
        return count
    
    def _load_tools_from_file(self, file_path: Path) -> int:
        """
        Carga herramientas desde un archivo Python específico.
        
        Args:
            file_path (Path): Ruta del archivo Python
            
        Returns:
            int: Número de herramientas cargadas
        """
        count = 0
        
        # Crear nombre de módulo
        module_name = f"tools.{file_path.stem}"
        
        try:
            # Importar el módulo
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Buscar clases que hereden de BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj != BaseTool and 
                        issubclass(obj, BaseTool) and 
                        not inspect.isabstract(obj)):
                        
                        count += self._register_tool_class(obj)
                        
        except Exception as e:
            logger.error(f"Error importing module from {file_path}: {e}")
        
        return count
    
    def _register_tool_class(self, tool_class: Type[BaseTool]) -> int:
        """
        Registra una clase de herramienta.
        
        Args:
            tool_class (Type[BaseTool]): Clase de herramienta a registrar
            
        Returns:
            int: 1 si se registró exitosamente, 0 en caso contrario
        """
        try:
            # Obtener el nombre de la herramienta
            tool_name = tool_class.get_tool_name()
            
            # Verificar si ya está registrada
            if tool_name in self._tools:
                logger.warning(f"Tool {tool_name} already registered, skipping...")
                return 0
            
            # Registrar la herramienta
            self._tools[tool_name] = tool_class
            
            # Crear instancia para obtener metadatos
            try:
                instance = tool_class()
                self._tool_instances[tool_name] = instance
                
                # Categorizar
                category = instance.metadata.category
                if category not in self._categories:
                    self._categories[category] = []
                self._categories[category].append(tool_name)
                
                logger.info(f"Registered tool: {tool_name} ({category.value})")
                return 1
                
            except Exception as e:
                logger.error(f"Error instantiating tool {tool_name}: {e}")
                return 0
                
        except Exception as e:
            logger.error(f"Error registering tool class {tool_class}: {e}")
            return 0
    
    def register_tool(self, tool_class: Type[BaseTool]) -> bool:
        """
        Registra manualmente una herramienta.
        
        Args:
            tool_class (Type[BaseTool]): Clase de herramienta a registrar
            
        Returns:
            bool: True si se registró exitosamente
        """
        return self._register_tool_class(tool_class) == 1
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Obtiene una instancia de herramienta por nombre.
        
        Args:
            tool_name (str): Nombre de la herramienta
            
        Returns:
            Optional[BaseTool]: Instancia de la herramienta o None
        """
        return self._tool_instances.get(tool_name)
    
    def get_tool_class(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """
        Obtiene la clase de una herramienta por nombre.
        
        Args:
            tool_name (str): Nombre de la herramienta
            
        Returns:
            Optional[Type[BaseTool]]: Clase de la herramienta o None
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        Lista todas las herramientas registradas.
        
        Returns:
            List[str]: Lista de nombres de herramientas
        """
        return list(self._tools.keys())
    
    def list_available_tools(self) -> List[str]:
        """
        Lista herramientas disponibles (con API keys válidas).
        
        Returns:
            List[str]: Lista de nombres de herramientas disponibles
        """
        available = []
        for tool_name, tool_instance in self._tool_instances.items():
            if tool_instance.is_available():
                available.append(tool_name)
        return available
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """
        Obtiene herramientas por categoría.
        
        Args:
            category (ToolCategory): Categoría de herramientas
            
        Returns:
            List[str]: Lista de nombres de herramientas en la categoría
        """
        return self._categories.get(category, [])
    
    def execute_tool(self, tool_name: str, query: str, **kwargs) -> ToolExecutionResult:
        """
        Ejecuta una herramienta por nombre.
        
        Args:
            tool_name (str): Nombre de la herramienta
            query (str): Consulta para la herramienta
            **kwargs: Parámetros adicionales
            
        Returns:
            ToolExecutionResult: Resultado de la ejecución
        """
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                return ToolExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found"
                )
            
            if not tool.is_available():
                return ToolExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' is not available (missing API key?)"
                )
            
            # Ejecutar la herramienta
            result = tool.execute(query, **kwargs)
            
            return ToolExecutionResult(
                success=True,
                data=result,
                metadata={
                    "tool_name": tool_name,
                    "tool_category": tool.metadata.category.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolExecutionResult(
                success=False,
                error=str(e),
                metadata={"tool_name": tool_name}
            )
    
    def get_tools_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada de todas las herramientas.
        
        Returns:
            Dict[str, Any]: Información de todas las herramientas
        """
        tools_info = {}
        
        for tool_name, tool_instance in self._tool_instances.items():
            tools_info[tool_name] = tool_instance.get_usage_info()
        
        return tools_info
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del registry.
        
        Returns:
            Dict[str, Any]: Estadísticas del registry
        """
        available_count = len(self.list_available_tools())
        total_count = len(self._tools)
        
        category_stats = {}
        for category, tools in self._categories.items():
            category_stats[category.value] = len(tools)
        
        return {
            "total_tools": total_count,
            "available_tools": available_count,
            "unavailable_tools": total_count - available_count,
            "categories": category_stats,
            "discovery_paths": [str(p) for p in self._discovery_paths]
        }
    
    def reload_tools(self) -> int:
        """
        Recarga todas las herramientas.
        
        Returns:
            int: Número de herramientas recargadas
        """
        # Limpiar registry
        self._tools.clear()
        self._tool_instances.clear()
        self._categories.clear()
        
        # Redescubrir herramientas
        return self.discover_tools()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada sobre una herramienta específica.
        
        Args:
            tool_name (str): Nombre de la herramienta
            
        Returns:
            Optional[Dict[str, Any]]: Información de la herramienta o None si no existe
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.get_usage_info()
        return None
    
    @property
    def tools(self) -> Dict[str, BaseTool]:
        """
        Devuelve el diccionario de instancias de herramientas registradas.
        """
        return self._tool_instances

# Instancia global del registry
tool_registry = ToolRegistry()
