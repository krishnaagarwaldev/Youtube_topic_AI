"""
youtube_fetcher.py
Fetches tutorial videos from YouTube Data API v3 for a given topic.
Each search costs 100 quota units. Free tier = 10,000 units/day → 100 searches/day.
"""

import os
import requests


YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise ValueError("YOUTUBE_API_KEY not set. Add it to your .env file.")
    return key


def fetch_videos(topic: str, max_results: int = 3) -> list[dict]:
    """
    Search YouTube for tutorial videos on the given topic.

    Returns a list of dicts:
      {
        "title":     str,
        "url":       str,   # full watch URL
        "thumbnail": str,   # thumbnail image URL
        "channel":   str,
      }
    """
    query = f"{topic} Class 10 CBSE tutorial"

    params = {
        "key":         _api_key(),
        "q":           query,
        "part":        "snippet",
        "type":        "video",
        "maxResults":  max_results,
        "relevanceLanguage": "en",
        "videoDuration": "medium",   # 4–20 min — avoids shorts and hour-long lectures
    }

    try:
        resp = requests.get(YT_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return [{"title": f"Could not fetch videos: {e}", "url": "", "thumbnail": "", "channel": ""}]

    videos = []
    for item in data.get("items", []):
        vid_id  = item["id"].get("videoId", "")
        snippet = item.get("snippet", {})
        videos.append({
            "title":     snippet.get("title", "No title"),
            "url":       f"https://www.youtube.com/watch?v={vid_id}",
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "channel":   snippet.get("channelTitle", ""),
        })
    return videos


def fetch_videos_for_topics(topics: list[dict], max_per_topic: int = 3) -> list[dict]:
    """
    Fetch videos for every topic in the list.
    Returns the same list with a 'videos' key added to each item.
    """
    enriched = []
    for item in topics:
        topic_name = item.get("topic", "")
        videos = fetch_videos(topic_name, max_results=max_per_topic)
        enriched.append({**item, "videos": videos})
    return enriched
