import requests
from bs4 import BeautifulSoup
import re
import random
import time
import random
from urllib.parse import quote_plus, urlparse
from langchain.tools import tool
from requests_html import HTMLSession
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

from .base_tool import BaseTool, ToolMetadata, ToolCategory

# Importar la función search_internet directamente
def _get_search_internet_function():
    """Obtiene la función search_internet de SearchTools de manera segura"""
    try:
        from .search_tools import SearchTools
        return SearchTools.search_internet
    except Exception:
        # Fallback: función dummy si no se puede importar
        return lambda query: "Error: No se pudo cargar la función de búsqueda en internet"

_search_internet = _get_search_internet_function()

class AdvancedSearchTools(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Busqueda Multiples Motores",
            description="Realiza búsquedas avanzadas  con técnicas especializadas y varios motores de búsqueda",
            category=ToolCategory.SEARCH,
            requires_api_key=False
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Busqueda Multiples Motores"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta búsqueda avanzada"""
        return self.advanced_search(query)
    """
    Clase que proporciona herramientas de búsqueda OSINT
    """
    
    # Lista de User-Agents para rotación
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.1518.55",
    ]
    
    @staticmethod
    def get_random_headers():
        """Genera encabezados HTTP aleatorios para evitar detección."""
        return {
            "User-Agent": random.choice(AdvancedSearchTools.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    @staticmethod
    def extract_content_from_url(url, max_retries=3):
        """
        Extrae contenido de una URL con reintentos y manejo de errores.
        """
        for attempt in range(max_retries):
            try:
                session = HTMLSession()
                headers = AdvancedSearchTools.get_random_headers()
                response = session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Extraer elementos de texto relevantes
                text_elements = response.html.find('body')[0].xpath('//p|//h1|//h2|//h3|//article')
                content = '\n'.join([element.text for element in text_elements if element.text.strip()])
                
                # Si no hay suficiente contenido, intentar extraer todo el texto
                if len(content) < 200:
                    content = response.html.text
                
                return content[:2000]  # Limitar a 2000 caracteres
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Error al extraer contenido: {str(e)}"
                time.sleep(random.uniform(1, 3))  # Espera aleatoria entre intentos
    
    @staticmethod
    def summarize_content(content, language='spanish'):
        """Resume el contenido extraído usando el algoritmo LSA."""
        try:
            from sumy.nlp.stemmers import Stemmer
            from sumy.utils import get_stop_words
            
            # Preparar el texto para el resumen
            from sumy.parsers.plaintext import PlaintextParser
            parser = PlaintextParser.from_string(content, Tokenizer(language))
            
            # Aplicar el algoritmo LSA para resumir
            stemmer = Stemmer(language)
            summarizer = LsaSummarizer(stemmer)
            summarizer.stop_words = get_stop_words(language)
            
            # Obtener un resumen de 3 oraciones
            summary = summarizer(parser.document, 3)
            return " ".join(str(sentence) for sentence in summary)
        except Exception as e:
            return f"No se pudo resumir el contenido: {str(e)}"   
    @staticmethod
    def search_duckduckgo(query):
        """Realiza una búsqueda en DuckDuckGo y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('a', class_='result__a')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a', class_='result__a')
                link = link_element.get('href') if link_element else ""
                
                # Extraer el enlace real si es un redireccionamiento
                if link and '/redirect/' in link:
                    link_match = re.search(r'uddg=([^&]+)', link)
                    if link_match:
                        from urllib.parse import unquote
                        link = unquote(link_match.group(1))
                
                snippet_element = result.find('a', class_='result__snippet')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en DuckDuckGo: {str(e)}"
    
    @staticmethod
    def search_google(query):
        """Realiza una búsqueda en Google y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&num={top_results}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Intentar diferentes estructuras de resultados que Google podría usar
            results = soup.find_all('div', class_='g')
            
            if not results:
                results = soup.select("div.tF2Cxc")
            
            if not results:
                results = soup.select("div.MjjYud")
            
            if not results:
                results = soup.select("div.Gx5Zad")
            
            if not results:
                # Enfoque alternativo: buscar cualquier elemento que tenga enlaces y descripciones
                results = soup.select("div.yuRUbf, div.Z26q7c, div.kvH3mc")
            
            if not results:
                # Guardar el HTML para depuración
                with open("google_response.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                return "No se encontraron resultados para la búsqueda. Se ha guardado la respuesta HTML para depuración."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.select_one('h3')
                title = title_element.get_text() if title_element else "Sin título"
                
                link_element = result.select_one('a')
                link = link_element.get('href') if link_element else ""
                
                # Extraer el enlace real si es un redireccionamiento
                if link and link.startswith('/url?'):
                    link_match = re.search(r'q=([^&]+)', link)
                    if link_match:
                        from urllib.parse import unquote
                        link = unquote(link_match.group(1))
                
                snippet_element = result.select_one('div.VwiC3b')
                snippet = snippet_element.get_text() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link and link.startswith('http'):
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Google: {str(e)}"
    
    @staticmethod
    def search_bing(query):
        """Realiza una búsqueda en Bing y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded_query}&count={top_results}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('li', class_='b_algo')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('h2')
                title = title_element.get_text() if title_element else "Sin título"
                
                link_element = result.find('a')
                link = link_element.get('href') if link_element else ""
                
                snippet_element = result.find('div', class_='b_caption')
                snippet = snippet_element.get_text() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Bing: {str(e)}"
  



    


    @staticmethod
    def extract_yandex_results(soup):
        """Extrae títulos, enlaces y descripciones de los resultados de búsqueda en Yandex."""
        results = []
        for result in soup.find_all("li", class_="serp-item"):
            title_tag = result.find("h2")
            link_tag = result.find("a", href=True)
            snippet_tag = result.find("div", class_="text-container")
            
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag["href"]
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Sin descripción"
                
                # Filtrar enlaces irrelevantes (ej. yabs.yandex)
                if "yabs.yandex" not in link:
                    results.append({"title": title, "link": link, "snippet": snippet})
        return results

    @staticmethod
    def search_yandex(query, top_results=5):
        """Realiza una búsqueda en Yandex y devuelve los resultados más relevantes."""
        encoded_query = quote_plus(query)
        url = f"https://yandex.com/search/?text={encoded_query}&lr=114681"
        
        headers = AdvancedSearchTools.get_random_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return f"Error: Código {response.status_code}"
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = AdvancedSearchTools.extract_yandex_results(soup)
            
            if not results:
                return "No se encontraron resultados en Yandex."
            
            # Formatear la salida
            output = []
            for idx, result in enumerate(results[:top_results], 1):
                output.append(f"🔹 **{idx}. {result['title']}**\n🔗 {result['link']}\n📄 {result['snippet']}\n")
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error en la búsqueda: {str(e)}"


    @staticmethod
    def extract_yandex_results(soup):
        selectors = [
            'li.serp-item',
            'div.OrganicTextContentSpan',
            '.organic',
            'div[data-fast-name="organic"]',
            'div.link_cropped_no',
            '.search-result',
            '.b-serp-item',
            '.misspell__message + div',
            '.typo-message + div'
        ]
        
        for selector in selectors:
            results = soup.select(selector)
            if results:
                return results
        
        # Buscar cualquier contenedor que parezca resultado de búsqueda
        containers = soup.find_all(['div', 'li'], class_=lambda c: c and any(term in c for term in ['serp', 'organic', 'result', 'search']))
        if containers:
            return containers
        
        # Último recurso: buscar estructuras que parecen resultados
        divs = soup.find_all('div')
        return [div for div in divs if div.find('a') and (div.find('h2') or div.find('h3') or div.find('p'))]
    
    @staticmethod
    def search_startpage(query):
        """Realiza una búsqueda en Startpage y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://www.startpage.com/sp/search?q={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='w-gl__result')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('a', class_='w-gl__result-title')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a', class_='w-gl__result-title')
                link = link_element.get('href') if link_element else ""
                
                snippet_element = result.find('p', class_='w-gl__description')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Startpage: {str(e)}"
    
    @staticmethod
    def search_baidu(query):
        """Realiza una búsqueda en Baidu y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://www.baidu.com/s?wd={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('h3')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a')
                link = link_element.get('href') if link_element else ""
                
                snippet_element = result.find('div', class_='c-abstract')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Baidu: {str(e)}"
    
    @staticmethod
    def search_ecosia(query):
        """Realiza una búsqueda en Ecosia y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://www.ecosia.org/search?q={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('a', class_='result-title')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a', class_='result-url')
                link = link_element.get('href') if link_element else ""
                
                snippet_element = result.find('div', class_='result-snippet')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Ecosia: {str(e)}"
    
    @staticmethod
    def search_archive(query):
        """Realiza una búsqueda en Archive.org (Wayback Machine) y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://archive.org/search?query={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='item-ia')
            
            if not results:
                return "No se encontraron resultados para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('div', class_='ttl')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a', class_='stealth')
                link = f"https://archive.org{link_element.get('href')}" if link_element else ""
                
                snippet_element = result.find('div', class_='details')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Archive.org: {str(e)}"
    
    @staticmethod
    def search_scholar(query):
        """Realiza una búsqueda en Google Scholar y devuelve los resultados académicos más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://scholar.google.com/scholar?q={encoded_query}&hl=es"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='gs_ri')
            
            if not results:
                return "No se encontraron resultados académicos para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('h3', class_='gs_rt')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = title_element.find('a') if title_element else None
                link = link_element.get('href') if link_element else ""
                
                snippet_element = result.find('div', class_='gs_rs')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                authors_element = result.find('div', class_='gs_a')
                authors = authors_element.get_text().strip() if authors_element else "Autor desconocido"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Autores: {authors}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en Google Scholar: {str(e)}"
    
    @staticmethod
    def search_news(query):
        """Realiza una búsqueda en fuentes de noticias y devuelve los resultados más relevantes."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://news.google.com/search?q={encoded_query}&hl=es"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='NiLAwe')
            
            if not results:
                return "No se encontraron noticias para la búsqueda."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                title_element = result.find('h3', class_='ipQwMb')
                title = title_element.get_text().strip() if title_element else "Sin título"
                
                link_element = result.find('a')
                rel_link = link_element.get('href') if link_element else ""
                link = f"https://news.google.com{rel_link[1:]}" if rel_link.startswith('./') else ""
                
                snippet_element = result.find('span', class_='xBbh9')
                snippet = snippet_element.get_text().strip() if snippet_element else "Sin descripción"
                
                source_element = result.find('a', class_='wEwyrc')
                source = source_element.get_text().strip() if source_element else "Fuente desconocida"
                
                time_element = result.find('time')
                timestamp = time_element.get_text().strip() if time_element else "Fecha desconocida"
                
                # Extraer contenido de la página
                content = "No se pudo extraer contenido."
                if link:
                    content = AdvancedSearchTools.extract_content_from_url(link)
                    summary = AdvancedSearchTools.summarize_content(content)
                else:
                    summary = "No se pudo obtener un resumen."
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Título: {title}\n"
                    f"Fuente: {source} - {timestamp}\n"
                    f"Enlace: {link}\n"
                    f"Descripción: {snippet}\n"
                    f"Resumen: {summary}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en noticias: {str(e)}"
    
    @staticmethod
    def get_domain_info(domain):
        """Obtiene información básica sobre un dominio web."""
        try:
            # Validar el formato del dominio
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$', domain):
                return f"Formato de dominio inválido: {domain}"
            
            # Obtener información del dominio utilizando whois
            try:
                import whois
                domain_info = whois.whois(domain)
                
                # Crear una salida formateada de la información
                info = {
                    "Dominio": domain,
                    "Registrante": domain_info.registrant_name if hasattr(domain_info, 'registrant_name') else "No disponible",
                    "Organización": domain_info.org if hasattr(domain_info, 'org') else "No disponible",
                    "Registrador": domain_info.registrar if hasattr(domain_info, 'registrar') else "No disponible",
                    "Fecha de creación": domain_info.creation_date if hasattr(domain_info, 'creation_date') else "No disponible",
                    "Fecha de expiración": domain_info.expiration_date if hasattr(domain_info, 'expiration_date') else "No disponible",
                    "Fecha de actualización": domain_info.updated_date if hasattr(domain_info, 'updated_date') else "No disponible",
                    "Servidores de nombres": domain_info.name_servers if hasattr(domain_info, 'name_servers') else "No disponible",
                    "País": domain_info.country if hasattr(domain_info, 'country') else "No disponible",
                    "Estado/Provincia": domain_info.state if hasattr(domain_info, 'state') else "No disponible",
                    "Ciudad": domain_info.city if hasattr(domain_info, 'city') else "No disponible"
                }
                
                result = "\n".join([f"{key}: {value}" for key, value in info.items()])
                
            except ImportError:
                # Alternativa si whois no está disponible
                headers = AdvancedSearchTools.get_random_headers()
                response = requests.get(f"http://{domain}", headers=headers, timeout=5)
                server = response.headers.get('Server', 'No disponible')
                
                # Intentar resolver la IP
                import socket
                try:
                    ip = socket.gethostbyname(domain)
                except:
                    ip = "No se pudo resolver"
                
                result = (
                    f"Dominio: {domain}\n"
                    f"IP: {ip}\n"
                    f"Servidor: {server}\n"
                    f"Nota: Información limitada debido a que el módulo whois no está disponible"
                )
            
            return result
        
        except Exception as e:
            return f"Error al obtener información del dominio: {str(e)}"
    
    @staticmethod
    def reverse_image_search(image_url):
        """Realiza una búsqueda inversa de imagen utilizando TinEye."""
        try:
            # Verificar formato de URL
            if not image_url.startswith(('http://', 'https://')):
                return "La URL de la imagen debe comenzar con http:// o https://"
            
            # Preparar la búsqueda en TinEye
            search_url = f"https://tineye.com/search/?url={quote_plus(image_url)}"
            
            headers = AdvancedSearchTools.get_random_headers()
            session = HTMLSession()
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Esperar a que se cargue el contenido dinámico
            response.html.render(timeout=20)
            
            soup = BeautifulSoup(response.html.html, 'html.parser')
            
            # Extraer resultados
            match_count_element = soup.select_one('.matches strong')
            match_count = match_count_element.text if match_count_element else "0"
            
            results = soup.select('.match-row')
            
            if not results:
                return "No se encontraron coincidencias para esta imagen."
            
            output = [f"Coincidencias encontradas: {match_count}"]
            
            for i, result in enumerate(results[:5]):
                # Extraer información de la coincidencia
                site_element = result.select_one('.match-thumb-link')
                site_url = site_element.get('href') if site_element else "No disponible"
                
                domain_element = result.select_one('.domains-link')
                domain = domain_element.text.strip() if domain_element else "Dominio desconocido"
                
                size_element = result.select_one('.image-size')
                size = size_element.text.strip() if size_element else "Tamaño desconocido"
                
                match_info = (
                    f"Coincidencia {i+1}:\n"
                    f"Sitio: {domain}\n"
                    f"URL: {site_url}\n"
                    f"Tamaño: {size}\n"
                    "-----------------"
                )
                output.append(match_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda inversa de imagen: {str(e)}"
    
    @staticmethod
    def search_username(username):
        """Busca información sobre un nombre de usuario en múltiples plataformas sociales."""
        username= username.replace(" ", "")
        sites = [
            {"name": "Twitter/X", "url": f"https://twitter.com/{username}"},
            {"name": "Instagram", "url": f"https://www.instagram.com/{username}/"},
            {"name": "GitHub", "url": f"https://github.com/{username}"},
            {"name": "LinkedIn", "url": f"https://www.linkedin.com/in/{username}/"},
            {"name": "Facebook", "url": f"https://www.facebook.com/{username}"},
            {"name": "Reddit", "url": f"https://www.reddit.com/user/{username}"},
            {"name": "YouTube", "url": f"https://www.youtube.com/@{username}"},
            {"name": "TikTok", "url": f"https://www.tiktok.com/@{username}"},
            {"name": "Pinterest", "url": f"https://www.pinterest.com/{username}/"},
            {"name": "Medium", "url": f"https://medium.com/@{username}"}
        ]
        
        results = []
        
        for site in sites:
            try:
                headers = AdvancedSearchTools.get_random_headers()
                response = requests.get(site["url"], headers=headers, timeout=5)
                
                if response.status_code == 200:
                    # Intentar extraer información básica
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.title.text.strip() if soup.title else "No hay título disponible"
                    
                    results.append(f"{site['name']}: Perfil encontrado - {site['url']}")
                    
                    # Para búsquedas más profundas, podríamos extraer más información del perfil
                    
                else:
                    results.append(f"{site['name']}: Perfil no encontrado o inaccesible")
                
                # Esperar un tiempo aleatorio para evitar detección
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                results.append(f"{site['name']}: Error al verificar - {str(e)}")
        
        return "Resultados de la búsqueda para usuario '" + username + "':\n\n" + "\n".join(results)
    
    @staticmethod
    def search_email(email):
        """Busca información asociada a una dirección de correo electrónico."""
        # Validar formato de email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return f"Formato de correo electrónico inválido: {email}"
        
        try:
            # Extraer el dominio del correo
            domain = email.split('@')[1]
            
            # Verificar si el dominio existe
            try:
                import socket
                socket.gethostbyname(domain)
                domain_exists = True
            except:
                domain_exists = False
            
            # Búsqueda de brechas real sin API
            breach_results = []
            encoded_email = quote_plus(email)
            
            # Buscar en DeHashed (versión pública)
            try:
                dehashed_url = f"https://dehashed.com/search?query={encoded_email}"
                headers = AdvancedSearchTools.get_random_headers()
                response = requests.get(dehashed_url, headers=headers, timeout=10)
                if "appears in the following breaches" in response.text:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    breach_elements = soup.select(".breach-item")
                    if breach_elements:
                        for elem in breach_elements[:5]:  # Limitar a 5 resultados
                            breach_name = elem.select_one(".breach-name")
                            if breach_name:
                                breach_results.append(f"Posible brecha: {breach_name.text.strip()}")
            except Exception:
                pass
                
            # Búsqueda alternativa en IntelligenceX
            try:
                intelx_url = f"https://intelx.io/?s={encoded_email}"
                headers = AdvancedSearchTools.get_random_headers()
                response = requests.get(intelx_url, headers=headers, timeout=10)
                if "data breach" in response.text.lower() or "leaks" in response.text.lower():
                    breach_results.append("Posibles coincidencias en IntelligenceX: " + intelx_url)
            except Exception:
                pass
            
            # Resultados base
            results = [
                f"Dirección: {email}",
                f"Dominio: {domain} ({'Válido' if domain_exists else 'No resuelve'})"
            ]
            
            # Añadir resultados de brechas si existen
            if breach_results:
                results.append("\nPosibles brechas detectadas:")
                results.extend(breach_results)
            else:
                results.append("\nNo se detectaron brechas de datos evidentes en las fuentes consultadas.")
                results.append("Nota: Esta búsqueda no es exhaustiva. Se recomienda verificar en múltiples fuentes.")
            
            # Buscar el dominio en redes sociales
            social_results = []
            social_sites = [
                {"name": "LinkedIn", "url": f"https://www.linkedin.com/company/{domain.split('.')[0]}"},
                {"name": "Twitter", "url": f"https://twitter.com/{domain.split('.')[0]}"},
                {"name": "Facebook", "url": f"https://www.facebook.com/{domain.split('.')[0]}"}
            ]
            
            for site in social_sites:
                try:
                    headers = AdvancedSearchTools.get_random_headers()
                    response = requests.get(site["url"], headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        social_results.append(f"Posible presencia en {site['name']}: {site['url']}")
                        
                except Exception:
                    pass
            
            if social_results:
                results.append("\nPresencia potencial de la organización:")
                results.extend(social_results)
            
            return "\n".join(results)
        
        except Exception as e:
            return f"Error durante la búsqueda de correo electrónico: {str(e)}"
        
    @staticmethod
    def advanced_search(query, engines=None):
        """
        Realiza una búsqueda combinada en múltiples motores de búsqueda y devuelve resultados agregados.
        
        Args:
            query (str): La consulta de búsqueda
            engines (list, optional): Lista de motores a utilizar. Por defecto, usa DuckDuckGo y Google.
                Opciones disponibles: "duckduckgo", "google", "bing", "yandex", "startpage", "baidu", "ecosia"
        """
        if not engines:
            engines = ["google","startpage", "scholar", "yandex", "bing", "news", "baidu", "ecosia","github"]
        
            all_engines = {
            "duckduckgo": AdvancedSearchTools.search_duckduckgo,
            "google": _search_internet,
            "bing": AdvancedSearchTools.search_bing,
            "yandex": AdvancedSearchTools.search_yandex,
            "startpage": AdvancedSearchTools.search_startpage,
            "baidu": AdvancedSearchTools.search_baidu,
            "ecosia": AdvancedSearchTools.search_ecosia,
            "scholar": AdvancedSearchTools.search_scholar,
            "news": AdvancedSearchTools.search_news,
            "archive": AdvancedSearchTools.search_archive
        }
        
        results = []
        for engine in engines:
            if engine.lower() in all_engines:
                try:
                    result = all_engines[engine.lower()](query)
                    results.append(f"=== Resultados de {engine.upper()} ===\n{result}")
                    print("result: ", result)
                    # Esperar un tiempo aleatorio entre búsquedas para evitar detección
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    results.append(f"Error en {engine}: {str(e)}")
            else:
                results.append(f"Motor de búsqueda '{engine}' no reconocido.")
        
        return "\n\n".join(results)
    
    @staticmethod
    def search_github(query):
        """Busca en GitHub repos, código o usuarios relacionados con la consulta."""
        top_results = 5
        encoded_query = quote_plus(query)
        url = f"https://github.com/search?q={encoded_query}"
        
        try:
            headers = AdvancedSearchTools.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='repo-list-item')
            
            if not results:
                # Intentar encontrar resultados con otra estructura
                results = soup.select('.Box-row')
            
            if not results:
                return "No se encontraron resultados para la búsqueda en GitHub."
            
            output = []
            for i, result in enumerate(results[:top_results]):
                name_element = result.select_one('a[data-hydro-click]')
                name = name_element.text.strip() if name_element else "Nombre desconocido"
                
                link = name_element.get('href') if name_element else ""
                full_link = f"https://github.com{link}" if link else ""
                
                description_element = result.select_one('p')
                description = description_element.text.strip() if description_element else "Sin descripción"
                
                # Obtener estrellas, forks, etc.
                stars_element = result.select_one('a[href$="stargazers"]')
                stars = stars_element.text.strip() if stars_element else "0"
                
                language_element = result.select_one('[itemprop="programmingLanguage"]')
                language = language_element.text.strip() if language_element else "No especificado"
                
                updated_element = result.select_one('relative-time')
                updated = updated_element.text.strip() if updated_element else "Fecha desconocida"
                
                result_info = (
                    f"Resultado {i+1}:\n"
                    f"Nombre: {name}\n"
                    f"Enlace: {full_link}\n"
                    f"Descripción: {description}\n"
                    f"Lenguaje principal: {language}\n"
                    f"Estrellas: {stars}\n"
                    f"Última actualización: {updated}\n"
                    "-----------------"
                )
                output.append(result_info)
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error durante la búsqueda en GitHub: {str(e)}"
    

    @staticmethod
    def analyze_website(url):
        """Realiza un análisis rápido de un sitio web, extrayendo metadatos e información básica."""
        try:
            # Asegurar que la URL tenga protocolo
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = AdvancedSearchTools.get_random_headers()
            session = HTMLSession()
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extraer información básica
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Obtener título
            title = soup.title.text.strip() if soup.title else "Sin título"
            
            # Obtener meta descripción
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else "Sin descripción"
            
            # Obtener meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords['content'] if meta_keywords and 'content' in meta_keywords.attrs else "Sin palabras clave"
            
            # Obtener encabezados H1
            h1_tags = [h1.text.strip() for h1 in soup.find_all('h1')]
            h1_text = "\n   - ".join(h1_tags[:5]) if h1_tags else "No hay encabezados H1"
            
            # Obtener enlaces externos e internos
            all_links = soup.find_all('a', href=True)
            
            domain = urlparse(url).netloc
            internal_links = []
            external_links = []
            
            for link in all_links[:30]:
                href = link.get('href')
                if href:
                    if href.startswith(('http://', 'https://')):
                        parsed_link = urlparse(href)
                        if parsed_link.netloc == domain:
                            internal_links.append(href)
                        else:
                            external_links.append(href)
                    elif href.startswith('/'):
                        internal_links.append(f"https://{domain}{href}")
            
            # Obtener información del servidor
            server_info = response.headers.get('Server', 'No especificado')
            content_type = response.headers.get('Content-Type', 'No especificado')
            
            # Crear resumen del análisis
            analysis = f"""
ANÁLISIS RÁPIDO DEL SITIO WEB: {url}
=====================================

Información básica:
- Título: {title}
- Descripción: {description}
- Palabras clave: {keywords}
- Servidor: {server_info}
- Tipo de contenido: {content_type}

Encabezados H1:
{h1_text}

Enlaces encontrados:
- Enlaces internos: {len(internal_links)}
- Enlaces externos: {len(external_links)}

Primeros 5 enlaces externos:
{chr(10).join(external_links[:5]) if external_links else "No hay enlaces externos"}

Información técnica:
- Código de estado: {response.status_code}
- Tamaño de respuesta: {len(response.content)} bytes
- Tiempo de carga: Disponible tras la solicitud
"""
            
            return analysis
            
        except Exception as e:
            return f"Error durante el análisis del sitio web: {str(e)}"