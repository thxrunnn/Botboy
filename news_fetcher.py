"""
==============================================================
 news_fetcher.py — Fetch latest trending news headlines
 Sources: NewsAPI | Filters: India, TN, Cinema, IPL
==============================================================
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── File to track already-posted headlines ───────────────────
POSTED_CACHE = "logs/posted_headlines.json"

# ── News topics to search ────────────────────────────────────
SEARCH_QUERIES = [
    "Tamil Nadu",
    "Chennai",
    "IPL cricket",
    "Kollywood cinema",
    "India trending",
    "Tamil politics",
    "South India news",
    "CSK",
    "Rajinikanth OR Vijay OR Ajith",
    "Tamil entertainment",
]


def _load_posted_cache() -> set:
    """Load the set of already-posted headline titles."""
    try:
        with open(POSTED_CACHE, "r") as f:
            data = json.load(f)
        return set(data.get("headlines", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_posted_cache(cache: set):
    """Save updated posted headlines cache (keep last 500)."""
    os.makedirs("logs", exist_ok=True)
    limited = list(cache)[-500:]          # keep last 500 to avoid unlimited growth
    with open(POSTED_CACHE, "w") as f:
        json.dump({"headlines": limited}, f, indent=2)


def fetch_news_newsapi() -> list[dict]:
    """
    Fetch headlines using NewsAPI.org.
    Returns list of article dicts.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY not set — skipping NewsAPI fetch")
        return []

    articles = []
    base_url = "https://newsapi.org/v2/everything"
    yesterday = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")

    for query in SEARCH_QUERIES[:5]:          # limit to 5 queries to save quota
        try:
            params = {
                "q": query,
                "from": yesterday,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 5,
                "apiKey": api_key,
            }
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for art in data.get("articles", []):
                if art.get("title") and art["title"] != "[Removed]":
                    articles.append({
                        "title":       art.get("title", ""),
                        "description": art.get("description", ""),
                        "url":         art.get("url", ""),
                        "source":      art.get("source", {}).get("name", "Unknown"),
                        "publishedAt": art.get("publishedAt", ""),
                        "urlToImage":  art.get("urlToImage", ""),
                        "query":       query,
                    })
        except requests.RequestException as e:
            logger.error(f"NewsAPI fetch error for '{query}': {e}")

    logger.info(f"NewsAPI returned {len(articles)} raw articles")
    return articles


def fetch_news_gnews() -> list[dict]:
    """
    Fallback: Fetch headlines using GNews API.
    Returns list of article dicts.
    """
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        logger.warning("GNEWS_API_KEY not set — skipping GNews fetch")
        return []

    articles = []
    base_url = "https://gnews.io/api/v4/search"
    queries = ["Tamil Nadu news", "IPL cricket", "Kollywood", "Chennai"]

    for query in queries:
        try:
            params = {
                "q":        query,
                "lang":     "en",
                "country":  "in",
                "max":      5,
                "apikey":   api_key,
            }
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for art in data.get("articles", []):
                articles.append({
                    "title":       art.get("title", ""),
                    "description": art.get("description", ""),
                    "url":         art.get("url", ""),
                    "source":      art.get("source", {}).get("name", "Unknown"),
                    "publishedAt": art.get("publishedAt", ""),
                    "urlToImage":  art.get("image", ""),
                    "query":       query,
                })
        except requests.RequestException as e:
            logger.error(f"GNews fetch error for '{query}': {e}")

    logger.info(f"GNews returned {len(articles)} raw articles")
    return articles


def _deduplicate(articles: list[dict], posted: set) -> list[dict]:
    """
    Remove:
    1. Already-posted headlines (from local cache)
    2. Duplicate titles within current batch
    """
    seen_titles = set()
    fresh = []

    for art in articles:
        title = art.get("title", "").strip()
        if not title:
            continue
        if title in posted:
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        fresh.append(art)

    logger.info(f"After dedup: {len(fresh)} fresh articles")
    return fresh


def _score_article(article: dict) -> int:
    """
    Score article relevance (higher = post sooner).
    Prioritizes: Tamil/Chennai/IPL keywords.
    """
    score = 0
    text = f"{article['title']} {article['description']}".lower()

    priority_keywords = [
        "tamil", "chennai", "csk", "ipl", "kollywood",
        "rajinikanth", "vijay", "ajith", "thalapathy",
        "suriya", "nayanthara", "cricket", "t20",
    ]
    for kw in priority_keywords:
        if kw in text:
            score += 2

    boost_keywords = ["breaking", "exclusive", "just in", "alert", "update"]
    for kw in boost_keywords:
        if kw in text:
            score += 1

    # Prefer articles with images
    if article.get("urlToImage"):
        score += 1

    return score


def get_fresh_articles(limit: int = 3) -> list[dict]:
    """
    Main function: fetch, dedup, rank, and return top fresh articles.
    Also marks them as posted in the local cache.
    """
    posted = _load_posted_cache()

    # Gather from both sources
    all_articles = fetch_news_newsapi() + fetch_news_gnews()

    if not all_articles:
        logger.warning("No articles fetched from any source!")
        return []

    fresh = _deduplicate(all_articles, posted)
    fresh.sort(key=_score_article, reverse=True)   # best first

    chosen = fresh[:limit]

    # Mark chosen as posted
    for art in chosen:
        posted.add(art["title"])
    _save_posted_cache(posted)

    logger.info(f"Returning {len(chosen)} articles to process")
    return chosen


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    import pprint
    articles = get_fresh_articles(limit=2)
    pprint.pprint(articles)
