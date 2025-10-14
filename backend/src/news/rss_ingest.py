from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

import feedparser


@dataclass
class NewsItem:
    source: str
    title: str
    link: str
    published: datetime
    summary: str


DEFAULT_FEEDS = [
    (
        "Binance Announcements",
        "https://www.binance.com/en/support/announcement/c-48?navId=48&hl=en&rss=1",
    ),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("SEC Calendar", "https://www.sec.gov/rss/news/press.xml"),
]


def parse_feed(url: str, source_name: str) -> list[NewsItem]:
    parsed = feedparser.parse(url)
    items: list[NewsItem] = []
    for e in parsed.entries:
        published = None
        if getattr(e, "published_parsed", None):
            published = datetime(*e.published_parsed[:6])
        else:
            published = datetime.utcnow()
        items.append(
            NewsItem(
                source=source_name,
                title=getattr(e, "title", ""),
                link=getattr(e, "link", ""),
                published=published,
                summary=getattr(e, "summary", ""),
            )
        )
    return items


def fetch_all(feeds: Iterable[tuple[str, str]] = DEFAULT_FEEDS) -> list[NewsItem]:
    out: list[NewsItem] = []
    for name, url in feeds:
        out.extend(parse_feed(url, name))
    return out
