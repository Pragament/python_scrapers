from config import SERPAPI_API_KEY
import requests

def fetch_gif_urls(topic, num_results=2):
    search_query = f"{topic} concept animation GIF site:tenor.com OR site:giphy.com"

    params = {
        "engine": "google",
        "q": search_query,
        "tbm": "isch",
        "api_key": SERPAPI_API_KEY,
        "ijn": 0
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        results = response.json()
        gifs = [img["original"] for img in results.get("images_results", []) if img["original"].endswith(".gif")]
        return gifs[:num_results]
    except Exception as e:
        print(f"[ERROR] Failed to fetch for '{topic}': {e}")
        return []
