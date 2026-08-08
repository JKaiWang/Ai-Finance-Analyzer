"""Shared upstream access helpers for caching, retries and provider isolation."""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

import yfinance as yf

logger = logging.getLogger("finsight.data_provider")

T = TypeVar("T")


def _env_float(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.getenv(name, str(default))))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except ValueError:
        return default


@dataclass
class _CacheEntry:
    expires_at: float
    value: Any


class TTLCache:
    """Small process-local cache with bounded size and thread-safe access."""

    def __init__(self, ttl_seconds: float, max_entries: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._entries.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._entries) >= self.max_entries:
                oldest_key = min(
                    self._entries,
                    key=lambda item: self._entries[item].expires_at,
                )
                self._entries.pop(oldest_key, None)
            self._entries[key] = _CacheEntry(
                expires_at=time.monotonic() + self.ttl_seconds,
                value=value,
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


class MarketDataProvider(Protocol):
    """Provider boundary used by services and replaceable in tests."""

    def ticker(self, symbol: str) -> Any: ...


class YahooFinanceProvider:
    name = "Yahoo Finance via yfinance"

    def __init__(self) -> None:
        self._ticker_cache = TTLCache(
            ttl_seconds=_env_float("FINSIGHT_TICKER_CACHE_TTL", 60),
            max_entries=_env_int("FINSIGHT_CACHE_MAX_ENTRIES", 256),
        )

    def ticker(self, symbol: str) -> Any:
        key = symbol.strip().upper()
        cached = self._ticker_cache.get(key)
        if cached is not None:
            return cached
        ticker = retry_call(
            lambda: yf.Ticker(key),
            operation_name=f"initialize ticker {key}",
        )
        self._ticker_cache.set(key, ticker)
        return ticker

    def clear_cache(self) -> None:
        self._ticker_cache.clear()


_provider: MarketDataProvider = YahooFinanceProvider()


def get_market_data_provider() -> MarketDataProvider:
    return _provider


def set_market_data_provider(provider: MarketDataProvider) -> None:
    """Replace the provider for tests or a future alternate data source."""
    global _provider
    _provider = provider


def retry_call(
    operation: Callable[[], T],
    *,
    operation_name: str,
    attempts: int | None = None,
    backoff_seconds: float | None = None,
) -> T:
    max_attempts = attempts or _env_int("FINSIGHT_UPSTREAM_RETRIES", 2) + 1
    backoff = (
        _env_float("FINSIGHT_UPSTREAM_BACKOFF_SECONDS", 0.25)
        if backoff_seconds is None
        else backoff_seconds
    )
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - providers expose varied exceptions.
            last_error = exc
            if attempt == max_attempts - 1:
                break
            delay = backoff * (2**attempt)
            logger.warning(
                "Upstream operation failed (%s/%s): %s; retrying in %.2fs",
                attempt + 1,
                max_attempts,
                operation_name,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError(f"Upstream operation failed: {operation_name}") from last_error


def clear_provider_caches() -> None:
    provider = get_market_data_provider()
    clear_cache = getattr(provider, "clear_cache", None)
    if callable(clear_cache):
        clear_cache()
