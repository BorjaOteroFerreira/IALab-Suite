"""
Herramienta de búsqueda en internet usando Google Custom Search API gratuita.
Compatible con el sistema base_tool de IALab Suite.
"""
import os
import requests
import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from dotenv import load_dotenv

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
            name="Google Search",
            description="Busca información en internet usando Google Custom Search API gratuita (100 búsquedas/día)",
            category=ToolCategory.SEARCH,
            version="1.0.0",
            author="IALab Suite",
            requires_api_key=True,
            api_key_env_var="CUSTOM_SEARCH_API_KEY",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Texto a buscar en internet",
                    "required": True
                },
                "num_results": {
                    "type": "integer",
                    "description": "Número de resultados a devolver (máximo 10)",
                    "default": 5,
                    "min": 1,
                    "max": 10
                },
                "language": {
                    "type": "string",
                    "description": "Idioma de los resultados (es, en, fr, etc.)",
                    "default": "es"
                },
                "safe_search": {
                    "type": "string",
                    "description": "Nivel de filtro de contenido (off, active)",
                    "default": "off"
                }
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
        import re
        # Formato típico: caracteres alfanuméricos, guiones, dos puntos
        pattern = r'^[a-zA-Z0-9_\-:\.]+$'
        return bool(re.match(pattern, cse_id)) and len(cse_id) > 10
    
    def execute(self, query: str, **kwargs) -> ToolExecutionResult:
        """
        Ejecuta una búsqueda en Google.
        
        Args:
            query (str): Texto a buscar
            **kwargs: Parámetros opcionales (num_results, language, safe_search)
            
        Returns:
            ToolExecutionResult: Resultado de la búsqueda
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
            
            # Parámetros de búsqueda
            num_results = kwargs.get('num_results', 5)
            language = kwargs.get('language', 'es')
            safe_search = kwargs.get('safe_search', 'off')
            
            # Validar parámetros
            num_results = max(1, min(10, num_results))
            
            # Realizar búsqueda
            results = self._search_google(query, num_results, language, safe_search)
            
            if results:
                return ToolExecutionResult(
                    success=True,
                    data=results,
                    metadata={
                        "query": query,
                        "num_results": len(results.get('items', [])),
                        "language": language,
                        "total_results": results.get('searchInformation', {}).get('totalResults', '0')
                    }
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    error="No se encontraron resultados para la búsqueda"
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Error en la búsqueda: {str(e)}"
            )
    
    def _search_google(self, query: str, num_results: int = 5, language: str = 'es', safe_search: str = 'off') -> Optional[Dict]:
        """
        Realiza la búsqueda usando Google Custom Search API.
        
        Args:
            query (str): Consulta de búsqueda
            num_results (int): Número de resultados
            language (str): Idioma de los resultados
            safe_search (str): Nivel de filtro de contenido
            
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
    
    def format_results(self, raw_results: Dict) -> List[Dict[str, Any]]:
        """
        Formatea los resultados de Google para una presentación más limpia.
        
        Args:
            raw_results (Dict): Resultados crudos de la API
            
        Returns:
            List[Dict]: Lista de resultados formateados
        """
        formatted_results = []
        
        if not raw_results or 'items' not in raw_results:
            return formatted_results
        
        for item in raw_results['items']:
            result = {
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayLink': item.get('displayLink', ''),
                'formattedUrl': item.get('formattedUrl', '')
            }
            
            # Agregar imagen si está disponible
            if 'pagemap' in item and 'cse_image' in item['pagemap']:
                result['image'] = item['pagemap']['cse_image'][0].get('src', '')
            
            formatted_results.append(result)
        
        return formatted_results
    
    def search_with_formatting(self, query: str, **kwargs) -> ToolExecutionResult:
        """
        Ejecuta búsqueda y devuelve resultados formateados.
        
        Args:
            query (str): Consulta de búsqueda
            **kwargs: Parámetros adicionales
            
        Returns:
            ToolExecutionResult: Resultado con datos formateados
        """
        result = self.execute(query, **kwargs)
        
        if result.success and result.data:
            formatted_data = self.format_results(result.data)
            return ToolExecutionResult(
                success=True,
                data=formatted_data,
                metadata=result.metadata
            )
        
        return result
    
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


# Función de conveniencia para uso directo
def buscar_internet(query: str, num_results: int = 5, language: str = 'es') -> Dict[str, Any]:
    """
    Función de conveniencia para búsquedas rápidas.
    
    Args:
        query (str): Texto a buscar
        num_results (int): Número de resultados
        language (str): Idioma de los resultados
        
    Returns:
        Dict: Resultado de la búsqueda
    """
    tool = GoogleSearchTool()
    result = tool.search_with_formatting(query, num_results=num_results, language=language)
    return result.to_dict()


# Alias para compatibilidad
GoogleInternetSearch = GoogleSearchTool