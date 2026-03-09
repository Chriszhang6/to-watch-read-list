import os
from typing import Optional
import google.generativeai as genai


def get_gemini_client():
    """Configure and return Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')


async def generate_summary(title: Optional[str], description: Optional[str], source_type: str) -> str:
    """Generate a concise summary using Gemini API."""
    if not title and not description:
        return "No content available for summary."

    # Prepare the content for summarization
    content_parts = []
    if title:
        content_parts.append(f"Title: {title}")
    if description:
        content_parts.append(f"Description: {description}")

    content = "\n".join(content_parts)

    source_context = {
        "youtube": "YouTube video",
        "article": "article or blog post",
        "other": "web content"
    }.get(source_type, "web content")

    prompt = f"""Please provide a very concise summary (under 100 Chinese characters or 80 English words) for this {source_context}.
Focus on what the content is about and its main topic.

{content}

Summary:"""

    try:
        model = get_gemini_client()
        response = model.generate_content(prompt)
        summary = response.text.strip()

        # Limit summary length
        if len(summary) > 200:
            summary = summary[:197] + "..."

        return summary
    except Exception as e:
        # Fallback to description if API fails
        if description:
            return description[:150] + "..." if len(description) > 150 else description
        return f"Summary generation failed: {str(e)}"
