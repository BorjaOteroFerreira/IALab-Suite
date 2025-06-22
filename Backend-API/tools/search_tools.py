import json
import os
import requests
from langchain.tools import tool
from send_to_console import SendToConsole
from langchain_community.document_loaders.chromium import AsyncChromiumLoader  # Assuming Chromium is available
from langchain.document_transformers.html2text import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from requests_html import HTMLSession
from requests_html import HTMLSession
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

class SearchTools:

    @staticmethod
    @tool("Search the internet")
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

    @staticmethod
    @tool("Get IP Information")
    def get_ip_info(ip_address):
        """Fetches geolocation and other information about a given IP address."""

        url = f"https://freeipapi.com/api/json/{ip_address}"

        try:
            # Realizar la solicitud HTTP para obtener la información de la IP
            response = requests.get(url)

            # Verificar que la solicitud fue exitosa
            if response.status_code == 200:
                data = response.json()

                # Devolver la información de la IP en formato de texto
                ip_info = (
                    f"Información de la IP proporcionada:\n"
                    f"Dirección IP: {data.get('ipAddress')}\n"
                    f"Versión de IP: {data.get('ipVersion')}\n"
                    f"Ubicación: {data.get('cityName')}, {data.get('regionName')}, {data.get('countryName')}\n"
                    f"Código de país: {data.get('countryCode')}\n"
                    f"Código postal: {data.get('zipCode')}\n"
                    f"Latitud: {data.get('latitude')}\n"
                    f"Longitud: {data.get('longitude')}\n"
                    f"Continente: {data.get('continent')} ({data.get('continentCode')})\n"
                    f"Moneda: {data.get('currency', {}).get('name')} ({data.get('currency', {}).get('code')})\n"
                    f"Idioma: {data.get('language')}\n"
                    f"Zona horaria: {data.get('timeZone')}\n"
                    f"Proxies detectados: {'Sí' if data.get('isProxy') else 'No'}"
                )
                return data
            else:
                return f"Error al obtener la información de la IP. Código de estado: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return f"Ocurrió un error al intentar obtener los datos: {e}"



