import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional, Dict


async def fetch_page_content(url: str) -> str:
    """Fetch HTML content from a URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return response.text


def is_youtube_url(url: str) -> bool:
    """Check if the URL is a YouTube video."""
    parsed = urlparse(url)
    youtube_domains = ["youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be"]
    if parsed.netloc in youtube_domains:
        return True
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return True
    return False


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
    try:
        html = await fetch_page_content(url)
        return extract_metadata(html, url)
    except Exception as e:
        return {
            "title": None,
            "description": f"Failed to fetch content: {str(e)}",
            "source_type": "other"
        }
