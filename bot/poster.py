import asyncio
import logging
from html.parser import HTMLParser

from telegram import Bot
from telegram.constants import ParseMode

from bot.config import settings

logger = logging.getLogger(__name__)

_bot = Bot(token=settings.telegram_bot_token)


class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts).strip()


def _strip_html(text: str) -> str:
    parser = _StripHTML()
    parser.feed(text)
    return parser.get_text()


def _format_message(item) -> str:
    summary = _strip_html(item.summary or "").strip()
    if len(summary) > 300:
        summary = summary[:297] + "..."
    parts = [f"<b>{item.title}</b>"]
    if summary:
        parts.append(summary)
    parts.append(f'<a href="{item.url}">Read more</a>')
    return "\n\n".join(parts)


def send_item(item) -> bool:
    text = _format_message(item)
    try:
        asyncio.run(
            _bot.send_message(
                chat_id=settings.telegram_channel_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        )
        logger.info("Posted to Telegram: %s", item.title[:80])
        return True
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False
