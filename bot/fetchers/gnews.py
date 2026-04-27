import logging
from datetime import datetime

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://gnews.io/api/v4/search"


def fetch_gnews() -> list[dict]:
    if not settings.gnews_api_key:
        logger.debug("GNews API key not set, skipping")
        return []

    items = []
    for keyword in settings.api_keywords:
        try:
            resp = httpx.get(
                _BASE_URL,
                params={
                    "q": keyword,
                    "lang": "en",
                    "max": 10,
                    "apikey": settings.gnews_api_key,
                },
                timeout=15,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            for article in articles:
                url = (article.get("url") or "").strip()
                title = (article.get("title") or "").strip()
                if not url or not title:
                    continue
                published_at = None
                raw_date = article.get("publishedAt")
                if raw_date:
                    try:
                        published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        pass
                items.append({
                    "url": url,
                    "title": title,
                    "summary": (article.get("description") or "")[:1000] or None,
                    "source_name": f"GNews:{article.get('source', {}).get('name', 'unknown')}",
                    "published_at": published_at,
                })
        except Exception as e:
            logger.warning("GNews fetch failed for '%s': %s", keyword, e)

    return items
