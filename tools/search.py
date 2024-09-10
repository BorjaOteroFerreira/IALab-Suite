import json
import os
import requests
from langchain.tools import tool
from pruebas.send_to_console import SendToConsole
class SearchTools():

  @tool("Search the internet")
  def search_internet(query):
    """Useful to search the internet
    about a a given topic and return relevant results"""
    top_result_to_return = 5
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, 'order':'date'})
    headers = {
        'X-API-KEY': os.environ['SERPER_API_KEY'],
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    # check if there is an organic key
    if 'organic' not in response.json():
      return "Sorry, I couldn't find anything about that, there could be an error with you serper api key."
    else:
      results = response.json()['organic']
      string = []
      for result in results[:top_result_to_return]:
        title = result['title'].replace('|', '-').replace('||', '--')
        snippet = result['snippet'].replace('|', '-').replace('||', '--')
        try:
          string.append('\n'.join([
              f"Title: {title}", f"Link: {result['link']}",
              f"Snippet: {snippet}", "\n-----------------"
          ]))
        except KeyError:
          next

      return '\n'.join(string)
