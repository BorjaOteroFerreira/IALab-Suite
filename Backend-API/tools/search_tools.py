import json
import os
import requests
from requests_html import HTMLSession
from app.core.socket_handler import SocketResponseHandler
from langchain_community.document_loaders.chromium import AsyncChromiumLoader  
from langchain_community.document_transformers import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

from .base_tool import BaseTool, ToolMetadata, ToolCategory
from urllib.parse import urlparse

class SearchTools(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="buscar_en_internet",
            description="Busca información en internet sobre un tema específico",
            category=ToolCategory.SEARCH,
            requires_api_key=True,
            api_key_env_var="SERPER_API_KEY"
        )

    @classmethod
    def get_tool_name(cls) -> str:
        return "buscar_en_internet"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta búsqueda en internet"""
        return SearchTools.search_internet(query)

    @staticmethod
    def search_internet(query):
        """Searches the internet for a given topic and returns relevant results."""

        top_result_to_return = 5
        url = "https://google.serper.dev/search"
        payload = {"q": query, 'order': 'date'}
        headers = {
            'X-API-KEY': os.environ.get('SERPER_API_KEY'),
            'content-type': 'application/json'
        }
        try:
            session = HTMLSession()
            response = session.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            if 'organic' not in data or not data['organic']:
                return "Sorry, no se encontraron resultados relevantes."

            string = []
            for result in data['organic'][:top_result_to_return]:
                title = result.get('title', '').replace('|', '-').replace('||', '--')
                snippet = result.get('snippet', '').replace('|', '-').replace('||', '--')
                link = result.get('link')
                if not link:
                    continue

                content = SearchTools.extract_content(link)
                string.append('\n'.join([
                    f"Title: {title}",
                    f"Link: {link}",
                    f"Snippet: {snippet}",
                    f"Content: {content}",
                    "\n-----------------"
                ]))

            return '\n'.join(string)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results: {e}")
            return "An error occurred while searching the internet."

    @staticmethod
    def extract_relevant_content_from_text(text):
        try:
            parser = HtmlParser.from_string(text, Tokenizer('spanish'))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 1)  # Una sola frase
            return str(summary[0]) if summary else ""
        except Exception as e:
            print(f"Error extracting content: {e}")
            return ""

    @staticmethod
    def extract_content(url):
        # No incluir URLs de más de 150 caracteres
        if len(url) > 150:
            return "Content extraction failed."

        session = HTMLSession()
        try:
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
            resumen = SearchTools.extract_relevant_content_from_text(content)

            return f"Imágenes: {md_imgs}\nResumen: {resumen}" if content or md_imgs else "Content extraction failed."

        except requests.exceptions.RequestException as e:
            print(f"Error extracting content: {e}")
            return "Content extraction failed."

    @staticmethod
    def extract_relevant_content(url):
        try:
            parser = HtmlParser.from_url(url, Tokenizer('spanish'))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 1)  # Extract a single sentence as summary
            return str(summary[0]) if summary else ""
        except Exception as e:
            print(f"Error extracting content: {e}")
            return "Content extraction failed."