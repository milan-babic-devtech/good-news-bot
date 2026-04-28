import logging
import logging.handlers
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import settings
from bot.db.session import init_db
from bot.jobs.fetch_job import run_fetch
from bot.jobs.score_job import run_score
from bot.jobs.post_job import run_post


def _setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


def _safe(fn):
    def wrapper():
        try:
            fn()
        except Exception:
            logging.getLogger(__name__).exception("Job %s failed", fn.__name__)
    return wrapper


def main() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Good News Bot starting up")

    init_db()

    scheduler = BlockingScheduler(timezone="Europe/Belgrade")

    scheduler.add_job(_safe(run_fetch), IntervalTrigger(hours=2), id="fetch")
    scheduler.add_job(_safe(run_score), IntervalTrigger(hours=2), id="score")
    for hour in [8, 12, 16, 20]:
        scheduler.add_job(
            _safe(run_post),
            CronTrigger(hour=hour, minute=0, timezone="Europe/Belgrade"),
            id=f"post_{hour}",
        )

    # Run immediately on startup
    _safe(run_fetch)()
    _safe(run_score)()

    logger.info("Scheduler started — fetch every 2h, score every 2h, post at 08/12/16/20")
    scheduler.start()


if __name__ == "__main__":
    main()
