"""
MCP Manager - Gestiona la selección y estado de herramientas MCP para el asistente
"""
from typing import List, Dict, Any
import threading
from app.utils.logger import logger
from app.core.mcp_registry import MCPRegistry

class MCPManager:
    """
    Singleton para gestionar la selección de herramientas MCP activas
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MCPManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._selected_tools: List[str] = []
            self._available_tools: Dict[str, Dict[str, Any]] = {}
            self._tools_enabled: bool = False
            self._registry = MCPRegistry()
            self._initialized = True
            logger.info("MCP manager initialized with MCPRegistry")
            self._update_available_tools()

    def _update_available_tools(self):
        if not self._registry:
            return
        self._available_tools = {}
        for tool_name in self._registry.list_tools():
            tool_info = self._registry.get_tool_info(tool_name)
            if tool_info:
                self._available_tools[tool_name] = tool_info
        if not self._selected_tools:
            self._selected_tools = [
                tool_name for tool_name, info in self._available_tools.items()
                if info["available"]
            ]

    def initialize_registry(self, registry):
        self._registry = registry
        self._update_available_tools()
        logger.info(f"MCPManager: Registry inicializado con {len(self._available_tools)} herramientas")

    def set_tools_enabled(self, enabled: bool):
        self._tools_enabled = enabled
        logger.info(f"MCPManager: Tools {'habilitado' if enabled else 'deshabilitado'}")

    def is_tools_enabled(self) -> bool:
        return self._tools_enabled

    def set_selected_tools(self, tool_names: List[str]):
        valid_tools = [
            name for name in tool_names
            if name in self._available_tools and self._available_tools[name]["available"]
        ]
        self._selected_tools = valid_tools
        logger.info(f"MCPManager: Herramientas seleccionadas: {self._selected_tools}")

    def get_selected_tools(self) -> List[str]:
        return self._selected_tools.copy()

    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        return self._available_tools.copy()

    def get_active_tools(self) -> List[str]:
        if not self._tools_enabled:
            return []
        active_tools = [
            tool_name for tool_name in self._selected_tools
            if tool_name in self._available_tools and self._available_tools[tool_name]["available"]
        ]
        return active_tools

    def is_tool_active(self, tool_name: str) -> bool:
        return (
            self._tools_enabled and
            tool_name in self._selected_tools and
            tool_name in self._available_tools and
            self._available_tools[tool_name]["available"]
        )

    def refresh_tools(self):
        if self._registry:
            self._registry.refresh_discovery()
            self._update_available_tools()
            logger.info("MCPManager: Herramientas refrescadas")

    def get_tools_summary(self) -> Dict[str, Any]:
        tools = self.get_available_tools()
        return {
            "tools_enabled": self._tools_enabled,
            "total_available": len(self._available_tools),
            "total_selected": len(self._selected_tools),
            "active_tools": self.get_active_tools(),
            "available_tools": tools
        }

    def get_tool(self, tool_name: str):
        """Obtener la instancia MCPTool (como get_tool en tools_manager)"""
        if tool_name in self._registry._tools:
            return self._registry._tools[tool_name]
        return None

    def list_tools(self) -> List[str]:
        """Lista todas las herramientas MCP conocidas"""
        return list(self._available_tools.keys())

    def get_tools_info_for_model(self) -> str:
        """Generar información de herramientas para el modelo (solo las activas)"""
        if not self.is_tools_enabled():
            return "No hay herramientas MCP disponibles."
        active_tools = self.get_active_tools()
        if not active_tools:
            return "No hay herramientas MCP seleccionadas."
        instructions = "Funciones MCP disponibles:\n"
        for tool_name in active_tools:
            tool_info = self._available_tools.get(tool_name)
            if tool_info:
                instructions += f"[Funcion: '{tool_name}', query: '{tool_info['description']}']\n"
        return instructions

    @property
    def registry(self):
        return self._registry

# Instancia global del gestor de herramientas MCP
mcp_manager = MCPManager()
