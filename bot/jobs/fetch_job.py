import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from bot.db.session import get_session
from bot.db.models import NewsItem
from bot.fetchers.rss import fetch_rss
from bot.fetchers.newsapi import fetch_newsapi
from bot.fetchers.gnews import fetch_gnews

logger = logging.getLogger(__name__)


def run_fetch() -> None:
    logger.info("Fetch job started")
    all_items = fetch_rss() + fetch_newsapi() + fetch_gnews()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    inserted = 0

    with get_session() as session:
        for item in all_items:
            record = NewsItem(
                url=item["url"],
                title=item["title"],
                summary=item.get("summary"),
                source_name=item["source_name"],
                published_at=item.get("published_at"),
                fetched_at=now,
            )
            try:
                session.add(record)
                session.flush()
                inserted += 1
            except IntegrityError:
                session.rollback()
            except Exception as e:
                session.rollback()
                logger.warning("Insert failed for %s: %s", item.get("url"), e)

        session.commit()

    logger.info("Fetch job done — fetched %d items, inserted %d new", len(all_items), inserted)
