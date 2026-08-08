import difflib
import logging
import os
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from dotenv import load_dotenv

from app.schemas.news import NewsCategory, NewsSentiment
from app.services.stock_service import StockDataUnavailable, StockNotFound

logger = logging.getLogger("finsight.news_service")

load_dotenv()

FINNHUB_URL = "https://finnhub.io/api/v1/company-news"
SOURCE_NAME = "Finnhub"
LOOKBACK_DAYS = 30

_CATEGORY_KEYWORDS: dict[NewsCategory, tuple[str, ...]] = {
    NewsCategory.EARNINGS: (
        "earnings",
        "revenue",
        "profit",
        "eps",
        "quarter",
        "guidance",
        "forecast",
    ),
    NewsCategory.PRODUCT: (
        "product",
        "launch",
        "chip",
        "ai",
        "platform",
        "model",
        "device",
    ),
    NewsCategory.REGULATION: (
        "regulation",
        "regulator",
        "antitrust",
        "lawsuit",
        "court",
        "compliance",
    ),
    NewsCategory.MANAGEMENT: (
        "ceo",
        "cfo",
        "executive",
        "management",
        "appoint",
        "resign",
    ),
    NewsCategory.SUPPLY_CHAIN: (
        "supply",
        "supplier",
        "factory",
        "manufacturing",
        "shipment",
        "inventory",
    ),
    NewsCategory.MACROECONOMICS: (
        "fed",
        "interest rate",
        "inflation",
        "jobs",
        "economy",
        "gdp",
    ),
    NewsCategory.GEOPOLITICS: (
        "china",
        "taiwan",
        "war",
        "sanction",
        "tariff",
        "geopolit",
    ),
}

_POSITIVE_WORDS = (
    "beat",
    "growth",
    "surge",
    "record",
    "upgrade",
    "strong",
    "gain",
    "rally",
    "positive",
    "profit",
)
_NEGATIVE_WORDS = (
    "miss",
    "loss",
    "drop",
    "fall",
    "downgrade",
    "weak",
    "cut",
    "layoff",
    "lawsuit",
    "risk",
)
_TRUSTED_SOURCES = ("reuters", "bloomberg", "wall street journal", "cnbc", "sec")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _published_at(timestamp: Any) -> datetime | None:
    try:
        value = int(timestamp)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _classify(text: str) -> NewsCategory:
    lowered = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return NewsCategory.OTHER


def _sentiment(text: str) -> tuple[NewsSentiment, float]:
    lowered = text.lower()
    positive = sum(word in lowered for word in _POSITIVE_WORDS)
    negative = sum(word in lowered for word in _NEGATIVE_WORDS)
    total = positive + negative
    if total == 0 or positive == negative:
        return NewsSentiment.NEUTRAL, 0.52
    if positive > negative:
        return NewsSentiment.POSITIVE, min(0.95, 0.55 + positive / (total + 2))
    return NewsSentiment.NEGATIVE, min(0.95, 0.55 + negative / (total + 2))


def _source_score(source: str) -> int:
    return 2 if any(name in source.lower() for name in _TRUSTED_SOURCES) else 0


def _importance(category: NewsCategory, confidence: float, source: str) -> int:
    score = 2 + _source_score(source)
    if category in (
        NewsCategory.EARNINGS,
        NewsCategory.REGULATION,
        NewsCategory.GEOPOLITICS,
    ):
        score += 1
    if confidence >= 0.8:
        score += 1
    return min(5, score)


def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    urls: set[str] = set()
    titles: list[str] = []
    for item in sorted(
        items,
        key=lambda value: (
            value["published_at"],
            _source_score(value["source"]),
        ),
        reverse=True,
    ):
        title = _normalized_title(item["headline"])
        if item["url"] in urls:
            continue
        if any(
            difflib.SequenceMatcher(None, title, prior).ratio() >= 0.86
            for prior in titles
        ):
            continue
        urls.add(item["url"])
        titles.append(title)
        kept.append(item)
    return kept


def _normalize_article(item: dict[str, Any]) -> dict[str, Any] | None:
    headline = _clean_text(item.get("headline"))
    source = _clean_text(item.get("source")) or "Unknown source"
    url = _clean_text(item.get("url"))
    published_at = _published_at(item.get("datetime"))
    if not headline or not url or published_at is None:
        return None
    summary = _clean_text(item.get("summary")) or None
    category = _classify(f"{headline} {summary or ''}")
    sentiment, confidence = _sentiment(f"{headline} {summary or ''}")
    return {
        "headline": headline,
        "source": source,
        "published_at": published_at,
        "url": url,
        "summary": summary,
        "category": category,
        "sentiment": sentiment,
        "sentiment_confidence": round(confidence, 2),
        "importance": _importance(category, confidence, source),
    }


def get_news(symbol: str) -> dict[str, Any]:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise StockNotFound("Stock symbol cannot be empty")

    api_key = os.getenv("FINNHUB_API_KEY", "").strip()
    if not api_key:
        return {
            "symbol": normalized_symbol,
            "provider": SOURCE_NAME,
            "available": False,
            "message": "尚未設定 FINNHUB_API_KEY。",
            "articles": [],
        }

    end_date = date.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    try:
        response = httpx.get(
            FINNHUB_URL,
            params={
                "symbol": normalized_symbol,
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "token": api_key,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Finnhub news request failed for %s", normalized_symbol)
        raise StockDataUnavailable("Failed to retrieve company news") from exc

    if not isinstance(payload, list):
        logger.warning(
            "Finnhub returned an unexpected payload for %s", normalized_symbol
        )
        return {
            "symbol": normalized_symbol,
            "provider": SOURCE_NAME,
            "available": True,
            "message": "新聞來源回傳格式無法辨識。",
            "articles": [],
        }

    normalized = [
        article
        for item in payload
        if isinstance(item, dict)
        for article in [_normalize_article(item)]
        if article is not None
    ]
    return {
        "symbol": normalized_symbol,
        "provider": SOURCE_NAME,
        "available": True,
        "message": None,
        "articles": _deduplicate(normalized),
    }
