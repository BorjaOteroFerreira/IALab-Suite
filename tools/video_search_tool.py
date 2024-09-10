from typing import List
from pydantic import BaseModel, Field
from langchain.tools import tool
import requests
from datetime import datetime, timezone,timedelta
import os



class VideoSearchResult(BaseModel):
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    days_since_published: int

class YoutubeVideoSearchToolInput(BaseModel):
    """Input for YoutubeVideoSearchTool."""
    keyword: str = Field(..., description="The search keyword.")
    max_results: int = Field(
        5, description="The maximum number of results to return.")

class YoutubeVideoSearchTool:
    @staticmethod
    @tool("Search YouTube Videos")
    def run(keyword: str, max_results: int = 4) -> List[VideoSearchResult]:
        """
        Searches YouTube videos based on a keyword and returns a list of video search results.

        Parameters:
            keyword (str): The search keyword.
            max_results (int, optional): The maximum number of results to return. Defaults to 5.

        Returns:
            List[VideoSearchResult]: A list of video search results.
        """


        # Obtener la fecha y hora actual
        fecha_actual = datetime.now()

        # Restar tres días
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
            "publishedAfter" : fecha_rfc3339
        }
        try: 

            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
        except requests.exceptions.HTTPError as e:
            raise 'He superado el limite de consultas en la api de youtube'

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
            #instruccion =f' \nlos videos de youtube debes mostrarlos en este formaro:\n<div class="widget-youtube"><iframe width="590" height="345" src="https://www.youtube.com/embed/idVideo" frameborder="0" allow=" encrypted-media; picture-in-picture" allowfullscreen></iframe></div><br>\n\n'

            return f'{results_str}' ,ids#{instruccion}' , ids
        else: 
            return f''
