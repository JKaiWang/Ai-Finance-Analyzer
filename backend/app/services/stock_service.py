import logging
import math
from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger("finsight.stock_service")

SUPPORTED_HISTORY_PERIODS = ("1y", "5y", "10y")
SUPPORTED_HISTORY_INTERVALS = ("1d", "1wk", "1mo")
DATA_SOURCE = "Yahoo Finance via yfinance"


class StockNotFound(Exception):
    """Raised when no stock data can be found for a symbol"""


class StockDataUnavailable(Exception):
    """Raised when the external market data source cannot be reached."""


def _safe_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _safe_int(value: Any) -> int | None:
    if _is_missing(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number)


def _safe_str(value: Any) -> str | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    if isinstance(missing, bool):
        return missing
    return False


def _safe_date(value: Any) -> date | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.date()


def get_stock_data(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> dict[str, Any]:
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise StockNotFound("Stock symbol cannot be empty")
    if period not in SUPPORTED_HISTORY_PERIODS:
        raise ValueError(
            f"Unsupported history period: {period}. "
            f"Choose from {', '.join(SUPPORTED_HISTORY_PERIODS)}."
        )
    if interval not in SUPPORTED_HISTORY_INTERVALS:
        raise ValueError(
            f"Unsupported history interval: {interval}. "
            f"Choose from {', '.join(SUPPORTED_HISTORY_INTERVALS)}."
        )

    logger.info("Fetching market data for %s", normalized_symbol)

    try:
        ticker = yf.Ticker(normalized_symbol)
    except Exception as exc:
        logger.exception(
            "Failed to initialize yfinance ticker for %s", normalized_symbol
        )
        raise StockDataUnavailable(
            f"Failed to initialize market data for {normalized_symbol}"
        ) from exc

    try:
        history = ticker.history(period=period, interval=interval, auto_adjust=False)
    except Exception as exc:
        logger.exception("Failed to retrieve history for %s", normalized_symbol)
        raise StockDataUnavailable(
            f"Failed to retrieve market data for {normalized_symbol}"
        ) from exc

    if history is None or not isinstance(history, pd.DataFrame) or history.empty:
        raise StockNotFound(f"No market data found for {normalized_symbol}")

    price_history: list[dict[str, Any]] = []

    for timestamp, row in history.iterrows():
        record_date = _safe_date(timestamp)
        open_price = _safe_float(row.get("Open"))
        high_price = _safe_float(row.get("High"))
        low_price = _safe_float(row.get("Low"))
        close_price = _safe_float(row.get("Close"))
        adjusted_close = _safe_float(row.get("Adj Close")) or close_price

        if None in (
            record_date,
            open_price,
            high_price,
            low_price,
            close_price,
            adjusted_close,
        ):
            continue

        price_history.append(
            {
                "date": record_date,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "adjusted_close": adjusted_close,
                "volume": _safe_int(row.get("Volume")) or 0,
            }
        )

    if not price_history:
        raise StockNotFound(f"No usable market data found for {normalized_symbol}")

    try:
        info = ticker.info
    except Exception as exc:  # noqa: BLE001 - yfinance exposes varied upstream errors.
        logger.warning(
            "Optional company information unavailable for %s: %s",
            normalized_symbol,
            exc,
        )
        info = {}
    if not isinstance(info, dict):
        info = {}

    latest_close = price_history[-1]["close"]

    return {
        "symbol": normalized_symbol,
        "company_name": _safe_str(info.get("longName"))
        or _safe_str(info.get("shortName")),
        "currency": _safe_str(info.get("currency")),
        "current_price": _safe_float(info.get("currentPrice") or latest_close),
        "market_cap": _safe_int(info.get("marketCap")),
        "enterprise_value": _safe_int(info.get("enterpriseValue")),
        "shares_outstanding": _safe_int(info.get("sharesOutstanding")),
        "float_shares": _safe_int(info.get("floatShares")),
        "sector": _safe_str(info.get("sector")),
        "industry": _safe_str(info.get("industry")),
        "country": _safe_str(info.get("country")),
        "exchange": _safe_str(info.get("exchange")),
        "history": price_history,
        "data_quality": {
            "source": DATA_SOURCE,
            "as_of": price_history[-1]["date"],
            "period": period,
            "metrics": {
                "close": {
                    "value": latest_close,
                    "period": period,
                    "as_of": price_history[-1]["date"],
                    "source": DATA_SOURCE,
                },
                "adjusted_close": {
                    "value": price_history[-1]["adjusted_close"],
                    "period": period,
                    "as_of": price_history[-1]["date"],
                    "source": DATA_SOURCE,
                },
                "market_cap": {
                    "value": _safe_int(info.get("marketCap")),
                    "period": "latest",
                    "as_of": price_history[-1]["date"],
                    "source": DATA_SOURCE,
                    "metadata": {"availability": "provider_dependent"},
                },
            },
        },
    }
