"""RSS 뉴스 수집 및 24시간(전날 07:00 KST ~ 당일 07:00 KST) 윈도우 필터링."""
import calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser

KST = ZoneInfo("Asia/Seoul")

FEEDS_BY_CATEGORY = {
    "macro": ["https://www.cnbc.com/id/20910258/device/rss/rss.html"],
    "us_market": ["https://www.cnbc.com/id/10000664/device/rss/rss.html"],
    "bitcoin": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
    ],
}


def get_window_utc(now_kst: datetime = None):
    """(윈도우 시작 UTC, 윈도우 끝 UTC) 반환. 윈도우는 당일 07:00 KST 기준 직전 24시간."""
    if now_kst is None:
        now_kst = datetime.now(KST)
    end_kst = now_kst.replace(hour=7, minute=0, second=0, microsecond=0)
    if now_kst < end_kst:
        end_kst -= timedelta(days=1)
    start_kst = end_kst - timedelta(days=1)
    return start_kst.astimezone(timezone.utc), end_kst.astimezone(timezone.utc)


def fetch_category_items(category: str, start_utc: datetime, end_utc: datetime, limit: int = 5):
    """카테고리의 RSS 피드들에서 윈도우 내 기사를 모아 최신순으로 최대 limit개 반환."""
    items = []
    for url in FEEDS_BY_CATEGORY.get(category, []):
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published = entry.get("published_parsed")
                if not published:
                    continue
                pub_dt = datetime.fromtimestamp(calendar.timegm(published), tz=timezone.utc)
                if start_utc <= pub_dt <= end_utc:
                    items.append(
                        {
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "published": pub_dt,
                        }
                    )
        except Exception:
            continue
    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:limit]
