import pytest

from app.services.data_provider import clear_provider_caches
from app.services.news_service import NEWS_CACHE
from app.services.stock_service import STOCK_CACHE


@pytest.fixture(autouse=True)
def clear_upstream_caches() -> None:
    clear_provider_caches()
    NEWS_CACHE.clear()
    STOCK_CACHE.clear()
