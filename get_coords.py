import requests
from bs4 import BeautifulSoup

def get_wiki_coord(name: str) -> str:
    # Replace spaces with underscores to match Wikipedia URL format
    name = name.replace(' ', '_')

    # Get the Wikipedia page
    url = f"https://en.wikipedia.org/wiki/{name}"
    response = requests.get(url)

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the span with class "geo"
    lat_tag = soup.find('span', {'class': 'latitude'})
    lon_tag = soup.find('span', {'class': 'longitude'})

    if lat_tag and lon_tag:
        # If both tags are found, return their contents
        return lat_tag.text, lon_tag.text
    else:
        # If no geo tag is found, return an error message
        return False
    
def get_searxng_coord(name: str):
    name = name.replace(' ', '+')
    url = "https://search.ericdevelops.com/search"
    params = {
        'q': name,
        'format': 'json'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        return f"Error: Received status code {response.status_code}"