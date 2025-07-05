"""
@Author: Borja Otero Ferreira
Tools package for IALab Suite Cortex
"""

# Import all tools for easy access
from .base_tool import BaseTool, ToolCategory, ToolExecutionResult
from .tool_registry import ToolRegistry
from .search_tools import SearchTools
from .advanced_search import AdvancedSearchTools
from .image_search_tool import ImageSearchTool
from .video_search_tool import YoutubeVideoSearchTool
from .ip_info_tool import IpInfoTool
from .cripto_price import CriptoPrice
from .generate_image import ImageGenerationTool
from .buscar_internet import GoogleSearchTool, buscar_internet

__all__ = [
    'BaseTool',
    'ToolCategory', 
    'ToolExecutionResult',
    'ToolRegistry',
    'SearchTools',
    'AdvancedSearchTools',
    'ImageSearchTool',
    'YoutubeVideoSearchTool',
    'IpInfoTool',
    'CriptoPrice',
    'ImageGenerationTool',
    'GoogleSearchTool',
    'buscar_internet'
]
