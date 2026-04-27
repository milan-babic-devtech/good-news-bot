import logging
from datetime import datetime, timezone

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://newsapi.org/v2/everything"


def fetch_newsapi() -> list[dict]:
    if not settings.newsapi_key:
        logger.debug("NewsAPI key not set, skipping")
        return []

    items = []
    for keyword in settings.api_keywords:
        try:
            resp = httpx.get(
                _BASE_URL,
                params={
                    "q": keyword,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                    "apiKey": settings.newsapi_key,
                },
                timeout=15,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            for article in articles:
                url = (article.get("url") or "").strip()
                title = (article.get("title") or "").strip()
                if not url or not title or url == "https://removed.com":
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
                    "source_name": f"NewsAPI:{article.get('source', {}).get('name', 'unknown')}",
                    "published_at": published_at,
                })
        except Exception as e:
            logger.warning("NewsAPI fetch failed for '%s': %s", keyword, e)

    return items
