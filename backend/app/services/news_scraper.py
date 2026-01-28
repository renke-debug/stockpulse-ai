"""
News scraper using RSS feeds from major financial news sources.
Free alternative to paid news APIs.
"""

import re
from datetime import datetime
from typing import Optional
import feedparser
import json
from pathlib import Path


class NewsItem:
    """Container for a news article."""

    def __init__(
        self,
        title: str,
        source: str,
        url: str,
        published_at: Optional[datetime] = None,
        tickers_mentioned: Optional[list[str]] = None,
    ):
        self.title = title
        self.source = source
        self.url = url
        self.published_at = published_at
        self.tickers_mentioned = tickers_mentioned or []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "tickers_mentioned": self.tickers_mentioned,
        }


# RSS feed URLs for financial news
RSS_FEEDS = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Investing.com": "https://www.investing.com/rss/news.rss",
}

# Load stock tickers for matching
def _load_stock_tickers() -> dict[str, str]:
    """Load ticker -> company name mapping."""
    json_path = Path(__file__).parent.parent.parent / "data" / "stocks_sp100.json"
    try:
        with open(json_path, "r") as f:
            stocks = json.load(f)
        return {s["ticker"]: s["name"] for s in stocks}
    except FileNotFoundError:
        return {}


STOCK_TICKERS = _load_stock_tickers()


def extract_tickers(text: str) -> list[str]:
    """
    Extract stock tickers mentioned in text.

    Looks for:
    - Cashtags like $AAPL
    - Company names from our tracked list
    - Ticker symbols in parentheses like (AAPL)

    Args:
        text: Text to search for ticker mentions

    Returns:
        List of unique ticker symbols found
    """
    found_tickers: set[str] = set()
    text_upper = text.upper()

    # Pattern 1: Cashtags ($AAPL)
    cashtag_pattern = r"\$([A-Z]{1,5})\b"
    for match in re.findall(cashtag_pattern, text_upper):
        if match in STOCK_TICKERS:
            found_tickers.add(match)

    # Pattern 2: Tickers in parentheses (AAPL)
    paren_pattern = r"\(([A-Z]{1,5})\)"
    for match in re.findall(paren_pattern, text_upper):
        if match in STOCK_TICKERS:
            found_tickers.add(match)

    # Pattern 3: Company name mentions
    text_lower = text.lower()
    for ticker, name in STOCK_TICKERS.items():
        # Check for company name (case insensitive)
        name_parts = name.lower().split()
        # Use first significant word (skip "The", "Inc", etc)
        for part in name_parts:
            if len(part) > 3 and part not in ["inc.", "corp.", "company", "corporation", "group", "limited"]:
                if part in text_lower:
                    found_tickers.add(ticker)
                break

    return list(found_tickers)


def parse_feed_date(entry: dict) -> Optional[datetime]:
    """Parse date from feed entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except (TypeError, ValueError):
            pass

    return None


def fetch_news(max_items_per_feed: int = 20) -> list[NewsItem]:
    """
    Fetch news from all RSS feeds.

    Args:
        max_items_per_feed: Maximum items to fetch per feed

    Returns:
        List of NewsItem objects, deduplicated by URL
    """
    all_news: dict[str, NewsItem] = {}  # URL -> NewsItem for deduplication

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:max_items_per_feed]:
                url = entry.get("link", "")
                if not url or url in all_news:
                    continue

                title = entry.get("title", "").strip()
                if not title:
                    continue

                published = parse_feed_date(entry)
                tickers = extract_tickers(title)

                news_item = NewsItem(
                    title=title,
                    source=source_name,
                    url=url,
                    published_at=published,
                    tickers_mentioned=tickers,
                )
                all_news[url] = news_item

        except Exception as e:
            # Log but don't fail on individual feed errors
            print(f"Error fetching {source_name}: {e}")
            continue

    return list(all_news.values())


def fetch_news_for_ticker(ticker: str, max_items: int = 10) -> list[NewsItem]:
    """
    Fetch recent news mentioning a specific ticker.

    Args:
        ticker: Stock ticker symbol
        max_items: Maximum items to return

    Returns:
        List of NewsItem objects mentioning the ticker
    """
    all_news = fetch_news()
    ticker_news = [n for n in all_news if ticker in n.tickers_mentioned]

    # Sort by date, most recent first
    ticker_news.sort(
        key=lambda x: x.published_at or datetime.min,
        reverse=True,
    )

    return ticker_news[:max_items]
