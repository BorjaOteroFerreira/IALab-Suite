"""
MCPRegistry - Descubre y gestiona herramientas MCP gratuitas (implementación real)
Actualizado con repositorios extendidos y mejor logging
"""
import json
import subprocess
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
from dataclasses import dataclass, asdict
import time

@dataclass
class MCPTool:
    name: str
    description: str
    category: str
    available: bool
    requires_api_key: bool
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    install_command: Optional[str] = None
    github_url: Optional[str] = None
    version: Optional[str] = None

class MCPRegistry:
    def __init__(self, cache_file: str = "mcp_tools_cache.json"):
        self.cache_file = cache_file
        self.logger = self._setup_logger()
        self._tools: Dict[str, MCPTool] = {}
        self._selected_tools: List[str] = []
        # Lista actualizada con muchos más repositorios
        self.known_mcp_repos = self._get_extended_mcp_repos()
        self._load_cache()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("MCPRegistry")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _get_extended_mcp_repos(self) -> List[str]:
        """Retorna la lista extendida de repositorios MCP organizados por prioridad"""
        return [
            # 🔥 Oficiales (prioridad máxima)
            "modelcontextprotocol/servers",
            "anthropics/mcp-example-servers", 
            "docker/mcp-servers",
            
            # 🔥 Awesome lists (prioridad alta - muchos servers)
            "punkpeye/awesome-mcp-servers",
            "wong2/awesome-mcp-servers",
            "appcypher/awesome-mcp-servers",
            "TensorBlock/awesome-mcp-servers",
            "apappascs/mcp-servers-hub",
            

        ]

    def _load_cache(self):
        """Carga herramientas desde cache si existe"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    self._tools = {
                        name: MCPTool(**tool_data)
                        for name, tool_data in cached_data.get('tools', {}).items()
                    }
                    self._selected_tools = cached_data.get('selected_tools', [])
                self.logger.info(f"Cargadas {len(self._tools)} herramientas desde cache")
            except Exception as e:
                self.logger.error(f"Error cargando cache: {e}")

    def _save_cache(self):
        """Guarda herramientas en cache"""
        try:
            cache_data = {
                'tools': {name: asdict(tool) for name, tool in self._tools.items()},
                'selected_tools': self._selected_tools
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.info("Cache actualizado")
        except Exception as e:
            self.logger.error(f"Error guardando cache: {e}")

    def discover_github_mcp_tools(self) -> List[Dict[str, Any]]:
        """Descubre herramientas MCP desde repositorios de GitHub extendidos"""
        tools = []
        successful_repos = 0
        failed_repos = 0
        
        self.logger.info(f"Iniciando descubrimiento en {len(self.known_mcp_repos)} repositorios...")
        
        for i, repo in enumerate(self.known_mcp_repos):
            if not repo.strip():  # Saltar repos vacíos
                continue
                
            self.logger.info(f"[{i+1}/{len(self.known_mcp_repos)}] Procesando: {repo}")
            
            try:
                # API de GitHub para obtener información del repositorio
                api_url = f"https://api.github.com/repos/{repo}"
                response = requests.get(api_url, timeout=15)  # Timeout aumentado
                
                if response.status_code == 200:
                    repo_data = response.json()
                    self.logger.info(f"✓ Repositorio {repo} encontrado - {repo_data.get('description', 'Sin descripción')}")
                    
                    # Buscar contenido del repositorio
                    contents_url = f"https://api.github.com/repos/{repo}/contents"
                    contents_response = requests.get(contents_url, timeout=15)
                    
                    if contents_response.status_code == 200:
                        contents = contents_response.json()
                        repo_tools = []
                        
                        for item in contents:
                            if item['type'] == 'dir':
                                # Explorar subdirectorios que podrían contener herramientas MCP
                                dir_tools = self._explore_mcp_directory(repo, item['name'])
                                repo_tools.extend(dir_tools)
                                tools.extend(dir_tools)
                        
                        self.logger.info(f"  → Encontradas {len(repo_tools)} herramientas en {repo}")
                        successful_repos += 1
                        
                    else:
                        self.logger.warning(f"  → No se pudo acceder al contenido de {repo} (status: {contents_response.status_code})")
                        
                elif response.status_code == 404:
                    self.logger.warning(f"✗ Repositorio {repo} no encontrado (404)")
                    failed_repos += 1
                elif response.status_code == 403:
                    self.logger.warning(f"✗ Rate limit excedido en {repo} (403) - pausando 10s")
                    failed_repos += 1
                    time.sleep(10)  # Pausa para rate limit
                else:
                    self.logger.warning(f"✗ Error {response.status_code} accediendo a {repo}")
                    failed_repos += 1
                    
            except Exception as e:
                self.logger.error(f"✗ Error explorando repositorio {repo}: {e}")
                failed_repos += 1
                
            # Pequeña pausa para evitar rate limiting
            time.sleep(1)
                
        self.logger.info(f"Descubrimiento completado: {successful_repos} exitosos, {failed_repos} fallidos")
        return tools

    def _explore_mcp_directory(self, repo: str, directory: str) -> List[Dict[str, Any]]:
        """Explora un directorio específico buscando herramientas MCP"""
        tools = []
        
        try:
            dir_url = f"https://api.github.com/repos/{repo}/contents/{directory}"
            response = requests.get(dir_url, timeout=15)
            
            if response.status_code == 200:
                files = response.json()
                
                # Buscar archivos que indiquen una herramienta MCP
                has_package_json = any(f['name'] == 'package.json' for f in files)
                has_setup_py = any(f['name'] == 'setup.py' for f in files)
                has_pyproject_toml = any(f['name'] == 'pyproject.toml' for f in files)
                has_dockerfile = any(f['name'] == 'Dockerfile' for f in files)
                
                # Más flexible: cualquier directorio con estructura de proyecto
                if has_package_json or has_setup_py or has_pyproject_toml or has_dockerfile or len(files) > 3:
                    # Obtener información del README
                    readme_info = self._get_readme_info(repo, directory)
                    
                    tool_info = {
                        'name': directory,
                        'description': readme_info.get('description', f'Herramienta MCP: {directory}'),
                        'category': self._infer_category(directory, readme_info),
                        'github_url': f"https://github.com/{repo}/tree/main/{directory}",
                        'install_command': self._infer_install_command(files, repo, directory),
                        'requires_api_key': self._check_requires_api_key(readme_info),
                        'metadata': readme_info
                    }
                    
                    self.logger.debug(f"    ✓ Detectada herramienta: {directory}")
                    tools.append(tool_info)
                    
            else:
                self.logger.debug(f"    ✗ No se pudo acceder a {directory} (status: {response.status_code})")
                
        except Exception as e:
            self.logger.debug(f"    ✗ Error explorando directorio {directory}: {e}")
            
        return tools

    def _get_readme_info(self, repo: str, directory: str) -> Dict[str, Any]:
        """Obtiene información del README de una herramienta"""
        readme_files = ['README.md', 'readme.md', 'README.txt', 'README.rst']
        
        for readme_file in readme_files:
            try:
                readme_url = f"https://api.github.com/repos/{repo}/contents/{directory}/{readme_file}"
                response = requests.get(readme_url, timeout=10)
                
                if response.status_code == 200:
                    readme_data = response.json()
                    if readme_data.get('encoding') == 'base64':
                        import base64
                        content = base64.b64decode(readme_data['content']).decode('utf-8')
                        return self._parse_readme_content(content)
                        
            except Exception as e:
                self.logger.debug(f"Error obteniendo {readme_file} para {directory}: {e}")
                
        return {}

    def _parse_readme_content(self, content: str) -> Dict[str, Any]:
        """Parsea el contenido del README para extraer información"""
        lines = content.split('\n')
        info = {}
        
        # Extraer título y descripción
        for i, line in enumerate(lines):
            if line.startswith('# '):
                info['title'] = line[2:].strip()
                # Buscar descripción en las siguientes líneas
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        info['description'] = lines[j].strip()
                        break
                break
                
        # Buscar keywords relacionadas con funcionalidad
        content_lower = content.lower()
        if 'database' in content_lower or 'sql' in content_lower:
            info['category'] = 'database'
        elif 'web' in content_lower or 'http' in content_lower:
            info['category'] = 'web'
        elif 'file' in content_lower or 'filesystem' in content_lower:
            info['category'] = 'filesystem'
        elif 'ai' in content_lower or 'llm' in content_lower:
            info['category'] = 'ai'
        elif 'devops' in content_lower or 'cloud' in content_lower:
            info['category'] = 'devops'
        elif 'game' in content_lower or 'gaming' in content_lower:
            info['category'] = 'gaming'
        
        return info

    def _infer_category(self, name: str, readme_info: Dict[str, Any]) -> str:
        """Infiere la categoría de una herramienta basándose en su nombre y descripción"""
        if readme_info.get('category'):
            return readme_info['category']
            
        name_lower = name.lower()
        if 'database' in name_lower or 'sql' in name_lower or 'postgres' in name_lower:
            return 'database'
        elif 'web' in name_lower or 'http' in name_lower or 'api' in name_lower:
            return 'web'
        elif 'file' in name_lower or 'filesystem' in name_lower:
            return 'filesystem'
        elif 'search' in name_lower or 'elastic' in name_lower:
            return 'search'
        elif 'image' in name_lower or 'photo' in name_lower:
            return 'image'
        elif 'cloud' in name_lower or 'aws' in name_lower or 'azure' in name_lower:
            return 'cloud'
        elif 'docker' in name_lower or 'container' in name_lower:
            return 'devops'
        elif 'game' in name_lower or 'gaming' in name_lower:
            return 'gaming'
        elif 'ai' in name_lower or 'llm' in name_lower:
            return 'ai'
        else:
            return 'utility'

    def _infer_install_command(self, files: List[Dict], repo: str, directory: str) -> str:
        """Infiere el comando de instalación basándose en los archivos del proyecto"""
        if any(f['name'] == 'package.json' for f in files):
            return f"npm install https://github.com/{repo}/tree/main/{directory}"
        elif any(f['name'] == 'setup.py' for f in files):
            return f"pip install git+https://github.com/{repo}.git#subdirectory={directory}"
        elif any(f['name'] == 'pyproject.toml' for f in files):
            return f"pip install git+https://github.com/{repo}.git#subdirectory={directory}"
        elif any(f['name'] == 'Dockerfile' for f in files):
            return f"docker build -t {directory} https://github.com/{repo}.git#{directory}"
        else:
            return f"git clone https://github.com/{repo}.git && cd {directory}"

    def _check_requires_api_key(self, readme_info: Dict[str, Any]) -> bool:
        """Verifica si la herramienta requiere una API key"""
        content = str(readme_info).lower()
        api_keywords = ['api_key', 'api key', 'token', 'secret', 'credential', 'auth']
        return any(keyword in content for keyword in api_keywords)

    def check_installed_tools(self) -> List[str]:
        """Verifica qué herramientas MCP están instaladas localmente"""
        installed = []
        
        # Verificar herramientas instaladas via npm
        try:
            result = subprocess.run(['npm', 'list', '-g', '--depth=0'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'mcp-' in line:
                        tool_name = line.split('mcp-')[1].split('@')[0]
                        installed.append(f"mcp-{tool_name}")
        except Exception as e:
            self.logger.debug(f"Error verificando herramientas npm: {e}")

        # Verificar herramientas instaladas via pip
        try:
            result = subprocess.run(['pip', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'mcp' in line.lower():
                        tool_name = line.split()[0]
                        installed.append(tool_name)
        except Exception as e:
            self.logger.debug(f"Error verificando herramientas pip: {e}")

        return installed

    def discover_mcp_tools(self) -> Dict[str, MCPTool]:
        """Descubre herramientas MCP disponibles"""
        self.logger.info("Iniciando descubrimiento de herramientas MCP...")
        
        # Descubrir desde repositorios de GitHub
        github_tools = self.discover_github_mcp_tools()
        
        # Verificar herramientas instaladas
        installed_tools = self.check_installed_tools()
        
        # Crear objetos MCPTool
        discovered_tools = {}
        
        for tool_info in github_tools:
            tool = MCPTool(
                name=tool_info['name'],
                description=tool_info['description'],
                category=tool_info['category'],
                available=tool_info['name'] in installed_tools,
                requires_api_key=tool_info['requires_api_key'],
                parameters={},
                metadata=tool_info.get('metadata', {}),
                install_command=tool_info.get('install_command'),
                github_url=tool_info.get('github_url'),
                version=None
            )
            discovered_tools[tool_info['name']] = tool
        
        # Agregar herramientas básicas conocidas
        basic_tools = self._get_basic_mcp_tools()
        discovered_tools.update(basic_tools)
        
        self._tools = discovered_tools
        # Seleccionar automáticamente todas las herramientas disponibles y gratuitas
        self._selected_tools = [name for name, tool in self._tools.items() if tool.available and not tool.requires_api_key]
        self._save_cache()
        
        self.logger.info(f"✅ Descubrimiento completado: {len(self._tools)} herramientas MCP encontradas")
        return self._tools

    def _get_basic_mcp_tools(self) -> Dict[str, MCPTool]:
        """Retorna herramientas MCP básicas conocidas"""
        return {
            "filesystem": MCPTool(
                name="filesystem",
                description="Acceso al sistema de archivos",
                category="filesystem",
                available=True,
                requires_api_key=False,
                parameters={},
                install_command="Built-in MCP tool"
            ),
            "stdio": MCPTool(
                name="stdio",
                description="Entrada/salida estándar",
                category="io",
                available=True,
                requires_api_key=False,
                parameters={},
                install_command="Built-in MCP tool"
            ),
            "memory": MCPTool(
                name="memory",
                description="Almacenamiento en memoria",
                category="storage",
                available=True,
                requires_api_key=False,
                parameters={},
                install_command="Built-in MCP tool"
            )
        }

    def install_tool(self, tool_name: str) -> bool:
        """Instala una herramienta MCP"""
        if tool_name not in self._tools:
            self.logger.error(f"Herramienta {tool_name} no encontrada")
            return False
        
        tool = self._tools[tool_name]
        if not tool.install_command:
            self.logger.error(f"No hay comando de instalación para {tool_name}")
            return False
        
        try:
            self.logger.info(f"Instalando {tool_name}...")
            result = subprocess.run(tool.install_command.split(), 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                tool.available = True
                self._save_cache()
                self.logger.info(f"✅ Herramienta {tool_name} instalada exitosamente")
                return True
            else:
                self.logger.error(f"❌ Error instalando {tool_name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error instalando {tool_name}: {e}")
            return False

    def list_tools(self) -> List[str]:
        """Lista todas las herramientas disponibles"""
        if not self._tools:
            self.discover_mcp_tools()
        return list(self._tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de una herramienta"""
        if tool_name not in self._tools:
            return None
        return asdict(self._tools[tool_name])

    def get_tools_summary(self) -> Dict[str, Any]:
        """Retorna un resumen de todas las herramientas"""
        if not self._tools:
            self.discover_mcp_tools()
            
        available_tools = {name: tool for name, tool in self._tools.items() if tool.available}
        
        return {
            "tools_enabled": len(available_tools) > 0,
            "total_available": len(available_tools),
            "total_discovered": len(self._tools),
            "active_tools": list(available_tools.keys()),
            "available_tools": {name: asdict(tool) for name, tool in available_tools.items()},
            "categories": self._get_categories_summary(),
            "repositories_scanned": len(self.known_mcp_repos)
        }

    def _get_categories_summary(self) -> Dict[str, int]:
        """Retorna un resumen por categorías"""
        categories = {}
        for tool in self._tools.values():
            categories[tool.category] = categories.get(tool.category, 0) + 1
        return categories

    def refresh_discovery(self) -> Dict[str, MCPTool]:
        """Refresca el descubrimiento de herramientas"""
        self.logger.info("🔄 Refrescando descubrimiento de herramientas...")
        return self.discover_mcp_tools()

    def get_free_tools(self) -> Dict[str, MCPTool]:
        """Retorna solo herramientas gratuitas (sin API key)"""
        return {
            name: tool for name, tool in self._tools.items() 
            if not tool.requires_api_key
        }

    def get_selected_tools(self) -> List[str]:
        return self._selected_tools

    def set_selected_tools(self, selected: List[str]):
        self._selected_tools = [s for s in selected if s in self._tools]
        self._save_cache()

    def get_active_tools(self) -> List[str]:
        """
        Devuelve todas las herramientas activas (seleccionadas y disponibles)
        """
        return [name for name in self._selected_tools if name in self._tools and self._tools[name].available]

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas detalladas del registro"""
        if not self._tools:
            self.discover_mcp_tools()
            
        stats = {
            "total_tools": len(self._tools),
            "available_tools": len([t for t in self._tools.values() if t.available]),
            "selected_tools": len(self._selected_tools),
            "free_tools": len([t for t in self._tools.values() if not t.requires_api_key]),
            "categories": self._get_categories_summary(),
            "repositories_scanned": len(self.known_mcp_repos),
            "top_categories": sorted(self._get_categories_summary().items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        return stats

# Ejemplo de uso
if __name__ == "__main__":
    registry = MCPRegistry()
    
    # Descubrir herramientas
    tools = registry.discover_mcp_tools()
    
    # Mostrar estadísticas
    stats = registry.get_stats()
    print(f"📊 Estadísticas MCP Registry:")
    print(f"   Total herramientas: {stats['total_tools']}")
    print(f"   Herramientas disponibles: {stats['available_tools']}")
    print(f"   Herramientas gratuitas: {stats['free_tools']}")
    print(f"   Repositorios escaneados: {stats['repositories_scanned']}")
    print(f"   Top categorías: {stats['top_categories']}")
    
    # Listar herramientas gratuitas
    free_tools = registry.get_free_tools()
    print(f"\n🆓 Herramientas gratuitas ({len(free_tools)}):")
    for name, tool in list(free_tools.items())[:10]:  # Mostrar solo las primeras 10
        status = "✅" if tool.available else "⏸️"
        print(f"  {status} {name} ({tool.category}): {tool.description}")
    
    if len(free_tools) > 10:
        print(f"   ... y {len(free_tools) - 10} más")