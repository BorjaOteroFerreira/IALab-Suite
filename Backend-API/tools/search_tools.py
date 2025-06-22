import json
import os
import requests
from langchain.tools import tool
from send_to_console import SendToConsole
from langchain_community.document_loaders.chromium import AsyncChromiumLoader
from langchain.document_transformers.html2text import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from requests_html import HTMLSession

from .base_tool import BaseTool, ToolMetadata, ToolCategory

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

            if 'organic' not in response.json():
                return "Sorry, I couldn't find anything relevant."

            results = response.json()['organic']
            string = []
            for result in results[:top_result_to_return]:
                title = result['title'].replace('|', '-').replace('||', '--')
                snippet = result['snippet'].replace('|', '-').replace('||', '--')

                try:
                    link = result['link']
                    # Use simple content extraction to avoid warnings
                    content = SearchTools.extract_simple_content(link)

                    string.append('\n'.join([
                        f"Title: {title}", f"Link: {link}",
                        f"Snippet: {snippet}", f"Content: {content}",
                        f"traduce todo a español.",
                        "\n-----------------"
                    ]))
                except KeyError:
                    pass

            return '\n'.join(string)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results: {e}")
            return "An error occurred while searching the internet."

    @staticmethod
    def extract_simple_content(url):
        """Extrae contenido simple de una URL evitando warnings"""
        session = HTMLSession()
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            # Buscar elementos de texto principales
            text_elements = response.html.find('p, h1, h2, h3')
            content_parts = []
            
            for element in text_elements[:5]:  # Limitar a los primeros 5 elementos
                text = element.text.strip()
                if text and len(text) > 20:  # Solo textos significativos
                    content_parts.append(text)
            
            if content_parts:
                return ' '.join(content_parts)[:500] + '...'  # Limitar longitud
            else:
                return "Content extraction failed."
                
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return "Content extraction failed."

    @staticmethod
    def extract_content(url):
        """Método de compatibilidad"""
        return SearchTools.extract_simple_content(url)
    
    @staticmethod
    def extract_relevant_content(url):
        """Método de compatibilidad"""
        return SearchTools.extract_simple_content(url)
