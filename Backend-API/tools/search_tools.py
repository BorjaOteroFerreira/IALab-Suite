import json
import os
import requests
from send_to_console import SendToConsole
from langchain_community.document_loaders.chromium import AsyncChromiumLoader  
from langchain_community.document_transformers import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from requests_html import HTMLSession
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

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
            response.raise_for_status()  # Raise an exception for non-2xx status codes

            if 'organic' not in response.json():
                return "Sorry, I couldn't find anything relevant."

            results = response.json()['organic']
            string = []
            for result in results[:top_result_to_return]:
                title = result['title'].replace('|', '-').replace('||', '--')
                snippet = result['snippet'].replace('|', '-').replace('||', '--')

                try:
                    link = result['link']
                    # Extract content using requests-html
                    content = SearchTools.extract_relevant_content(link)

                    string.append('\n'.join([
                        f"Title: {title}", f"Link: {link}",
                        f"Snippet: {snippet}", f"Content: {content}",
                        f"traduce todo a español.",
                        "\n-----------------"
                    ]))
                except KeyError:
                    pass  # Skip links with missing information

            return '\n'.join(string)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results: {e}")
            return "An error occurred while searching the internet."

    @staticmethod
    def extract_content(url):
        session = HTMLSession()
        try:
            response = session.get(url)
            response.raise_for_status()
            # Extract all text elements from the page
            text_elements = response.html.find('body')[0].xpath('//p|//h1|//h2|//h3')
            content = '\n'.join([element.text for element in text_elements])
            return content if content else "Content extraction failed."
        except requests.exceptions.RequestException as e:
            print(f"Error extracting content: {e}")
            return "Content extraction failed."
    
    @staticmethod
    def extract_relevant_content(url):
        try:
            parser = HtmlParser.from_url(url, Tokenizer('spanish'))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 1)  # Extract a single sentence as summary
            return str(summary[0]) if summary else "Content extraction failed."
        except Exception as e:
            print(f"Error extracting content: {e}")
            return "Content extraction failed."



