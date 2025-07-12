"""
Herramienta de búsqueda en internet usando Google Custom Search API gratuita.
Compatible con el sistema base_tool de IALab Suite.
"""
import os
import re
import requests
import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Importaciones para extracción de contenido (igual que search_tools.py)
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

from .base_tool import BaseTool, ToolMetadata, ToolCategory, ToolExecutionResult

# Cargar variables de entorno
load_dotenv()

class GoogleSearchTool(BaseTool):
    """
    Herramienta para búsquedas en internet usando Google Custom Search API.
    
    Requiere:
    - CUSTOM_SEARCH_API_KEY: API key de Google Cloud Console
    - GOOGLE_CSE_ID: ID del Custom Search Engine
    """
    
    def __init__(self):
        self.api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        self.base_url = "https://customsearch.googleapis.com/customsearch/v1"
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Google Custom Search",
            description="Busca información en internet usando Google Custom Search API (requiere API key y CSE ID)",
            category=ToolCategory.SEARCH,
            requires_api_key=True,
            api_key_env_var="CUSTOM_SEARCH_API_KEY",
            usage_example={
                "búsqueda_simple": '{"tool": "google_custom_search", "query": "historia de la inteligencia artificial"}',
                "con_opciones": '{"tool": "google_custom_search", "query": "machine learning", "num_results": 3, "language": "es"}',
                "formatos_soportados": [
                    'query: texto de búsqueda (string)',
                    'num_results: número de resultados (int, opcional)',
                    'language: idioma (string, opcional)',
                    'date_restrict: filtro temporal (string, opcional)'
                ]
            }
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Google Custom Search API"
    
    def validate_api_key(self) -> bool:
        """Valida que tanto la API key como el CSE ID estén configurados"""
        return bool(self.api_key and self.cse_id)
    
    def validate_cse_id(self, cse_id: str) -> bool:
        """Valida el formato del CSE ID"""
        # CSE ID debe ser alfanumérico con algunos caracteres especiales permitidos
        # Formato típico: caracteres alfanuméricos, guiones, dos puntos
        pattern = r'^[a-zA-Z0-9_\-:\.]+$'
        return bool(re.match(pattern, cse_id)) and len(cse_id) > 10
    
    def execute(self, query: str, **kwargs) -> ToolExecutionResult:
        """
        Ejecuta una búsqueda en Google y devuelve resultados optimizados con contenido extraído.
        
        Args:
            query (str): Texto a buscar
            **kwargs: Parámetros opcionales (num_results, language, safe_search)
            
        Returns:
            ToolExecutionResult: Resultado con contenido formateado y extraído de páginas web
        """
        # Delegar al método optimizado que extrae contenido real
        return self.search_with_formatting(query, **kwargs)
    
    def _search_google(self, query: str, num_results: int = 5, language: str = 'es', safe_search: str = 'off', date_restrict: str = 'm1', sort_by_date: bool = True) -> Optional[Dict]:
        """
        Realiza la búsqueda usando Google Custom Search API con filtros de fecha.
        
        Args:
            query (str): Consulta de búsqueda
            num_results (int): Número de resultados
            language (str): Idioma de los resultados
            safe_search (str): Nivel de filtro de contenido
            date_restrict (str): Filtro temporal (d1, w1, m1, y1)
            sort_by_date (bool): Ordenar por fecha más reciente
            
        Returns:
            Dict: Respuesta de la API de Google o None si hay error
        """
        try:
            # Limpiar y preparar la consulta
            query = query.strip()
            if not query:
                return None
            
            # Mapear valores de safe_search a los válidos de Google
            safe_values = {
                'off': 'off',
                'active': 'active',
                'high': 'active',
                'medium': 'off',
                'low': 'off'
            }
            safe_search = safe_values.get(safe_search.lower(), 'off')
            
            # Parámetros básicos obligatorios
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': num_results,
                'start': 1  # Siempre empezar desde el primer resultado
            }
            
            # Agregar parámetros opcionales
            if language and language.lower() != 'all':
                # Usar gl (geolocation) en lugar de lr para mejor compatibilidad
                lang_map = {
                    'es': 'es',
                    'en': 'us',
                    'fr': 'fr',
                    'de': 'de',
                    'it': 'it',
                    'pt': 'br'
                }
                gl_code = lang_map.get(language.lower(), language.lower())
                params['gl'] = gl_code
                
                # También agregar lr si es necesario
                if language.lower() in ['es', 'en', 'fr', 'de', 'it', 'pt']:
                    params['lr'] = f'lang_{language.lower()}'
            
            if safe_search != 'off':
                params['safe'] = safe_search
            
            # Agregar filtros de fecha para resultados recientes
            if date_restrict and date_restrict != 'all':
                # Validar formato de date_restrict
                valid_periods = {
                    'd1': 'd1',   # último día
                    'w1': 'w1',   # última semana  
                    'm1': 'm1',   # último mes
                    'm3': 'm3',   # últimos 3 meses
                    'y1': 'y1'    # último año
                }
                if date_restrict in valid_periods:
                    params['dateRestrict'] = date_restrict
            
            # Ordenar por fecha si se solicita
            if sort_by_date:
                params['sort'] = 'date'
            
            # Agregar headers para mejor identificación
            headers = {
                'User-Agent': 'IALab Suite Google Search Tool/1.0',
                'Accept': 'application/json'
            }
            
            # Realizar solicitud con mejor manejo de errores
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=headers,
                timeout=15
            )
            
            # Log de debug (opcional)
            print(f"🔍 Búsqueda: {query}")
            print(f"📡 URL: {response.url}")
            print(f"📊 Status: {response.status_code}")
            
            response.raise_for_status()
            
            json_response = response.json()
            
            # Validar que la respuesta tenga el formato esperado
            if 'items' not in json_response and 'searchInformation' not in json_response:
                print("⚠️  Respuesta inesperada de Google API")
                print(f"📋 Contenido: {json_response}")
                return None
            
            return json_response
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP {e.response.status_code}"
            
            # Manejo específico de errores HTTP
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_details = error_data['error']
                        error_msg += f": {error_details.get('message', 'Solicitud malformada')}"
                        
                        # Errores específicos
                        if 'errors' in error_details:
                            for error in error_details['errors']:
                                reason = error.get('reason', '')
                                if reason == 'invalid':
                                    error_msg += "\n🔧 Posibles soluciones:"
                                    error_msg += "\n   • Verifica que GOOGLE_CSE_ID sea correcto"
                                    error_msg += "\n   • Asegúrate de que el CSE esté configurado para 'Buscar en toda la web'"
                                    error_msg += "\n   • Verifica que el CSE tenga el estado 'Público'"
                                elif reason == 'keyInvalid':
                                    error_msg += "\n🔑 API Key inválida o expirada"
                                elif reason == 'dailyLimitExceeded':
                                    error_msg += "\n⏰ Límite diario excedido (100 búsquedas/día)"
                except:
                    error_msg += "\n❌ Error al procesar detalles del error"
            
            elif e.response.status_code == 403:
                error_msg += " - Acceso denegado"
                error_msg += "\n🔧 Posibles soluciones:"
                error_msg += "\n   • Verifica que Custom Search API esté habilitada"
                error_msg += "\n   • Verifica que la API Key tenga permisos"
                error_msg += "\n   • Revisa las restricciones de la API Key"
            
            elif e.response.status_code == 429:
                error_msg += " - Demasiadas solicitudes"
                error_msg += "\n⏰ Espera un momento antes de intentar de nuevo"
            
            print(error_msg)
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al procesar respuesta JSON: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None
    
    def _filter_raw_results(self, raw_results: Dict) -> Dict:
        """
        Filtra los resultados de Google API para conservar solo los datos esenciales.
        Elimina metadatos innecesarios para reducir el uso de tokens.
        
        Args:
            raw_results (Dict): Respuesta completa de Google API
            
        Returns:
            Dict: Resultados filtrados con solo los datos necesarios
        """
        if not raw_results or 'items' not in raw_results:
            return {'items': []}
        
        filtered_items = []
        for item in raw_results['items'][:5]:  # Máximo 5 resultados
            # Extraer solo campos esenciales
            filtered_item = {
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayLink': item.get('displayLink', ''),
                # Solo metadatos de imagen relevantes del pagemap
                'pagemap': self._extract_essential_pagemap(item.get('pagemap', {}))
            }
            filtered_items.append(filtered_item)
        
        return {
            'items': filtered_items,
            'searchInformation': {
                'totalResults': raw_results.get('searchInformation', {}).get('totalResults', '0')
            }
        }
    
    def _extract_essential_pagemap(self, pagemap: Dict) -> Dict:
        """
        Extrae solo los metadatos esenciales del pagemap para imágenes.
        
        Args:
            pagemap (Dict): Pagemap completo de Google
            
        Returns:
            Dict: Solo metadatos de imagen relevantes
        """
        essential = {}
        
        # Solo extraer og:image y twitter:image de metatags
        if 'metatags' in pagemap and pagemap['metatags']:
            meta = pagemap['metatags'][0]  # Solo el primer metatag
            for key in ['og:image', 'twitter:image']:
                if key in meta:
                    if 'metatags' not in essential:
                        essential['metatags'] = [{}]
                    essential['metatags'][0][key] = meta[key]
                    break  # Solo una imagen
        
        # CSE image como fallback
        if 'cse_image' in pagemap and pagemap['cse_image']:
            essential['cse_image'] = [{'src': pagemap['cse_image'][0].get('src', '')}]
        
        return essential

    def format_results(self, raw_results: Dict) -> List[Dict[str, Any]]:
        """
        Formatea los resultados siguiendo el formato exacto de search_tools.py.
        Filtra el contenido para usar el mínimo contexto posible.
        
        Args:
            raw_results (Dict): Resultados crudos de la API
            
        Returns:
            List[Dict]: Lista de resultados formateados
        """
        # Primero filtrar para reducir contexto
        filtered_results = self._filter_raw_results(raw_results)
        formatted_results = []
        
        if not filtered_results or 'items' not in filtered_results:
            return formatted_results
        
        for item in filtered_results['items']:
            title = item.get('title', '').replace('|', '-').replace('||', '--')
            link = item.get('link', '')
            snippet = item.get('snippet', '').replace('|', '-').replace('||', '--')
            
            if not link:
                continue
            
            # Extraer contenido con el mismo formato que search_tools
            content = self._extract_content_with_images(link)
            
            result = {
                'title': title,
                'link': link,
                'snippet': snippet,
                'content': content
            }
            
            formatted_results.append(result)
        
        return formatted_results
    
    def search_with_formatting(self, query: str, **kwargs) -> ToolExecutionResult:
        """
        Ejecuta búsqueda, visita enlaces y devuelve resultados con contenido extraído.
        Optimizado para mínimo contexto.
        
        Args:
            query (str): Consulta de búsqueda
            **kwargs: Parámetros adicionales
            
        Returns:
            ToolExecutionResult: Resultado con datos formateados como string y contenido real extraído
        """
        try:
            # Validar configuración
            if not self.validate_api_key():
                return ToolExecutionResult(
                    success=False,
                    error="Configuración incompleta. Se requieren CUSTOM_SEARCH_API_KEY y GOOGLE_CSE_ID"
                )
            
            # Validar formato del CSE ID
            if not self.validate_cse_id(self.cse_id):
                return ToolExecutionResult(
                    success=False,
                    error="GOOGLE_CSE_ID tiene formato inválido. Debe ser el ID completo del Custom Search Engine"
                )
            
            # Parámetros de búsqueda - forzar máximo 5 resultados
            num_results = min(kwargs.get('num_results', 5), 5)
            language = kwargs.get('language', 'es')
            safe_search = kwargs.get('safe_search', 'off')
            date_restrict = kwargs.get('date_restrict', 'm1')  # Por defecto último mes
            sort_by_date = kwargs.get('sort_by_date', True)    # Por defecto ordenar por fecha
            
            # Paso 1: Realizar búsqueda en Google API
            print(f"🔍 Paso 1: Buscando '{query}' en Google API...")
            print(f"📅 Filtro temporal: {date_restrict} (ordenar por fecha: {sort_by_date})")
            raw_results = self._search_google(query, num_results, language, safe_search, date_restrict, sort_by_date)
            
            if not raw_results:
                return ToolExecutionResult(
                    success=False,
                    error="No se encontraron resultados para la búsqueda"
                )
            
            # Paso 2: Filtrar resultados básicos de Google
            print("📊 Paso 2: Filtrando resultados de Google...")
            filtered_results = self._filter_raw_results(raw_results)
            
            # Paso 3: Visitar enlaces y extraer contenido real
            print("🌐 Paso 3: Visitando enlaces y extrayendo contenido...")
            formatted_data = self.format_results(raw_results)  # Usar raw_results para format_results
            
            # Paso 4: Convertir a formato string final (exactamente como search_tools.py)
            print("📄 Paso 4: Generando formato final...")
            string_results = []
            for item in formatted_data:
                string_results.append('\n'.join([
                    f"Title: {item['title']}",
                    f"Link: {item['link']}",
                    f"Snippet: {item['snippet']}",
                    f"Content: {item['content']}",
                    "\n-----------------"
                ]))
            
            final_string = '\n'.join(string_results)
            
            print(f"✅ Proceso completado: {len(formatted_data)} resultados con contenido extraído")
            
            return ToolExecutionResult(
                success=True,
                data=final_string,
                metadata={
                    "query": query,
                    "num_results": len(formatted_data),
                    "language": language,
                    "total_results": filtered_results.get('searchInformation', {}).get('totalResults', '0')
                }
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error en la búsqueda: {str(e)}"
            )
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Obtiene sugerencias de búsqueda (implementación básica).
        
        Args:
            query (str): Consulta base
            
        Returns:
            List[str]: Lista de sugerencias
        """
        # Sugerencias básicas basadas en palabras clave comunes
        suggestions = [
            f"{query} definición",
            f"{query} ejemplos", 
            f"{query} tutorial",
            f"qué es {query}",
            f"{query} ventajas y desventajas"
        ]
        
        return suggestions[:3]  # Limitar a 3 sugerencias
    
    def _extract_content_with_images(self, url: str) -> str:
        """
        Extrae contenido siguiendo exactamente la misma lógica que search_tools.py.
        
        Args:
            url (str): URL a procesar
            
        Returns:
            str: Contenido formateado como en search_tools
        """
        # No incluir URLs de más de 150 caracteres
        if len(url) > 150:
            return "Content extraction failed."

        try:
            from requests_html import HTMLSession
            from urllib.parse import urlparse
            import requests
            import json
            
            session = HTMLSession()
            resp = session.get(url)
            resp.raise_for_status()

            # texto dentro de <article>, fallback a <p> y <h1-3>
            elems = resp.html.xpath('//article//p | //article//h1 | //article//h2 | //article//h3')
            if not elems:
                elems = resp.html.xpath('//p | //h1 | //h2 | //h3')
            content = '\n'.join([e.text.strip() for e in elems if e.text and e.text.strip()])

            # Imágenes relevantes dentro de <article>
            imgs = resp.html.xpath('//article//img')
            srcs = set()
            for img in imgs:
                src = img.attrs.get('data-src') or img.attrs.get('src')
                if not src or src.startswith('data:'):
                    continue
                if any(x in src.lower() for x in ['ads.', 'tracker.', 'pixel.', 'gettyimages']):
                    continue
                # Formato: ![imagen dominio_url](url_imagen)
                domain = urlparse(url).netloc
                src = requests.compat.urljoin(url, src)
                if 'gettyimages' not in src.lower():
                    srcs.add(f"![{domain}]({src})")

            # Fallback a og:image si no hay imgs
            if not srcs:
                metas = resp.html.xpath('//meta[@property="og:image"]')
                for m in metas:
                    c = m.attrs.get('content')
                    if c and 'gettyimages' not in c.lower():
                        srcs.add(c)

            # Imágenes de perfil de LinkedIn, Facebook e Instagram
            perfil = []
            if 'linkedin.com/in/' in url:
                nodes = resp.html.xpath('//img[contains(@class,"profile-photo") or contains(@class,"pv-top-card__photo")]')
                for n in nodes:
                    src = n.attrs.get('src')
                    if src and 'gettyimages' not in src.lower():
                        perfil.append(requests.compat.urljoin(url, src))
            elif 'facebook.com/' in url and ('/profile.php' in url or url.rstrip('/').count('/') == 3):
                metas = resp.html.xpath('//meta[@property="og:image"]')
                for m in metas:
                    content = m.attrs.get('content')
                    if content and 'gettyimages' not in content.lower():
                        perfil.append(content)
            elif 'instagram.com/' in url:
                scripts = resp.html.xpath('//script[@type="application/ld+json"]')
                for s in scripts:
                    try:
                        ld = json.loads(s.text)
                        if 'image' in ld and 'gettyimages' not in ld['image'].lower():
                            perfil.append(ld['image'])
                    except:
                        continue

            
            # Filtrar Getty Images una vez más antes del resultado final
            final_filtered = []
            sources_to_check = perfil[:1] if perfil else list(srcs)[:2]
            
            for img_src in sources_to_check:
                # Verificar que no contenga gettyimages
                if 'gettyimages' not in img_src.lower():
                    final_filtered.append(img_src)
            
            final = final_filtered

            # Formatear Markdown 
            md_imgs = ' '.join(f'![{urlparse(url).netloc}]({i})' for i in final)
            resumen = self._extract_relevant_content_from_text(content)

            return f"Imágenes: {md_imgs}\nResumen: {resumen}" if content or md_imgs else "Content extraction failed."

        except requests.exceptions.RequestException as e:
            print(f"Error extracting content: {e}")
            return "Content extraction failed."
    
    def _extract_relevant_content_from_text(self, text: str) -> str:
        """
        Extrae contenido relevante usando la misma lógica que search_tools.py.
        """
        try:
            parser = HtmlParser.from_string(text, Tokenizer('spanish'))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 1)  # Una sola frase
            return str(summary[0]) if summary else ""
        except Exception as e:
            print(f"Error extracting content: {e}")
            return ""
    
    def _extract_images_from_pagemap(self, item: Dict) -> str:
        """
        Extrae la imagen más relevante del pagemap de Google.
        Optimizado para mínimo contexto.
        
        Args:
            item (Dict): Item de resultado de Google
            
        Returns:
            str: Una sola imagen en formato Markdown
        """
        if 'pagemap' not in item:
            return ""
        
        pagemap = item['pagemap']
        domain = item.get('displayLink', 'imagen')
        
        # Prioridad: og:image > cse_image > twitter:image
        # Solo extraer UNA imagen, la más relevante
        
        # 1. Buscar og:image (más confiable)
        if 'metatags' in pagemap:
            for meta in pagemap['metatags'][:1]:  # Solo primer metatag
                for key in ['og:image', 'twitter:image']:
                    if key in meta:
                        src = meta[key]
                        if src and 'gettyimages' not in src.lower():
                            return f"![{domain}]({src})"
        
        # 2. Fallback a cse_image
        if 'cse_image' in pagemap and pagemap['cse_image']:
            src = pagemap['cse_image'][0].get('src', '')
            if src and 'gettyimages' not in src.lower():
                return f"![{domain}]({src})"
        
        return ""
    
    def diagnosticar_configuracion(self) -> Dict[str, Any]:
        """
        Diagnostica la configuración actual y proporciona información de debug.
        
        Returns:
            Dict: Información de diagnóstico
        """
        diagnostico = {
            "api_key_configurada": bool(self.api_key),
            "api_key_valida": False,
            "cse_id_configurado": bool(self.cse_id),
            "cse_id_valido": False,
            "cse_id_formato_correcto": False,
            "api_habilitada": False,
            "recomendaciones": []
        }
        
        # Verificar API Key
        if not self.api_key:
            diagnostico["recomendaciones"].append("❌ CUSTOM_SEARCH_API_KEY no está configurada")
        elif self.api_key == "tu_google_api_key_aqui":
            diagnostico["recomendaciones"].append("❌ CUSTOM_SEARCH_API_KEY tiene valor placeholder")
        else:
            diagnostico["api_key_valida"] = True
            diagnostico["recomendaciones"].append("✅ CUSTOM_SEARCH_API_KEY configurada")
        
        # Verificar CSE ID
        if not self.cse_id:
            diagnostico["recomendaciones"].append("❌ GOOGLE_CSE_ID no está configurado")
        elif self.cse_id == "tu_custom_search_engine_id_aqui":
            diagnostico["recomendaciones"].append("❌ GOOGLE_CSE_ID tiene valor placeholder")
        else:
            diagnostico["cse_id_configurado"] = True
            
            # Verificar formato del CSE ID
            if self.validate_cse_id(self.cse_id):
                diagnostico["cse_id_formato_correcto"] = True
                diagnostico["recomendaciones"].append("✅ GOOGLE_CSE_ID configurado con formato válido")
            else:
                diagnostico["recomendaciones"].append("❌ GOOGLE_CSE_ID tiene formato inválido")
                diagnostico["recomendaciones"].append("💡 El CSE ID debe ser alfanumérico y tener más de 10 caracteres")
        
        # Hacer una prueba de conectividad básica si las configuraciones parecen válidas
        if diagnostico["api_key_valida"] and diagnostico["cse_id_formato_correcto"]:
            try:
                # Usar una búsqueda simple para probar
                params = {
                    'key': self.api_key,
                    'cx': self.cse_id,
                    'q': 'test',
                    'num': 1
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    diagnostico["api_habilitada"] = True
                    diagnostico["recomendaciones"].append("✅ API responde correctamente")
                else:
                    diagnostico["recomendaciones"].append(f"❌ API responde con código {response.status_code}")
                    
                    # Detalles específicos del error
                    if response.status_code == 400:
                        diagnostico["recomendaciones"].append("🔧 Solicitud malformada - revisa el CSE ID")
                    elif response.status_code == 403:
                        try:
                            error_data = response.json()
                            if 'error' in error_data:
                                reason = error_data['error'].get('errors', [{}])[0].get('reason', 'unknown')
                                if reason == 'keyInvalid':
                                    diagnostico["recomendaciones"].append("🔑 API Key inválida o expirada")
                                elif reason == 'customsearchNotEnabled':
                                    diagnostico["recomendaciones"].append("🔧 Custom Search API no habilitada")
                                else:
                                    diagnostico["recomendaciones"].append(f"📋 Razón: {reason}")
                        except:
                            pass
                    elif response.status_code == 429:
                        diagnostico["recomendaciones"].append("⏰ Límite de cuota excedido")
                        
            except Exception as e:
                diagnostico["recomendaciones"].append(f"❌ Error de conectividad: {str(e)}")
        
        return diagnostico
    
    def test_connection(self) -> bool:
        """
        Realiza una prueba básica de conexión.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            result = self.execute("test", num_results=1)
            return result.success
        except:
            return False
    
    @staticmethod
    def search_internet(query: str, num_results: int = 5, language: str = 'es', date_restrict: str = 'm1') -> str:
        """
        Método estático para búsqueda en internet compatible con search_tools.py.
        Optimizado para obtener resultados recientes por defecto.
        
        Args:
            query (str): Consulta de búsqueda
            num_results (int): Número de resultados (máximo 10)
            language (str): Idioma de los resultados
            date_restrict (str): Filtro temporal (d1=día, w1=semana, m1=mes, y1=año)
            
        Returns:
            str: Resultado de la búsqueda formateado como string
        """
        tool = GoogleSearchTool()
        
        # Verificar configuración
        if not tool.validate_api_key():
            return "Error: CUSTOM_SEARCH_API_KEY y GOOGLE_CSE_ID no están configuradas en las variables de entorno."
        
        result = tool.search_with_formatting(
            query, 
            num_results=num_results, 
            language=language,
            date_restrict=date_restrict,
            sort_by_date=True
        )
        
        if result.success:
            return result.data
        else:
            return f"Error en la búsqueda: {result.error}"
    
    @staticmethod
    def extract_content(url: str) -> str:
        """
        Método estático para extraer contenido compatible con search_tools.py.
        
        Args:
            url (str): URL a procesar
            
        Returns:
            str: Contenido extraído
        """
        tool = GoogleSearchTool()
        return tool._extract_content_with_images(url)


# Función de conveniencia para uso directo
def buscar_internet(query: str, num_results: int = 5, language: str = 'es', date_restrict: str = 'm1') -> str:
    """
    Función de conveniencia para búsquedas rápidas con resultados recientes.
    Devuelve el resultado en formato string compatible con search_tools.
    
    Args:
        query (str): Texto a buscar
        num_results (int): Número de resultados
        language (str): Idioma de los resultados
        date_restrict (str): Filtro temporal (d1=día, w1=semana, m1=mes, y1=año)
        
    Returns:
        str: Resultado de la búsqueda formateado como string
    """
    tool = GoogleSearchTool()
    result = tool.search_with_formatting(
        query, 
        num_results=num_results, 
        language=language,
        date_restrict=date_restrict,
        sort_by_date=True
    )
    
    if result.success:
        return result.data
    else:
        return f"Error en la búsqueda: {result.error}"


# Alias para compatibilidad
GoogleInternetSearch = GoogleSearchTool