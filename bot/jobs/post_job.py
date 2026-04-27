import logging
from datetime import datetime, timezone

from sqlalchemy import select

from bot.db.session import get_session
from bot.db.models import NewsItem
from bot.poster import send_item

logger = logging.getLogger(__name__)

_MIN_SCORE = 7.0


def run_post() -> None:
    logger.info("Post job started")

    with get_session() as session:
        stmt = (
            select(NewsItem)
            .where(NewsItem.positivity_score >= _MIN_SCORE)
            .where(NewsItem.is_posted.is_(False))
            .order_by(NewsItem.positivity_score.desc(), NewsItem.fetched_at.desc())
            .limit(5)
        )
        candidates = list(session.scalars(stmt))

        if not candidates:
            logger.warning("Post job: no eligible items (score >= %s, unposted)", _MIN_SCORE)
            return

        item = candidates[0]
        sent = send_item(item)

        if sent:
            item.is_posted = True
            item.posted_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.commit()
            logger.info("Post job done — posted item id=%d", item.id)
        else:
            logger.error("Post job: send failed, item not marked as posted")
