import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from bot.db.session import get_session
from bot.db.models import NewsItem
from bot.scorer import score_items

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10
_MAX_ITEMS = 50
_MAX_AGE_HOURS = 48


def run_score() -> None:
    logger.info("Score job started")
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=_MAX_AGE_HOURS)

    with get_session() as session:
        stmt = (
            select(NewsItem)
            .where(NewsItem.positivity_score.is_(None))
            .where(NewsItem.fetched_at >= cutoff)
            .limit(_MAX_ITEMS)
        )
        items = list(session.scalars(stmt))

        if not items:
            logger.info("Score job: no unscored items found")
            return

        logger.info("Score job: scoring %d items", len(items))
        scored = 0

        for i in range(0, len(items), _BATCH_SIZE):
            batch = items[i: i + _BATCH_SIZE]
            results = score_items(batch)
            for item_id, score, reason, scored_at in results:
                record = session.get(NewsItem, item_id)
                if record:
                    record.positivity_score = score
                    record.claude_reasoning = reason
                    record.scored_at = scored_at
                    scored += 1

        session.commit()

    logger.info("Score job done — scored %d items", scored)
