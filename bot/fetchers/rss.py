import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from bot.config import settings

logger = logging.getLogger(__name__)


def _parse_date(entry) -> datetime | None:
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=None)
            except Exception:
                pass
    return None


def fetch_rss() -> list[dict]:
    items = []
    for feed_cfg in settings.rss_feeds:
        try:
            feed = feedparser.parse(feed_cfg.url)
            for entry in feed.entries:
                url = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                if not url or not title:
                    continue
                summary = entry.get("summary", "") or entry.get("description", "")
                items.append({
                    "url": url,
                    "title": title,
                    "summary": summary[:1000] if summary else None,
                    "source_name": feed_cfg.name,
                    "published_at": _parse_date(entry),
                })
            logger.debug("RSS %s: %d entries", feed_cfg.name, len(feed.entries))
        except Exception as e:
            logger.warning("RSS fetch failed for %s: %s", feed_cfg.url, e)
    return items
