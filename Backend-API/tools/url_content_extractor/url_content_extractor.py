import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from collections import Counter
from .base_tool import BaseTool, ToolMetadata, ToolCategory
import json

class WebContentExtractorTool(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Url Content Extractor",
            description="Extrae y resume el contenido más relevante de una URL o múltiples URLs incluyendo texto principal, imágenes y estructura",
            category=ToolCategory.UTILITY,
            requires_api_key=False,
            parameters={
                "url": "URL completa https://ejemplo.com o array de URLs ['https://ejemplo1.com', 'https://ejemplo2.com']",
                "summary_length": "Longitud del resumen en caracteres (default: 1000)",
                "include_images": "Incluir información de imágenes (default: True)",
                "max_concurrent": "Número máximo de URLs a procesar simultáneamente (default: 5)"
            },
            usage_example={
                "una_url": '{"tool": "url_content_extractor", "query": "https://ejemplo.com"}',
                "multiples_urls": '{"tool": "url_content_extractor", "query": ["https://ejemplo1.com", "https://ejemplo2.com"]}',
                "formatos_soportados": [
                    'URL individual: "https://ejemplo.com"',
                    'Array JSON: ["https://ejemplo1.com", "https://ejemplo2.com"]',
                    "Lista Python: ['https://ejemplo1.com', 'https://ejemplo2.com']",
                    'URLs separadas: "https://ejemplo1.com, https://ejemplo2.com"'
                ]
            }
        )
    
    def execute(self, query: str, **kwargs):
        """Extrae contenido relevante de una URL o múltiples URLs"""
        summary_length = kwargs.get('summary_length', 1000)
        include_images = kwargs.get('include_images', True)
        max_concurrent = kwargs.get('max_concurrent', 5)
        
        try:
            # Determinar si es una URL individual o múltiples URLs
            urls = self._parse_urls(query)
            
            if len(urls) == 1:
                return self.extract_and_summarize(urls[0], summary_length, include_images)
            else:
                return self.extract_multiple_urls(urls, summary_length, include_images, max_concurrent)
                
        except Exception as e:
            return f"""
Error al procesar la consulta: {str(e)}

Uso de la herramienta:
{{"tool": "url_content_extractor", "query": "https://ejemplo.com"}}

Para múltiples URLs:
{{"tool": "url_content_extractor", "query": ["https://ejemplo1.com", "https://ejemplo2.com"]}}

Formatos soportados:
- URL individual: "https://ejemplo.com"
- Array JSON: ["https://ejemplo1.com", "https://ejemplo2.com"]
- Lista Python: ['https://ejemplo1.com', 'https://ejemplo2.com']
- URLs separadas: "https://ejemplo1.com, https://ejemplo2.com"

"""
    
    @staticmethod
    def _parse_urls(query):
        """Parsea la entrada para determinar si es una URL individual o múltiples URLs"""
        query = query.strip()
        
        # Intentar parsear como JSON (array de URLs)
        try:
            parsed = json.loads(query)
            if isinstance(parsed, list):
                return [url for url in parsed if isinstance(url, str) and url.strip()]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Intentar parsear como lista de Python
        try:
            if query.startswith('[') and query.endswith(']'):
                # Evaluar de forma segura solo si parece una lista
                parsed = eval(query)
                if isinstance(parsed, list):
                    return [url for url in parsed if isinstance(url, str) and url.strip()]
        except:
            pass
        
        # Buscar múltiples URLs en texto plano (separadas por comas, espacios o saltos de línea)
        url_pattern = r'https?://[^\s,\n]+'
        urls = re.findall(url_pattern, query)
        
        if urls:
            return urls
        
        # Si no se encontraron URLs con patrón, tratar como URL individual
        return [query]
    
    @staticmethod
    def extract_multiple_urls(urls, summary_length=1000, include_images=True, max_concurrent=5):
        """Extrae contenido de múltiples URLs"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        # Limitar el número de URLs a procesar
        urls = urls[:max_concurrent]
        
        results = []
        
        def extract_single_url(url):
            """Función auxiliar para extraer contenido de una URL"""
            try:
                return {
                    'url': url,
                    'content': WebContentExtractorTool.extract_and_summarize(url, summary_length, include_images),
                    'success': True
                }
            except Exception as e:
                return {
                    'url': url,
                    'content': f"""Error al procesar {url}: {str(e)}

Uso de la herramienta:
{{"tool": "url_content_extractor", "query": "https://ejemplo.com"}}

Para múltiples URLs:
{{"tool": "url_content_extractor", "query": ["https://ejemplo1.com", "https://ejemplo2.com"]}}""",
                    'success': False
                }
        
        # Usar ThreadPoolExecutor para procesar URLs en paralelo
        with ThreadPoolExecutor(max_workers=min(3, len(urls))) as executor:
            # Enviar todas las tareas
            future_to_url = {executor.submit(extract_single_url, url): url for url in urls}
            
            # Recopilar resultados
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
        
        # Ordenar resultados por URL original
        results.sort(key=lambda x: urls.index(x['url']) if x['url'] in urls else float('inf'))
        
        # Formatear resultado final
        final_result = f"""
EXTRACCIÓN DE CONTENIDO DE MÚLTIPLES URLs
{'-'*60}
URLs procesadas: {len(urls)}
Exitosas: {sum(1 for r in results if r['success'])}
Con errores: {sum(1 for r in results if not r['success'])}

{'='*60}
"""
        
        for i, result in enumerate(results, 1):
            final_result += f"\n{i}. {result['url']}\n"
            final_result += f"{'='*60}\n"
            
            if result['success']:
                final_result += result['content']
            else:
                final_result += f"❌ {result['content']}"
            
            final_result += f"\n{'='*60}\n"
        
        return final_result
    
    @staticmethod
    def clean_text(text):
        """Limpia y normaliza el texto"""
        if not text:
            return ""
        
        # Eliminar espacios extra y saltos de línea
        text = re.sub(r'\s+', ' ', text.strip())
        # Eliminar caracteres especiales problemáticos
        text = re.sub(r'[^\w\s\.,;:!?¿¡\-\(\)]', '', text)
        return text
    
    @staticmethod
    def extract_main_content(soup):
        """Extrae el contenido principal de la página"""
        # Intentar encontrar el contenido principal usando selectores comunes
        main_content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '#content',
            '#main-content'
        ]
        
        main_content = ""
        for selector in main_content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    # Eliminar elementos no deseados
                    for unwanted in element.select('script, style, nav, footer, header, aside, .advertisement, .ads'):
                        unwanted.decompose()
                    
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 100:  # Solo si tiene contenido sustancial
                        main_content += text + " "
                break
        
        # Si no encontró contenido principal, usar el body completo
        if not main_content:
            # Eliminar elementos no deseados del body
            for unwanted in soup.select('script, style, nav, footer, header, aside, .advertisement, .ads'):
                unwanted.decompose()
            
            main_content = soup.get_text(separator=' ', strip=True)
        
        return main_content
    
    @staticmethod
    def extract_key_phrases(text, num_phrases=10):
        """Extrae frases clave del texto"""
        if not text:
            return []
        
        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', text)
        
        # Filtrar oraciones relevantes (longitud media, no muy cortas ni muy largas)
        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 150:
                relevant_sentences.append(sentence)
        
        return relevant_sentences[:num_phrases]
    
    @staticmethod
    def generate_summary(text, max_length=1000):
        """Genera un resumen del texto"""
        if not text or len(text) <= max_length:
            return text
        
        # Dividir en párrafos
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        # Si no hay párrafos, dividir por oraciones
        if not paragraphs:
            sentences = re.split(r'[.!?]+', text)
            paragraphs = [s.strip() for s in sentences if s.strip()]
        
        # Seleccionar los párrafos más relevantes
        summary = ""
        for paragraph in paragraphs:
            if len(summary) + len(paragraph) <= max_length:
                summary += paragraph + " "
            else:
                # Añadir parte del párrafo si queda espacio
                remaining_space = max_length - len(summary)
                if remaining_space > 50:
                    summary += paragraph[:remaining_space-3] + "..."
                break
        
        return summary.strip()
    
    @staticmethod
    def extract_and_summarize(url, summary_length=1000, include_images=True):
        """Extrae contenido relevante y genera un resumen completo"""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Información básica
                title = soup.find('title')
                title_text = WebContentExtractorTool.clean_text(title.get_text()) if title else "Sin título"
                
                # Meta descripción
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc.get('content', '').strip() if meta_desc else ""
                
                # Palabras clave meta
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                keywords = meta_keywords.get('content', '').strip() if meta_keywords else ""
                
                # Extraer contenido principal
                main_content = WebContentExtractorTool.extract_main_content(soup)
                main_content = WebContentExtractorTool.clean_text(main_content)
                
                # Extraer encabezados principales
                main_headings = []
                for level in range(1, 4):  # Solo H1, H2, H3 para lo más relevante
                    h_tags = soup.find_all(f'h{level}')
                    for h_tag in h_tags:
                        text = WebContentExtractorTool.clean_text(h_tag.get_text())
                        if text and len(text) > 3:
                            main_headings.append({
                                'level': level,
                                'text': text
                            })
                
                # Generar resumen del contenido
                content_summary = WebContentExtractorTool.generate_summary(main_content, summary_length)
                
                # Extraer frases clave
                key_phrases = WebContentExtractorTool.extract_key_phrases(main_content, 5)
                
                # Información de imágenes principales
                main_images = []
                if include_images:
                    img_tags = soup.find_all('img')
                    for img in img_tags:
                        img_src = img.get('src')
                        if img_src:
                            img_url = urljoin(url, img_src)
                            img_alt = WebContentExtractorTool.clean_text(img.get('alt', ''))
                            img_title = WebContentExtractorTool.clean_text(img.get('title', ''))
                            
                            # Filtrar imágenes relevantes (no iconos pequeños)
                            width = img.get('width')
                            height = img.get('height')
                            
                            # Considerar relevante si no tiene dimensiones o si son >= 100px
                            is_relevant = True
                            if width and height:
                                try:
                                    if int(width) < 100 or int(height) < 100:
                                        is_relevant = False
                                except ValueError:
                                    pass
                            
                            if is_relevant and (img_alt or img_title or len(main_images) < 5):
                                main_images.append({
                                    'url': img_url,
                                    'alt': img_alt,
                                    'title': img_title
                                })
                
                # Formatear resultado
                result = f"""
RESUMEN COMPLETO DE LA PÁGINA WEB
{'-'*50}
URL: {url}
Título: {title_text}
"""
                
                if description:
                    result += f"Descripción: {description}\n"
                
                if keywords:
                    result += f"Palabras clave: {keywords}\n"
                
                result += f"\nCONTENIDO PRINCIPAL:\n{'-'*30}\n"
                
                if main_headings:
                    result += "ESTRUCTURA PRINCIPAL:\n"
                    for heading in main_headings[:8]:  # Limitar a 8 encabezados
                        indent = "  " * (heading['level'] - 1)
                        result += f"{indent}• {heading['text']}\n"
                    result += "\n"
                
                result += f"RESUMEN DEL CONTENIDO:\n{content_summary}\n\n"
                
                if key_phrases:
                    result += f"FRASES CLAVE:\n"
                    for i, phrase in enumerate(key_phrases, 1):
                        result += f"{i}. {phrase}\n"
                    result += "\n"
                
                if include_images and main_images:
                    result += f"IMÁGENES PRINCIPALES ({len(main_images)} encontradas):\n{'-'*30}\n"
                    for i, img in enumerate(main_images, 1):
                        result += f"{i}. {img['url']}\n"
                        if img['alt']:
                            result += f"   Descripción: {img['alt']}\n"
                        if img['title']:
                            result += f"   Título: {img['title']}\n"
                        result += "\n"
                
                # Estadísticas
                word_count = len(main_content.split())
                char_count = len(main_content)
                
                result += f"ESTADÍSTICAS:\n{'-'*30}\n"
                result += f"Palabras totales: {word_count}\n"
                result += f"Caracteres totales: {char_count}\n"
                result += f"Encabezados principales: {len(main_headings)}\n"
                if include_images:
                    result += f"Imágenes relevantes: {len(main_images)}\n"
                
                return result
                
            else:
                return f"Error al acceder a la URL: Código de estado {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"""
Error de conexión: {str(e)}

Asegúrate de que la URL es válida y accesible.
Uso de la herramienta: 
{{"tool": "url_content_extractor", "query": "https://ejemplo.com"}}

Para múltiples URLs:
{{"tool": "url_content_extractor", "query": ["https://ejemplo1.com", "https://ejemplo2.com"]}}
"""
        except Exception as e:
            return f"""
Error al extraer contenido: {str(e)}

Uso de la herramienta:
{{"tool": "url_content_extractor", "query": "https://ejemplo.com"}}

Para múltiples URLs:
{{"tool": "url_content_extractor", "query": ["https://ejemplo1.com", "https://ejemplo2.com"]}}

Formatos soportados:
- URL individual: "https://ejemplo.com"
- Array JSON: ["https://ejemplo1.com", "https://ejemplo2.com"]
- Lista Python: ['https://ejemplo1.com', 'https://ejemplo2.com']
- URLs separadas: "https://ejemplo1.com, https://ejemplo2.com"
"""
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Url Content Extractor"