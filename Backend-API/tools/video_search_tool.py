from typing import List
from pydantic import BaseModel, Field
import requests
from datetime import datetime, timezone, timedelta
import os

from .base_tool import BaseTool, ToolMetadata, ToolCategory


class VideoSearchResult(BaseModel):
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    days_since_published: int


class YoutubeVideoSearchToolInput(BaseModel):
    """Input for YoutubeVideoSearchTool."""
    keyword: str = Field(..., description="The search keyword.")
    max_results: int = Field(5, description="The maximum number of results to return.")


class YoutubeVideoSearchTool(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Búsqueda de vídeos en YouTube",
            description="Busca videos en YouTube basado en palabras clave",
            category=ToolCategory.MEDIA,
            requires_api_key=True,
            api_key_env_var="YOUTUBE_API_KEY",
            usage_example={
                "búsqueda_simple": '{"tool": "youtube_video_search_tool", "query": "tutorial python"}',
                "con_max_results": '{"tool": "youtube_video_search_tool", "query": "noticias tecnología", "max_results": 6}',
                "formatos_soportados": [
                    'query: palabra clave de búsqueda (string)',
                    'max_results: número máximo de vídeos (opcional, int)'
                ]
            }
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Búsqueda de vídeos en YouTube"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta búsqueda de videos en YouTube"""
        max_results = kwargs.get('max_results', 4)
        return self._search_youtube_videos(query, max_results)
    
    def _search_youtube_videos(self, keyword: str, max_results: int = 4):
        """
        Busca videos en YouTube basado en palabras clave.

        Parameters:
            keyword (str): La palabra clave de búsqueda.
            max_results (int, optional): El número máximo de resultados a devolver. Por defecto 4.

        Returns:
            tuple: Una tupla con los resultados y los IDs de videos.
        """
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now()

        # Restar 30 días
        fecha_resta = fecha_actual - timedelta(days=30)

        # Formatear en formato RFC 3339
        fecha_rfc3339 = fecha_resta.replace(microsecond=0).isoformat() + 'Z'
        api_key = os.getenv("YOUTUBE_API_KEY")
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword,
            "maxResults": max_results,
            "type": "video",
            "key": api_key,
            "order": "date",
            "publishedAfter": fecha_rfc3339
        }
        
        try:            
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
        except requests.exceptions.HTTPError as e:
            raise Exception('He superado el limite de consultas en la api de youtube')

        results = []
        ids = []
        for item in items:
            video_id = item["id"]["videoId"]
            ids.append(video_id)
            title = item["snippet"]["title"].replace('|', '-').replace('||', '--')
            channel_id = item["snippet"]["channelId"]
            channel_title = item["snippet"]["channelTitle"]
            publish_date = datetime.fromisoformat(
                item["snippet"]["publishedAt"].replace('Z', '+00:00')).astimezone(timezone.utc)
            days_since_published = (datetime.now(
                timezone.utc) - publish_date).days
            results.append(VideoSearchResult(
                video_id=video_id,
                title=title,
                channel_id=channel_id,
                channel_title=channel_title,
                days_since_published=days_since_published
            ))

        results_str = '\n'.join(str(result) for result in reversed(results))
        if results_str != '':
            print(ids)
            return f'{results_str}', ids  # Devolver resultado e IDs
        else: 
            return f'', []  # Devolver cadena vacía y lista vacía de IDs

    # Mantener el método estático original para compatibilidad con LangChain si es necesario
    @staticmethod
    def run(keyword: str, max_results: int = 4) -> List[VideoSearchResult]:
        """
        Método estático legacy para compatibilidad con LangChain.
        No se usa en el nuevo sistema de registry.
        """
        tool_instance = YoutubeVideoSearchTool()
        return tool_instance._search_youtube_videos(keyword, max_results)
