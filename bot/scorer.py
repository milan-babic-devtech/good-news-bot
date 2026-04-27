import json
import logging
from datetime import datetime, timezone

import anthropic

from bot.config import settings

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
_MODEL = "claude-haiku-4-5"


def score_batch(items: list[dict]) -> list[dict]:
    """
    items: list of {"id": int, "title": str}
    Returns list of {"id": int, "score": float, "reason": str}
    """
    headlines = "\n".join(f"{i}. {item['title']}" for i, item in enumerate(items))
    prompt = (
        "Rate each headline for positivity on a scale of 1–10 "
        "(1=tragedy/disaster, 5=neutral, 10=breakthrough/rescue/major progress). "
        "Return a JSON array only — no explanation outside the JSON.\n"
        'Format: [{"id":0,"score":8,"reason":"..."}]\n\n'
        f"Headlines:\n{headlines}"
    )

    message = _client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    results = json.loads(raw)
    return results


def score_items(db_items) -> list[tuple]:
    """
    db_items: list of NewsItem ORM objects
    Returns list of (id, score, reason, scored_at)
    """
    batch_input = [{"id": i, "title": item.title} for i, item in enumerate(db_items)]
    try:
        results = score_batch(batch_input)
    except Exception as e:
        logger.error("Claude scoring failed: %s", e)
        return []

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    output = []
    for r in results:
        idx = r["id"]
        if idx >= len(db_items):
            continue
        db_item = db_items[idx]
        output.append((db_item.id, float(r["score"]), r.get("reason", ""), now))
    return output
