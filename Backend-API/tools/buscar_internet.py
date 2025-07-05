"""
Google Search España - Versión Ultra Robusta
Esta versión usa múltiples estrategias para garantizar que encuentra resultados
Compatible con BaseTool de IALab Suite
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urlparse, unquote
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from .base_tool import BaseTool, ToolMetadata, ToolCategory

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: str = ""
    
    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'content': self.content
        }

class BuscarInternet(BaseTool):
    """
    Herramienta de búsqueda universal en Internet para IALab Suite
    Versión ultra robusta con múltiples estrategias de extracción
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Búsqueda Universal en Internet",
            description="Busca información en internet usando múltiples estrategias robustas sin API keys",
            category=ToolCategory.SEARCH,
            version="2.0.0",
            author="IALab Suite",
            requires_api_key=False,
            api_key_env_var=None,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Consulta de búsqueda",
                    "required": True
                },
                "max_results": {
                    "type": "integer", 
                    "description": "Número máximo de resultados (default: 5)",
                    "required": False,
                    "default": 5
                },
                "include_images": {
                    "type": "boolean",
                    "description": "Incluir imágenes en resultados (default: False)", 
                    "required": False,
                    "default": False
                }
            }
        )

    @classmethod
    def get_tool_name(cls) -> str:
        return "Búsqueda Universal en Internet"
    
    def is_available(self) -> bool:
        """Verifica si la herramienta está disponible"""
        try:
            import requests
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            logger.error("Dependencias requeridas no disponibles: requests, beautifulsoup4")
            return False
    
    def execute(self, query: str, **kwargs) -> str:
        """Ejecuta búsqueda en internet con parámetros avanzados"""
        if not query or not query.strip():
            return "❌ Error: Query de búsqueda vacío"
        
        try:
            max_results = kwargs.get('max_results', 5)
            include_images = kwargs.get('include_images', False)
            
            # Validar parámetros
            if not isinstance(max_results, int) or max_results <= 0:
                max_results = 5
            if max_results > 20:  # Limitar para rendimiento
                max_results = 20
                
            logger.info(f"🔍 Ejecutando búsqueda: {query}")
            
            # Usar la clase robusta GoogleSearchRobust
            searcher = GoogleSearchRobust(max_results=max_results)
            results = searcher.search(query)
            
            if not results:
                return f"❌ No se encontraron resultados para: {query}"
            
            # Formatear resultados
            formatted_results = self._format_results(results, include_images)
            
            # Obtener contenido adicional de algunos resultados
            if len(results) > 0:
                try:
                    content = searcher.get_page_content(results[0].url)
                    if content and len(content.strip()) > 50:
                        formatted_results += f"\n\n📄 **Contenido destacado:**\n{content[:500]}..."
                except Exception as e:
                    logger.debug(f"Error obteniendo contenido adicional: {e}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error en execute: {e}")
            return f"❌ Error en la búsqueda: {str(e)}"
    
    def _format_results(self, results: List[SearchResult], include_images: bool = False) -> str:
        """Formatear resultados para output"""
        formatted = f"🔍 **Resultados de búsqueda ({len(results)} encontrados):**\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"**{i}. {result.title}**\n"
            formatted += f"🔗 {result.url}\n"
            if result.snippet:
                formatted += f"📄 {result.snippet}\n"
            formatted += "\n"
        
        if include_images:
            # Buscar imágenes en los resultados (funcionalidad básica)
            formatted += "\n🖼️ **Imágenes relacionadas:**\n"
            formatted += "_(Funcionalidad de imágenes en desarrollo)_\n"
        
        return formatted
    
    @staticmethod
    def scrape_url_content(url: str, max_chars: int = 2000, include_images: bool = False) -> Dict[str, Any]:
        """Scraping estático de contenido de URL (compatibilidad con tests)"""
        try:
            if not url or not url.strip():
                return {'error': 'URL vacía o inválida'}
            
            searcher = GoogleSearchRobust()
            content = searcher.get_page_content(url)
            
            result = {
                'success': True,
                'url': url,
                'title': 'Contenido extraído',
                'content': content[:max_chars] if content else '',
                'content_length': len(content) if content else 0,
                'images': [],
                'images_markdown': ''
            }
            
            if include_images:
                result['images_markdown'] = '_(Funcionalidad de imágenes en desarrollo)_'
            
            return result
            
        except Exception as e:
            logger.error(f"Error en scrape_url_content: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'content': '',
                'images': [],
                'images_markdown': ''
            }


class GoogleSearchRobust:
    """
    Versión ultra robusta de Google Search España
    Usa múltiples estrategias para garantizar extracción de resultados
    """
    
    def __init__(self, max_results: int = 5, timeout: int = 15):
        self.max_results = max_results
        self.timeout = timeout
        self.session = self._create_session()
        
    def _create_session(self):
        """Crear sesión optimizada para Google España"""
        session = requests.Session()
        
        # Headers que funcionan bien con Google
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        })
        
        return session
    
    def search(self, query: str) -> List[SearchResult]:
        """
        Realizar búsqueda en Google España con múltiples estrategias
        """
        logger.info(f"🔍 Iniciando búsqueda: {query}")
        
        # Estrategia 1: Búsqueda normal
        results = self._search_strategy_1(query)
        if results:
            logger.info(f"✅ Estrategia 1 exitosa: {len(results)} resultados")
            return results
        
        # Estrategia 2: Búsqueda con parámetros alternativos
        results = self._search_strategy_2(query)
        if results:
            logger.info(f"✅ Estrategia 2 exitosa: {len(results)} resultados")
            return results
        
        # Estrategia 3: Búsqueda con User-Agent móvil
        results = self._search_strategy_3(query)
        if results:
            logger.info(f"✅ Estrategia 3 exitosa: {len(results)} resultados")
            return results
        
        # Estrategia 4: Búsqueda en google.com con geolocalización
        results = self._search_strategy_4(query)
        if results:
            logger.info(f"✅ Estrategia 4 exitosa: {len(results)} resultados")
            return results
        
        logger.warning("❌ Todas las estrategias fallaron")
        return []
    
    def _search_strategy_1(self, query: str) -> List[SearchResult]:
        """Estrategia 1: Búsqueda normal en Google España"""
        try:
            params = {
                'q': query,
                'hl': 'es',
                'gl': 'ES',
                'num': 10,
                'ie': 'UTF-8',
                'oe': 'UTF-8',
            }
            
            response = self.session.get('https://www.google.es/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return self._extract_results_comprehensive(response.text, query)
            
        except Exception as e:
            logger.warning(f"Estrategia 1 falló: {e}")
            return []
    
    def _search_strategy_2(self, query: str) -> List[SearchResult]:
        """Estrategia 2: Búsqueda con parámetros alternativos"""
        try:
            # Cambiar User-Agent
            original_ua = self.session.headers.get('User-Agent')
            self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            params = {
                'q': query,
                'hl': 'es',
                'gl': 'ES',
                'num': 10,
                'safe': 'off',
                'filter': '0',
                'pws': '0',
                'ie': 'UTF-8',
                'oe': 'UTF-8',
                'lr': 'lang_es',
                'cr': 'countryES',
            }
            
            response = self.session.get('https://www.google.es/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Restaurar User-Agent original
            self.session.headers['User-Agent'] = original_ua
            
            return self._extract_results_comprehensive(response.text, query)
            
        except Exception as e:
            logger.warning(f"Estrategia 2 falló: {e}")
            return []
    
    def _search_strategy_3(self, query: str) -> List[SearchResult]:
        """Estrategia 3: Búsqueda con User-Agent móvil"""
        try:
            # Cambiar a User-Agent móvil
            original_ua = self.session.headers.get('User-Agent')
            self.session.headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            
            params = {
                'q': query,
                'hl': 'es',
                'gl': 'ES',
                'num': 10,
            }
            
            response = self.session.get('https://www.google.es/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Restaurar User-Agent original
            self.session.headers['User-Agent'] = original_ua
            
            return self._extract_results_comprehensive(response.text, query)
            
        except Exception as e:
            logger.warning(f"Estrategia 3 falló: {e}")
            return []
    
    def _search_strategy_4(self, query: str) -> List[SearchResult]:
        """Estrategia 4: Búsqueda en google.com con geolocalización"""
        try:
            params = {
                'q': query,
                'hl': 'es',
                'gl': 'ES',
                'num': 10,
                'ie': 'UTF-8',
                'oe': 'UTF-8',
            }
            
            response = self.session.get('https://www.google.com/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return self._extract_results_comprehensive(response.text, query)
            
        except Exception as e:
            logger.warning(f"Estrategia 4 falló: {e}")
            return []
    
    def _extract_results_comprehensive(self, html_content: str, query: str) -> List[SearchResult]:
        """
        Extracción comprehensiva de resultados usando múltiples métodos
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Método 1: Extracción por enlaces /url?q=
        results = self._extract_by_url_pattern(soup)
        if results:
            logger.info(f"✅ Método URL pattern: {len(results)} resultados")
            return results[:self.max_results]
        
        # Método 2: Extracción por estructura de divs
        results = self._extract_by_div_structure(soup)
        if results:
            logger.info(f"✅ Método div structure: {len(results)} resultados")
            return results[:self.max_results]
        
        # Método 3: Extracción por h3 y enlaces
        results = self._extract_by_h3_links(soup)
        if results:
            logger.info(f"✅ Método h3 links: {len(results)} resultados")
            return results[:self.max_results]
        
        # Método 4: Extracción genérica
        results = self._extract_generic(soup)
        if results:
            logger.info(f"✅ Método genérico: {len(results)} resultados")
            return results[:self.max_results]
        
        logger.warning("❌ Todos los métodos de extracción fallaron")
        return []
    
    def _extract_by_url_pattern(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Método 1: Extraer por patrón /url?q="""
        results = []
        
        try:
            # Buscar todos los enlaces con /url?q=
            links = soup.find_all('a', href=lambda href: href and '/url?q=' in href)
            
            for link in links:
                href = link.get('href', '')
                if '/url?q=' not in href:
                    continue
                
                # Extraer URL real
                try:
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = unquote(actual_url)
                    
                    if not self._is_valid_url(actual_url):
                        continue
                    
                    # Buscar título (h3 cercano)
                    title = ""
                    h3 = link.find('h3')
                    if not h3:
                        # Buscar h3 en el padre
                        parent = link.parent
                        for _ in range(3):
                            if parent:
                                h3 = parent.find('h3')
                                if h3:
                                    break
                                parent = parent.parent
                    
                    if h3:
                        title = h3.get_text(strip=True)
                    else:
                        title = link.get_text(strip=True)
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Buscar snippet cerca del enlace
                    snippet = self._find_snippet_near_element(link)
                    
                    results.append(SearchResult(
                        title=self._clean_text(title),
                        url=actual_url,
                        snippet=self._clean_text(snippet)
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error procesando enlace: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Error en extracción por URL pattern: {e}")
            return []
    
    def _extract_by_div_structure(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Método 2: Extraer por estructura de divs"""
        results = []
        
        try:
            # Selectores comunes de Google
            selectors = [
                'div.g',
                'div.tF2Cxc',
                'div.MjjYud',
                'div.hlcw0c',
                'div.yuRUbf',
                'div.kCrYT',
                'div.Gx5Zad',
                'div.kvH3mc',
                'div.BNeawe',
                'div.egMi0',
                'div.Z0LcW',
                'div.fP1Qef',
                'div.UiRzPc',
                'div.dXiKIc',
                'div.TzHB6b',
                'div.cxCtG',
                'div.N54PNb',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if not elements:
                    continue
                
                logger.debug(f"Probando selector: {selector} ({len(elements)} elementos)")
                
                for element in elements:
                    try:
                        # Buscar título
                        title = ""
                        h3 = element.find('h3')
                        if h3:
                            title = h3.get_text(strip=True)
                        
                        if not title or len(title) < 3:
                            continue
                        
                        # Buscar URL
                        url = ""
                        link = element.find('a', href=True)
                        if link:
                            href = link.get('href', '')
                            if '/url?q=' in href:
                                url = href.split('/url?q=')[1].split('&')[0]
                                url = unquote(url)
                            elif href.startswith('http'):
                                url = href
                        
                        if not self._is_valid_url(url):
                            continue
                        
                        # Buscar snippet
                        snippet = self._find_snippet_in_element(element)
                        
                        results.append(SearchResult(
                            title=self._clean_text(title),
                            url=url,
                            snippet=self._clean_text(snippet)
                        ))
                        
                    except Exception as e:
                        logger.debug(f"Error procesando elemento: {e}")
                        continue
                
                if results:
                    logger.info(f"Selector exitoso: {selector}")
                    break
            
            return results
            
        except Exception as e:
            logger.warning(f"Error en extracción por div structure: {e}")
            return []
    
    def _extract_by_h3_links(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Método 3: Extraer por h3 y enlaces"""
        results = []
        
        try:
            # Buscar todos los h3
            h3_elements = soup.find_all('h3')
            
            for h3 in h3_elements:
                try:
                    title = h3.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue
                    
                    # Buscar enlace asociado
                    url = ""
                    
                    # Método 1: h3 dentro de un enlace
                    parent_link = h3.find_parent('a')
                    if parent_link and parent_link.get('href'):
                        href = parent_link.get('href')
                        if '/url?q=' in href:
                            url = href.split('/url?q=')[1].split('&')[0]
                            url = unquote(url)
                        elif href.startswith('http'):
                            url = href
                    
                    # Método 2: Buscar enlace cercano
                    if not url:
                        parent = h3.parent
                        for _ in range(3):
                            if parent:
                                link = parent.find('a', href=True)
                                if link:
                                    href = link.get('href')
                                    if '/url?q=' in href:
                                        url = href.split('/url?q=')[1].split('&')[0]
                                        url = unquote(url)
                                        break
                                    elif href.startswith('http'):
                                        url = href
                                        break
                                parent = parent.parent
                    
                    if not self._is_valid_url(url):
                        continue
                    
                    # Buscar snippet cerca del h3
                    snippet = self._find_snippet_near_element(h3)
                    
                    results.append(SearchResult(
                        title=self._clean_text(title),
                        url=url,
                        snippet=self._clean_text(snippet)
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error procesando h3: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Error en extracción por h3 links: {e}")
            return []
    
    def _extract_generic(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Método 4: Extracción genérica como último recurso"""
        results = []
        
        try:
            # Buscar cualquier enlace que parezca un resultado
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                try:
                    href = link.get('href', '')
                    
                    # Filtrar enlaces de Google internos
                    if any(skip in href for skip in [
                        'google.', 'youtube.com/googleads', 'support.google',
                        'accounts.google', 'policies.google', 'webcache',
                        'javascript:', 'mailto:', '#', 'maps.google'
                    ]):
                        continue
                    
                    # Procesar URL
                    url = ""
                    if '/url?q=' in href:
                        url = href.split('/url?q=')[1].split('&')[0]
                        url = unquote(url)
                    elif href.startswith('http'):
                        url = href
                    
                    if not self._is_valid_url(url):
                        continue
                    
                    # Obtener título del texto del enlace o elementos cercanos
                    title = link.get_text(strip=True)
                    if not title or len(title) < 3:
                        # Buscar en elementos padre
                        parent = link.parent
                        for _ in range(2):
                            if parent:
                                title = parent.get_text(strip=True)
                                if title and len(title) > 3:
                                    break
                                parent = parent.parent
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Buscar snippet
                    snippet = self._find_snippet_near_element(link)
                    
                    results.append(SearchResult(
                        title=self._clean_text(title),
                        url=url,
                        snippet=self._clean_text(snippet)
                    ))
                    
                    if len(results) >= self.max_results:
                        break
                    
                except Exception as e:
                    logger.debug(f"Error en extracción genérica: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Error en extracción genérica: {e}")
            return []
    
    def _find_snippet_near_element(self, element) -> str:
        """Buscar snippet cerca de un elemento"""
        snippet = ""
        
        try:
            # Método 1: Buscar en el mismo elemento
            snippet = element.get_text(strip=True)
            if len(snippet) > 50:
                return snippet
            
            # Método 2: Buscar en elementos hermanos
            parent = element.parent
            if parent:
                for sibling in parent.find_all(['span', 'div', 'p']):
                    text = sibling.get_text(strip=True)
                    if len(text) > 30 and text != snippet:
                        snippet = text
                        break
            
            # Método 3: Buscar en elementos padre
            current = element.parent
            for _ in range(3):
                if current:
                    text = current.get_text(strip=True)
                    if len(text) > 30 and text != snippet:
                        snippet = text
                        break
                    current = current.parent
            
        except Exception as e:
            logger.debug(f"Error buscando snippet: {e}")
        
        return snippet
    
    def _find_snippet_in_element(self, element) -> str:
        """Buscar snippet dentro de un elemento"""
        snippet = ""
        
        try:
            # Buscar spans o divs que contengan texto descriptivo
            for tag in ['span', 'div', 'p']:
                snippets = element.find_all(tag)
                for s in snippets:
                    text = s.get_text(strip=True)
                    if len(text) > 30:
                        snippet = text
                        break
                if snippet:
                    break
            
            # Si no encontramos snippet específico, usar todo el texto
            if not snippet:
                snippet = element.get_text(strip=True)
            
        except Exception as e:
            logger.debug(f"Error buscando snippet en elemento: {e}")
        
        return snippet
    
    def _is_valid_url(self, url: str) -> bool:
        """Verificar si una URL es válida"""
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            
            # Debe tener esquema y netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Filtrar URLs de Google internas
            if any(domain in parsed.netloc.lower() for domain in [
                'google.', 'gstatic.', 'googleusercontent.', 
                'googlesyndication.', 'googleadservices.'
            ]):
                return False
            
            # Filtrar URLs problemáticas
            if any(skip in url.lower() for skip in [
                'javascript:', 'mailto:', 'tel:', 'ftp:', 'file:',
                'webcache', 'translate.google'
            ]):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraído"""
        if not text:
            return ""
        
        # Eliminar espacios extra y caracteres problemáticos
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Limitar longitud
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text
    
    def get_page_content(self, url: str) -> str:
        """Obtener contenido de una página web"""
        try:
            logger.info(f"📄 Obteniendo contenido de: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Eliminar scripts y estilos
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extraer texto principal
            content = soup.get_text()
            content = self._clean_text(content)
            
            # Limitar contenido
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            logger.info(f"✅ Contenido obtenido: {len(content)} caracteres")
            return content
            
        except Exception as e:
            logger.warning(f"❌ Error obteniendo contenido de {url}: {e}")
            return ""

    def get_usage_info(self) -> Dict[str, Any]:
        """Retorna información detallada de uso de la herramienta"""
        base_info = super().get_usage_info()
        base_info.update({
            "examples": [
                {
                    "query": "noticias España 2025",
                    "description": "Buscar noticias recientes sobre España"
                },
                {
                    "query": "desarrollo web Python",
                    "max_results": 10,
                    "description": "Buscar información sobre desarrollo web con Python"
                },
                {
                    "query": "inteligencia artificial",
                    "include_images": True,
                    "description": "Buscar sobre IA incluyendo imágenes"
                }
            ],
            "tips": [
                "Usa términos específicos para mejores resultados",
                "max_results se limita automáticamente a 20 para rendimiento",
                "La herramienta usa múltiples estrategias de búsqueda para mayor robustez",
                "Incluye contenido destacado del primer resultado cuando es posible"
            ]
        })
        return base_info
    
def buscar_en_google(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Función principal para buscar en Google España
    Mantiene compatibilidad con código legacy
    """
    try:
        logger.info(f"🚀 Iniciando búsqueda en Google España: {query}")
        
        # Usar la herramienta BuscarInternet para consistencia
        tool = BuscarInternet()
        if not tool.is_available():
            return {
                "success": False,
                "error": "Herramienta no disponible - dependencias faltantes",
                "query": query,
                "results": []
            }
        
        # Ejecutar búsqueda usando la herramienta
        result_text = tool.execute(query, max_results=max_results)
        
        # Para mantener compatibilidad, también usar GoogleSearchRobust directamente
        searcher = GoogleSearchRobust(max_results=max_results)
        results = searcher.search(query)
        
        if not results:
            return {
                "success": False,
                "error": "No se encontraron resultados",
                "query": query,
                "results": []
            }
        
        # Obtener contenido de los primeros resultados
        for i, result in enumerate(results[:2]):  # Solo los primeros 2 para no sobrecargar
            try:
                content = searcher.get_page_content(result.url)
                result.content = content
                time.sleep(random.uniform(1, 2))  # Pausa entre solicitudes
            except Exception as e:
                logger.warning(f"Error obteniendo contenido de {result.url}: {e}")
        
        response = {
            "success": True,
            "query": query,
            "results": [result.to_dict() for result in results],
            "total_results": len(results),
            "formatted_text": result_text
        }
        
        logger.info(f"✅ Búsqueda completada exitosamente: {len(results)} resultados")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": []
        }

# Función de conveniencia para compatibilidad
def buscar_internet(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Alias para buscar_en_google - mantiene compatibilidad"""
    return buscar_en_google(query, max_results)

if __name__ == "__main__":
    # Prueba del sistema
    query = "noticias España 2025"
    
    print("🧪 Iniciando pruebas de BuscarInternet...")
    print("="*60)
    
    # Probar con la clase BuscarInternet (compatible con BaseTool)
    print("1. Probando herramienta BuscarInternet (BaseTool)...")
    tool = BuscarInternet()
    
    # Verificar disponibilidad
    if tool.is_available():
        print("✅ Herramienta disponible")
        
        # Mostrar metadatos
        metadata = tool.metadata
        print(f"📋 Nombre: {metadata.name}")
        print(f"📋 Versión: {metadata.version}")
        print(f"📋 Categoría: {metadata.category.value}")
        
        # Ejecutar búsqueda
        result = tool.execute(query, max_results=3)
        print("✅ Resultado de BuscarInternet:")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # Mostrar info de uso
        usage_info = tool.get_usage_info()
        print(f"\n📖 Ejemplos disponibles: {len(usage_info.get('examples', []))}")
        
    else:
        print("❌ Herramienta no disponible")
    
    print("\n" + "="*60 + "\n")
    
    # Probar con la función directa (compatibilidad legacy)
    print("2. Probando función directa buscar_en_google...")
    results = buscar_en_google(query, max_results=3)
    if results["success"]:
        print(f"✅ Búsqueda directa exitosa: {results['total_results']} resultados")
        for i, result in enumerate(results["results"], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
            if result.get('content'):
                print(f"   Contenido: {len(result['content'])} caracteres")
    else:
        print(f"❌ Error: {results['error']}")
    
    print("\n" + "="*60)
    print("🎯 Pruebas completadas")