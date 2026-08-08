import logging
import os
import threading
import time
from collections import defaultdict
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.analytics import AnalyticsResponse
from app.schemas.comparison import ComparisonResponse
from app.schemas.fundamentals import FundamentalsResponse
from app.schemas.news import NewsResponse
from app.schemas.stock import StockResponse
from app.services.analytics_service import get_stock_analytics
from app.services.comparison_service import get_comparison
from app.services.fundamentals_service import get_fundamentals
from app.services.news_service import get_news
from app.services.stock_service import (
    StockDataUnavailable,
    StockNotFound,
    get_stock_data,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("finsight.api")

load_dotenv()


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple process-local guard against accidental request floods."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.limit = _env_int("FINSIGHT_RATE_LIMIT_REQUESTS", 120)
        self.window = _env_int("FINSIGHT_RATE_LIMIT_WINDOW_SECONDS", 60)
        self.requests: defaultdict[str, list[float]] = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        with self.lock:
            recent = [
                timestamp
                for timestamp in self.requests[client]
                if now - timestamp < self.window
            ]
            if len(recent) >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(self.window)},
                )
            recent.append(now)
            self.requests[client] = recent
        return await call_next(request)


app = FastAPI(
    title="FinSight API",
    description="Backend API for an AI-powered investment research platform.",
    version="0.1.0",
    openapi_tags=[
        {
            "name": "stocks",
            "description": "查詢股票公司資訊、即時價格與歷史市場資料。",
        },
    ],
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FINSIGHT_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.get(
    "/compare",
    response_model=ComparisonResponse,
    summary="比較多家公司",
    description="比較 2 到 5 支股票的價格、風險、基本面與估值指標。",
    tags=["stocks"],
    responses={
        400: {"description": "股票代號數量或格式不符合限制。"},
        404: {"description": "找不到其中一支股票。"},
        502: {"description": "無法從外部資料來源取得比較資料。"},
    },
)
async def compare_stocks(
    symbols: str = Query(
        description="以逗號分隔的股票代號，例如 NVDA,AMD,INTC。",
        examples=["NVDA,AMD,INTC"],
    ),
    period: Literal["1y", "5y", "10y"] = Query(
        default="5y", description="比較資料期間。"
    ),
    benchmark: str | None = Query(
        default=None, description="Benchmark 代號，例如 ^GSPC 或 ^TWII。"
    ),
    frequency: Literal["1d", "1wk", "1mo"] = Query(
        default="1d", description="市場資料頻率。"
    ),
) -> ComparisonResponse:
    try:
        return ComparisonResponse(
            **get_comparison(
                symbols,
                period=period,
                benchmark=benchmark,
                frequency=frequency,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StockNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StockDataUnavailable as exc:
        raise HTTPException(
            status_code=502, detail="Market or financial data source is unavailable."
        ) from exc


@app.get(
    "/",
    summary="Health check",
    description="確認 FinSight API 服務目前可正常運作。",
)
async def root() -> dict[str, str]:
    return {
        "message": "FinSight API is running.",
    }


@app.get(
    "/stocks/{symbol}",
    response_model=StockResponse,
    summary="查詢股票資料",
    description="依股票代號取得公司資訊與最近一年的每日價格資料。",
    tags=["stocks"],
    responses={
        404: {"description": "找不到股票或沒有可用的市場資料。"},
        502: {"description": "無法從外部市場資料來源取得資料。"},
        500: {"description": "伺服器發生未預期錯誤。"},
    },
)
async def read_stock(
    symbol: str = Path(
        description="股票代號，例如 NVDA、AAPL 或台股 2330.TW。",
        examples=["NVDA", "AAPL", "2330.TW"],
    ),
    period: Literal["1y", "5y", "10y"] = Query(
        default="1y",
        description="歷史資料期間；支援 1 年、5 年或 10 年。",
    ),
) -> StockResponse:
    logger.info("Stock lookup requested: %s", symbol)

    try:
        stock_data = get_stock_data(symbol, period=period)
        return StockResponse(**stock_data)

    except StockNotFound as exc:
        logger.warning("Stock not found: %s (%s)", symbol, exc)
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except StockDataUnavailable as exc:
        logger.error("Market data source unavailable for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="Market data source is unavailable.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        logger.exception("Unexpected error while reading stock %s", symbol)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from exc


@app.get(
    "/stocks/{symbol}/analytics",
    response_model=AnalyticsResponse,
    summary="計算股票量化指標",
    description=(
        "計算報酬率、波動率、最大回撤、移動平均、Sharpe Ratio 與 Benchmark 比較。"
    ),
    tags=["stocks"],
    responses={
        404: {"description": "找不到股票或沒有可用的市場資料。"},
        502: {"description": "無法從外部市場資料來源取得資料。"},
        500: {"description": "伺服器發生未預期錯誤。"},
    },
)
async def read_stock_analytics(
    symbol: str = Path(
        description="股票代號，例如 NVDA、AAPL 或台股 2330.TW。",
        examples=["NVDA", "AAPL", "2330.TW"],
    ),
) -> AnalyticsResponse:
    logger.info("Stock analytics requested: %s", symbol)

    try:
        return AnalyticsResponse(**get_stock_analytics(symbol))

    except StockNotFound as exc:
        logger.warning("Analytics stock not found: %s (%s)", symbol, exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except StockDataUnavailable as exc:
        logger.error("Analytics data source unavailable for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="Market data source is unavailable.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error while calculating analytics for %s", symbol)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from exc


@app.get(
    "/stocks/{symbol}/fundamentals",
    response_model=FundamentalsResponse,
    summary="查詢股票基本面",
    description="取得損益表、資產負債表、現金流與基本面指標。",
    tags=["stocks"],
    responses={
        404: {"description": "找不到股票或沒有可用的財務資料。"},
        502: {"description": "無法從外部財務資料來源取得資料。"},
        500: {"description": "伺服器發生未預期錯誤。"},
    },
)
async def read_stock_fundamentals(
    symbol: str = Path(
        description="股票代號，例如 NVDA、AAPL 或台股 2330.TW。",
        examples=["NVDA", "AAPL", "2330.TW"],
    ),
) -> FundamentalsResponse:
    logger.info("Stock fundamentals requested: %s", symbol)

    try:
        return FundamentalsResponse(**get_fundamentals(symbol))
    except StockNotFound as exc:
        logger.warning("Fundamentals not found: %s (%s)", symbol, exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StockDataUnavailable as exc:
        logger.error("Fundamentals data source unavailable for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="Financial data source is unavailable.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error while reading fundamentals for %s", symbol)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from exc


@app.get(
    "/stocks/{symbol}/news",
    response_model=NewsResponse,
    summary="查詢公司新聞",
    description="取得公司近期新聞，並提供事件分類、情緒與重要度標籤。情緒分類不代表投資建議。",
    tags=["stocks"],
    responses={
        404: {"description": "股票代號不可為空白。"},
        502: {"description": "新聞資料來源暫時無法使用。"},
        500: {"description": "伺服器發生未預期錯誤。"},
    },
)
async def read_stock_news(
    symbol: str = Path(
        description="股票代號，例如 NVDA、AAPL 或台股 2330.TW。",
        examples=["NVDA", "AAPL", "2330.TW"],
    ),
) -> NewsResponse:
    logger.info("Stock news requested: %s", symbol)

    try:
        return NewsResponse(**get_news(symbol))
    except StockNotFound as exc:
        logger.warning("News stock not found: %s (%s)", symbol, exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StockDataUnavailable as exc:
        logger.error("News data source unavailable for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="News data source is unavailable.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error while reading news for %s", symbol)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from exc
