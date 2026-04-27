import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class RssFeed:
    url: str
    name: str


@dataclass
class Settings:
    anthropic_api_key: str
    telegram_bot_token: str
    telegram_channel_id: str
    newsapi_key: str
    gnews_api_key: str
    db_path: Path
    log_level: str
    rss_feeds: list[RssFeed] = field(default_factory=list)
    api_keywords: list[str] = field(default_factory=list)


def load_settings() -> Settings:
    sources_path = BASE_DIR / "sources.yaml"
    with open(sources_path) as f:
        sources = yaml.safe_load(f)

    rss_feeds = [RssFeed(**feed) for feed in sources.get("rss_feeds", [])]
    api_keywords = sources.get("api_keywords", [])

    db_path_raw = os.getenv("DB_PATH", "data/news.db")
    db_path = Path(db_path_raw) if Path(db_path_raw).is_absolute() else BASE_DIR / db_path_raw

    return Settings(
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_channel_id=os.environ["TELEGRAM_CHANNEL_ID"],
        newsapi_key=os.getenv("NEWSAPI_KEY", ""),
        gnews_api_key=os.getenv("GNEWS_API_KEY", ""),
        db_path=db_path,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        rss_feeds=rss_feeds,
        api_keywords=api_keywords,
    )


settings = load_settings()
