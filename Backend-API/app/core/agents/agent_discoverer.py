import importlib
import pkgutil
import inspect
from pathlib import Path
from .base_agent import BaseAgent

AGENT_REGISTRY = {}


def add_discovery_path(paths_list, path: str) -> None:
    """
    Añade un directorio para auto-discovery de agentes.
    """
    path_obj = Path(path)
    if path_obj.exists() and path_obj.is_dir():
        paths_list.append(path_obj)


def autodiscover_agents(agents_dir: str = None) -> int:
    """
    Descubre automáticamente agentes en el directorio especificado.
    Args:
        agents_dir (str, optional): Directorio específico para escanear
    Returns:
        int: Número de agentes descubiertos
    """
    discovery_paths = []
    # Si no se especifica, usar el directorio 'z:/Github/IALab-Suite/Backend-API/app/core/agents'
    if not agents_dir:
        base_dir = Path(__file__).parent.parent
        agents_dir = str(base_dir)
    add_discovery_path(discovery_paths, agents_dir)
    discovered_count = 0
    for discovery_path in discovery_paths:
        discovered_count += _scan_agents_directory(discovery_path)
    return discovered_count


def _scan_agents_directory(directory: Path) -> int:
    """
    Escanea un directorio y sus subdirectorios buscando agentes.
    """
    count = 0
    for python_file in directory.rglob("*.py"):
        if python_file.name in ["__init__.py", "base_agent.py", "agent_discoverer.py"]:
            continue
        try:
            count += _load_agents_from_file(python_file)
        except Exception as e:
            print(f"Error loading agents from {python_file}: {e}")
    return count


def _load_agents_from_file(file_path: Path) -> int:
    """
    Carga agentes desde un archivo Python específico.
    """
    count = 0
    module_name = f"app.core.agents.{file_path.stem}"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    AGENT_REGISTRY[name] = obj
                    count += 1
    except Exception as e:
        print(f"Error importing agent module from {file_path}: {e}")
    return count
