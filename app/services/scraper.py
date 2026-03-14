import os
import httpx
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
USE_MOCK_EXTERNAL = os.getenv("USE_MOCK_EXTERNAL", "false").lower() == "true"


async def fetch_page_content(url: str) -> str:
    """Fetch HTML content from a URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return response.text


def is_youtube_url(url: str) -> bool:
    """Check if the URL is a YouTube video."""
    parsed = urlparse(url)
    youtube_domains = ["youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be", "m.youtube.com"]
    if parsed.netloc in youtube_domains:
        return True
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return True
    return False


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    parsed = urlparse(url)

    # Handle youtu.be short links
    if parsed.netloc in ["youtu.be", "www.youtu.be"]:
        return parsed.path.lstrip("/")

    # Handle youtube.com/watch?v= links
    if parsed.netloc in ["youtube.com", "www.youtube.com", "m.youtube.com"]:
        query = parse_qs(parsed.query)
        if "v" in query:
            return query["v"][0]

    return None


async def fetch_youtube_metadata(url: str) -> Optional[Dict[str, Optional[str]]]:
    """Fetch YouTube video metadata using oEmbed API."""
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None

    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(oembed_url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title"),
                    "description": None,  # oEmbed doesn't provide description
                    "source_type": "youtube"
                }
    except Exception:
        pass

    return None


async def fetch_youtube_data_api(url: str) -> Optional[Dict[str, Optional[str]]]:
    """Fetch YouTube video metadata using YouTube Data API v3."""
    if not YOUTUBE_API_KEY:
        if USE_MOCK_EXTERNAL:
            logger.info(f"[MOCK] YouTube API key not set, returning mock data for {url}")
            return {
                "title": "[Mock] Sample YouTube Video Title",
                "description": "[Mock] This is a sample video description. In production, this would come from YouTube Data API.",
                "source_type": "youtube"
            }
        return None

    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None

    api_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    snippet = items[0].get("snippet", {})
                    return {
                        "title": snippet.get("title"),
                        "description": snippet.get("description"),
                        "source_type": "youtube"
                    }
    except Exception as e:
        logger.error(f"Error fetching from YouTube API: {str(e)}")
        pass

    return None


def extract_metadata(html: str, url: str) -> Dict[str, Optional[str]]:
    """Extract metadata from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    metadata = {
        "title": None,
        "description": None,
        "source_type": "youtube" if is_youtube_url(url) else "article"
    }

    # Try to get title
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.get_text().strip()

    # Try OG title first
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        metadata["title"] = og_title["content"].strip()

    # Try to get description
    description = None

    # Try OG description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        description = og_desc["content"].strip()

    # Try meta description
    if not description:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

    # Try Twitter description
    if not description:
        twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            description = twitter_desc["content"].strip()

    # For YouTube, try to get more content
    if is_youtube_url(url) and not description:
        # Look for YouTube specific elements
        yt_description = soup.find("meta", attrs={"name": "description"})
        if yt_description and yt_description.get("content"):
            description = yt_description["content"].strip()

    metadata["description"] = description

    return metadata


async def scrape_url(url: str) -> Dict[str, Optional[str]]:
    """Main function to scrape a URL and extract metadata."""
    result = {
        "title": None,
        "description": None,
        "source_type": "other"
    }

    # For YouTube videos
    if is_youtube_url(url):
        result["source_type"] = "youtube"

        # Try YouTube Data API first (best source for description)
        yt_api_data = await fetch_youtube_data_api(url)
        if yt_api_data:
            result["title"] = yt_api_data.get("title")
            result["description"] = yt_api_data.get("description")
            return result

        # Fallback to oEmbed for title
        yt_metadata = await fetch_youtube_metadata(url)
        if yt_metadata and yt_metadata.get("title"):
            result["title"] = yt_metadata["title"]

        # Try HTML scraping for description as last resort
        try:
            html = await fetch_page_content(url)
            html_metadata = extract_metadata(html, url)
            if not result["title"] and html_metadata.get("title"):
                result["title"] = html_metadata["title"]
            if html_metadata.get("description"):
                result["description"] = html_metadata["description"]
        except Exception:
            pass

        return result

    # For non-YouTube URLs, use HTML scraping
    try:
        html = await fetch_page_content(url)
        html_metadata = extract_metadata(html, url)
        result["title"] = html_metadata.get("title")
        result["description"] = html_metadata.get("description")
        result["source_type"] = html_metadata.get("source_type", "other")
    except Exception as e:
        result["description"] = f"Failed to fetch content: {str(e)}"

    return result
