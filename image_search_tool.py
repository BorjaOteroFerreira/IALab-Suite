from typing import List
from pydantic import BaseModel, Field
import requests
from datetime import datetime, timezone, timedelta
import json
import re
from urllib.parse import quote, unquote
import time
import random

from .base_tool import BaseTool, ToolMetadata, ToolCategory


class ImageSearchResult(BaseModel):
    image_url: str
    title: str
    context_url: str
    thumbnail_url: str
    width: int = 0
    height: int = 0
    source_domain: str = None


class ImageSearchToolInput(BaseModel):
    """Input for ImageSearchTool."""
    keyword: str = Field(..., description="The search keyword.")
    max_results: int = Field(5, description="The maximum number of results to return.")
    safe_search: bool = Field(True, description="Enable safe search filter")


class ImageSearchTool(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="image_search_tool",
            description="Busca imágenes usando DuckDuckGo (sin API key)",
            category=ToolCategory.MEDIA,
            requires_api_key=False,
            api_key_env_var=None
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "image_search_tool"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta búsqueda de imágenes"""
        max_results = kwargs.get('max_results', 4)
        safe_search = kwargs.get('safe_search', True)
        return self._search_images(query, max_results, safe_search)
    
    def _get_headers(self):
        """Genera headers realistas"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://duckduckgo.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def _search_images(self, keyword: str, max_results: int = 4, safe_search: bool = True):
        """
        Busca imágenes usando DuckDuckGo.

        Parameters:
            keyword (str): La palabra clave de búsqueda.
            max_results (int): El número máximo de resultados a devolver.
            safe_search (bool): Activar filtro de búsqueda segura.

        Returns:
            tuple: Una tupla con los resultados y las URLs de imágenes.
        """
        try:
            # Paso 1: Obtener token de DuckDuckGo
            session = requests.Session()
            session.headers.update(self._get_headers())
            
            # Obtener token inicial
            token_url = "https://duckduckgo.com/"
            response = session.get(token_url, timeout=10)
            
            # Extraer vqd token del HTML
            vqd_match = re.search(r'vqd="([^"]+)"', response.text)
            if not vqd_match:
                vqd_match = re.search(r'vqd=([^&]+)', response.text)
                
            if not vqd_match:
                raise Exception("No se pudo obtener el token de DuckDuckGo")
            
            vqd = vqd_match.group(1)
            
            # Paso 2: Realizar búsqueda de imágenes
            search_url = "https://duckduckgo.com/i.js"
            
            safe_param = "moderate" if safe_search else "off"
            
            params = {
                'l': 'es-es',
                'o': 'json',
                'q': keyword,
                'vqd': vqd,
                'f': ',,,,,',
                'p': safe_param,
                's': '0',  # offset
                'u': 'bing',
                'v7exp': 'a'
            }
            
            # Añadir delay
            time.sleep(random.uniform(1, 2))
            
            response = session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extraer resultados
            results = self._extract_image_results(data, max_results, keyword)
            
            if results:
                results_str = '\n'.join(str(result) for result in results)
                image_urls = [result.image_url for result in results]
                print(f"Encontradas {len(results)} imágenes para: {keyword}")
                return results_str, image_urls
            else:
                return '', []
                
        except requests.exceptions.RequestException as e:
            # Fallback a método alternativo
            print(f"Error con DuckDuckGo, intentando método alternativo: {e}")
            return self._search_images_fallback(keyword, max_results)
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return self._search_images_fallback(keyword, max_results)
    
    def _extract_image_results(self, data, max_results, keyword):
        """Extrae resultados de la respuesta JSON de DuckDuckGo"""
        results = []
        
        try:
            images = data.get('results', [])
            
            count = 0
            for img in images:
                if count >= max_results:
                    break
                
                try:
                    image_url = img.get('image', '')
                    title = img.get('title', f'Imagen de {keyword}')
                    thumbnail_url = img.get('thumbnail', '')
                    context_url = img.get('url', '')
                    width = img.get('width', 0)
                    height = img.get('height', 0)
                    source = img.get('source', '')
                    
                    # Limpiar URLs
                    if image_url and image_url.startswith('http'):
                        # Extraer dominio fuente
                        source_domain = ""
                        if context_url:
                            try:
                                from urllib.parse import urlparse
                                source_domain = urlparse(context_url).netloc
                            except:
                                source_domain = source
                        
                        results.append(ImageSearchResult(
                            image_url=image_url,
                            title=str(title).replace('|', '-').replace('||', '--')[:200],
                            context_url=context_url,
                            thumbnail_url=thumbnail_url,
                            width=int(width) if isinstance(width, (int, str)) and str(width).isdigit() else 0,
                            height=int(height) if isinstance(height, (int, str)) and str(height).isdigit() else 0,
                            source_domain=source_domain
                        ))
                        count += 1
                        
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Error procesando imagen: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extrayendo resultados: {e}")
            
        return results
    
    def _search_images_fallback(self, keyword: str, max_results: int = 4):
        """Método alternativo usando Unsplash API público"""
        try:
            # Unsplash tiene una API pública sin autenticación para búsquedas básicas
            url = "https://unsplash.com/napi/search/photos"
            
            headers = self._get_headers()
            headers['Accept'] = 'application/json'
            
            params = {
                'query': keyword,
                'per_page': min(max_results, 20),
                'page': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                photos = data.get('results', [])
                for photo in photos[:max_results]:
                    try:
                        image_url = photo.get('urls', {}).get('regular', '')
                        thumbnail_url = photo.get('urls', {}).get('thumb', '')
                        title = photo.get('alt_description') or photo.get('description') or f'Imagen de {keyword}'
                        context_url = photo.get('links', {}).get('html', '')
                        width = photo.get('width', 0)
                        height = photo.get('height', 0)
                        
                        if image_url:
                            results.append(ImageSearchResult(
                                image_url=image_url,
                                title=str(title).replace('|', '-').replace('||', '--')[:200],
                                context_url=context_url,
                                thumbnail_url=thumbnail_url,
                                width=width,
                                height=height,
                                source_domain="unsplash.com"
                            ))
                    except:
                        continue
                
                if results:
                    results_str = '\n'.join(str(result) for result in results)
                    image_urls = [result.image_url for result in results]
                    print(f"Encontradas {len(results)} imágenes (Unsplash) para: {keyword}")
                    return results_str, image_urls
                    
        except Exception as e:
            print(f"Error en método fallback: {e}")
            
        return '', []
    
    @staticmethod
    def run(keyword: str, max_results: int = 4, safe_search: bool = True) -> List[ImageSearchResult]:
        """
        Método estático legacy para compatibilidad con LangChain.
        """
        tool_instance = ImageSearchTool()
        return tool_instance._search_images(keyword, max_results, safe_search)