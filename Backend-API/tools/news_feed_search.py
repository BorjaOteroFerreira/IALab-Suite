import json
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from .base_tool import BaseTool, ToolMetadata, ToolCategory

class NewsFeedTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Feed de Noticias",
            description="Obtiene las últimas noticias por categorías o temas específicos",
            category=ToolCategory.SEARCH,
            requires_api_key=True,
            api_key_env_var="NEWS_API_KEY",
            usage_example={
                "por_tema": '{"tool": "news_feed", "query": "tecnología"}',
                "por_categoria": '{"tool": "news_feed", "category": "sports"}',
                "con_opciones": '{"tool": "news_feed", "query": "política", "country": "es", "language": "es", "page_size": 5}',
                "formatos_soportados": [
                    'query: tema de búsqueda (string, opcional)',
                    'category: categoría de noticias (string, opcional)',
                    'country: país (string, opcional)',
                    'language: idioma (string, opcional)',
                    'page_size: número de resultados (int, opcional)'
                ]
            }
        )

    @classmethod
    def get_tool_name(cls) -> str:
        return "Feed de Noticias"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta búsqueda de noticias"""
        category = kwargs.get('category')
        country = kwargs.get('country', 'es')
        language = kwargs.get('language', 'es')
        page_size = min(kwargs.get('page_size', 10), 20)  # Limitado para mejor rendimiento
        
        return NewsFeedTool.get_news(query, category, country, language, page_size)

    @staticmethod
    def get_news(query=None, category=None, country='es', language='es', page_size=10):
        """Obtiene noticias de NewsAPI y extrae contenido relevante."""
        
        api_key = os.environ.get('NEWS_API_KEY')
        if not api_key:
            return "Error: NEW_SAPI_KEY no configurada en variables de entorno."
        
        base_url = "https://newsapi.org/v2"
        
        try:
            # Determinar endpoint y parámetros
            if query:
                # Búsqueda por tema
                url = f"{base_url}/everything"
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                params = {
                    'q': query,
                    'language': language,
                    'sortBy': 'publishedAt',
                    'pageSize': page_size,
                    'from': from_date,
                    'apiKey': api_key
                }
            else:
                # Top headlines por categoría
                url = f"{base_url}/top-headlines"
                params = {
                    'pageSize': page_size,
                    'apiKey': api_key
                }
                if category:
                    params['category'] = category
                if country:
                    params['country'] = country
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok' or not data.get('articles'):
                return "No se encontraron noticias relevantes."
            
            # Procesar artículos
            news_results = []
            for article in data['articles']:
                title = article.get('title', '').replace('|', '-').replace('||', '--')
                description = article.get('description', '').replace('|', '-').replace('||', '--')
                source = article.get('source', {}).get('name', 'Fuente desconocida')
                url_article = article.get('url', '')
                published_at = NewsFeedTool.format_date(article.get('publishedAt'))
                author = article.get('author', 'Autor desconocido')
                
                if not url_article:
                    continue
                
                # Extraer contenido adicional del artículo
                content = NewsFeedTool.extract_article_content(url_article)
                
                news_results.append('\n'.join([
                    f"Título: {title}",
                    f"Fuente: {source}",
                    f"Autor: {author}",
                    f"Fecha: {published_at}",
                    f"Descripción: {description}",
                    f"URL: {url_article}",
                    f"Contenido: {content}",
                    "\n-----------------"
                ]))
            
            if not news_results:
                return "No se pudieron procesar las noticias encontradas."
            
            header = f"📰 Noticias encontradas: {len(news_results)}"
            if query:
                header += f" sobre '{query}'"
            if category:
                header += f" en categoría '{category}'"
            header += f"\n{'='*50}\n"
            
            return header + '\n'.join(news_results)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return "Error al obtener noticias de la API."
        except Exception as e:
            print(f"Error processing news: {e}")
            return "Error al procesar las noticias."
    
    @staticmethod
    def extract_article_content(url):
        """Extrae contenido relevante del artículo de noticias."""
        
        # Filtrar URLs muy largas o problemáticas
        if len(url) > 200:
            return "Contenido no extraído (URL muy larga)."
        
        # Lista de dominios problemáticos o que requieren JS
        blocked_domains = [
            'youtube.com', 'youtu.be', 'twitter.com', 'x.com', 
            'facebook.com', 'instagram.com', 'tiktok.com',
            'reddit.com', 'pinterest.com'
        ]
        
        domain = urlparse(url).netloc.lower()
        if any(blocked in domain for blocked in blocked_domains):
            return "Contenido no extraído (plataforma social)."
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remover elementos no deseados
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                tag.decompose()
            
            # Buscar contenido principal en orden de prioridad
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main'
            ]
            
            content_text = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Extraer párrafos principales
                    paragraphs = element.find_all(['p', 'h1', 'h2', 'h3'])
                    texts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if len(text) > 50:  # Solo párrafos con contenido sustancial
                            texts.append(text)
                    
                    content_text = ' '.join(texts[:3])  # Primeros 3 párrafos relevantes
                    break
            
            # Fallback: buscar párrafos en todo el documento
            if not content_text:
                paragraphs = soup.find_all('p')
                texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 50:
                        texts.append(text)
                content_text = ' '.join(texts[:2])  # Solo 2 párrafos
            
            # Buscar imagen destacada
            featured_image = ""
            img_selectors = [
                'meta[property="og:image"]',
                'article img',
                '.featured-image img',
                '.article-image img'
            ]
            
            for selector in img_selectors:
                if 'meta' in selector:
                    meta = soup.select_one(selector)
                    if meta and meta.get('content'):
                        img_url = meta['content']
                        if NewsFeedTool.is_valid_image_url(img_url):
                            featured_image = f"![{domain}]({img_url})"
                            break
                else:
                    img = soup.select_one(selector)
                    if img and img.get('src'):
                        img_url = urljoin(url, img['src'])
                        if NewsFeedTool.is_valid_image_url(img_url):
                            featured_image = f"![{domain}]({img_url})"
                            break
            
            # Limitar longitud del contenido
            if len(content_text) > 500:
                content_text = content_text[:500] + "..."
            
            result = ""
            if featured_image:
                result += f"Imagen: {featured_image}\n"
            if content_text:
                result += f"Resumen: {content_text}"
            
            return result if result else "Contenido no extraído."
            
        except requests.exceptions.RequestException as e:
            print(f"Error extracting article content: {e}")
            return "Error al extraer contenido del artículo."
        except Exception as e:
            print(f"Error parsing article: {e}")
            return "Error al procesar el artículo."
    
    @staticmethod
    def is_valid_image_url(url):
        """Valida si la URL es una imagen válida."""
        if not url or len(url) > 300:
            return False
        
        # Filtrar imágenes no deseadas
        blocked_keywords = [
            'ads.', 'tracker.', 'pixel.', 'gettyimages', 
            'logo.', 'icon.', 'favicon.', 'avatar.',
            'placeholder', 'loading.gif'
        ]
        
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in blocked_keywords):
            return False
        
        # Verificar extensiones de imagen
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        return any(ext in url_lower for ext in image_extensions) or 'image' in url_lower
    
    @staticmethod
    def format_date(date_str):
        """Formatea la fecha de publicación."""
        if not date_str:
            return 'Fecha desconocida'
        
        try:
            # Parsear fecha ISO format
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M UTC')
        except:
            return date_str
    
    @staticmethod
    def get_available_categories():
        """Retorna las categorías disponibles."""
        return ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    
    @staticmethod
    def get_supported_countries():
        """Retorna códigos de países soportados."""
        return {
            'us': 'Estados Unidos', 
            'es': 'España', 
            'mx': 'México', 
            'ar': 'Argentina', 
            'co': 'Colombia', 
            'pe': 'Perú',
            'cl': 'Chile', 
            've': 'Venezuela', 
            'gb': 'Reino Unido',
            'fr': 'Francia', 
            'de': 'Alemania', 
            'it': 'Italia',
            'br': 'Brasil',
            'ca': 'Canadá', 
            'au': 'Australia'
        }