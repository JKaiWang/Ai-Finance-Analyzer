import logging
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch

import httpx
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.analytics_service import align_histories
from app.services.stock_service import StockNotFound

client = TestClient(app)


def _history(close: float = 101.5, tz: str = "America/New_York") -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2026-08-03 16:00", tz=tz),
            pd.Timestamp("2026-08-04 16:00", tz=tz),
        ]
    )
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.5],
            "Close": [101.0, close],
            "Volume": [1_000_000, 2_000_000],
        },
        index=index,
    )


def _ticker(history: pd.DataFrame | None, info: dict | None = None) -> Mock:
    ticker = Mock()
    ticker.history.return_value = history
    ticker.info = info or {}
    return ticker


def test_stock_symbol_success() -> None:
    ticker = _ticker(
        _history(),
        {
            "longName": "NVIDIA Corporation",
            "currency": "USD",
            "currentPrice": 105.25,
            "marketCap": 2_500_000_000_000,
        },
    )

    with patch("app.services.stock_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/NVDA")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "NVDA"
    assert body["company_name"] == "NVIDIA Corporation"
    assert body["currency"] == "USD"
    assert body["current_price"] == 105.25
    assert body["market_cap"] == 2_500_000_000_000
    assert body["history"][-1] == {
        "date": "2026-08-04",
        "open": 101.0,
        "high": 103.0,
        "low": 100.5,
        "close": 101.5,
        "adjusted_close": 101.5,
        "volume": 2_000_000,
    }


def test_taiwan_stock_symbol_success_with_missing_optional_info() -> None:
    ticker = _ticker(
        _history(close=950.0, tz="Asia/Taipei"),
        {
            "longName": None,
            "shortName": float("nan"),
            "currency": "TWD",
            "currentPrice": None,
            "marketCap": float("nan"),
        },
    )

    with patch("app.services.stock_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/2330.TW")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "2330.TW"
    assert body["company_name"] is None
    assert body["currency"] == "TWD"
    assert body["current_price"] == 950.0
    assert body["market_cap"] is None
    assert body["history"][-1]["date"] == "2026-08-04"


def test_unknown_stock_symbol_returns_404() -> None:
    ticker = _ticker(pd.DataFrame())

    with patch("app.services.stock_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/NOT_A_SYMBOL")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid stock symbol: NOT_A_SYMBOL"


def test_stock_history_period_and_metadata() -> None:
    history = _history().assign(**{"Adj Close": [99.0, 100.5]})
    ticker = _ticker(
        history,
        {
            "longName": "NVIDIA Corporation",
            "currency": "USD",
            "currentPrice": 105.25,
            "marketCap": 2_500_000_000_000,
            "enterpriseValue": 2_450_000_000_000,
            "sharesOutstanding": 2_400_000_000,
            "floatShares": 2_300_000_000,
            "sector": "Technology",
            "industry": "Semiconductors",
            "country": "United States",
            "exchange": "NMS",
        },
    )

    with patch("app.services.stock_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/NVDA?period=5y")

    assert response.status_code == 200
    body = response.json()
    assert body["history"][-1]["adjusted_close"] == 100.5
    assert body["enterprise_value"] == 2_450_000_000_000
    assert body["shares_outstanding"] == 2_400_000_000
    assert body["sector"] == "Technology"
    assert body["data_quality"]["period"] == "5y"
    assert body["data_quality"]["source"] == "Yahoo Finance via yfinance"


def test_stock_history_supports_ten_year_period() -> None:
    ticker = _ticker(_history())

    with patch("app.services.stock_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/NVDA?period=10y")

    assert response.status_code == 200
    assert response.json()["data_quality"]["period"] == "10y"


def test_align_histories_keeps_only_shared_trading_dates() -> None:
    stock = [
        {"date": date(2026, 8, 3), "close": 100.0},
        {"date": date(2026, 8, 4), "close": 101.0},
    ]
    benchmark = [
        {"date": date(2026, 8, 4), "close": 200.0},
        {"date": date(2026, 8, 5), "close": 202.0},
    ]

    assert align_histories(stock, benchmark) == [(date(2026, 8, 4), 101.0, 200.0)]


def test_market_data_source_failure_returns_502(caplog) -> None:
    ticker = _ticker(None)
    ticker.history.side_effect = ConnectionError("upstream timeout")

    with (
        caplog.at_level(logging.ERROR, logger="finsight.api"),
        patch("app.services.stock_service.yf.Ticker", return_value=ticker),
    ):
        response = client.get("/stocks/NVDA")

    assert response.status_code == 502
    assert response.json() == {"detail": "Market data source is unavailable."}
    assert "Market data source unavailable for NVDA" in caplog.text


def test_unexpected_error_returns_generic_500(caplog) -> None:
    with (
        caplog.at_level(logging.ERROR, logger="finsight.api"),
        patch(
            "app.main.get_stock_data",
            side_effect=RuntimeError("private implementation detail"),
        ),
    ):
        response = client.get("/stocks/NVDA")

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
    assert "private implementation detail" in caplog.text


def test_stock_analytics_returns_quant_metrics() -> None:
    history = [
        {
            "date": date(2025, 1, 1) + timedelta(days=index),
            "open": 100.0 + index * 0.1,
            "high": 101.0 + index * 0.1,
            "low": 99.0 + index * 0.1,
            "close": 100.0 + index * 0.1,
            "volume": 1_000_000,
        }
        for index in range(365)
    ]
    stock_data = {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "currency": "USD",
        "current_price": 136.4,
        "market_cap": 2_500_000_000_000,
        "history": history,
    }
    benchmark = Mock()
    benchmark.history.return_value = _history(close=104.0)

    with (
        patch("app.services.analytics_service.get_stock_data", return_value=stock_data),
        patch("app.services.analytics_service.yf.Ticker", return_value=benchmark),
    ):
        response = client.get("/stocks/NVDA/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "NVDA"
    assert len(body["daily_returns"]) == 365
    assert body["daily_returns"][0]["daily_return"] is None
    assert body["period_returns"]["one_year"] > 0
    assert body["annualized_volatility"] > 0
    assert body["maximum_drawdown"] == 0
    assert body["moving_averages"][18]["ma20"] is None
    assert body["moving_averages"][19]["ma20"] == 100.95
    assert body["moving_averages"][-1]["ma200"] is not None
    assert body["sharpe_ratio"] is not None
    assert "downside_volatility" in body
    assert "sortino_ratio" in body
    assert "calmar_ratio" in body
    assert body["cagr"] is not None
    assert body["benchmark"]["symbol"] == "^GSPC"
    assert body["benchmark"]["relative_performance"] is not None


def test_stock_analytics_unknown_symbol_returns_404() -> None:
    with patch(
        "app.services.analytics_service.get_stock_data",
        side_effect=StockNotFound("No market data found for UNKNOWN"),
    ):
        response = client.get("/stocks/UNKNOWN/analytics")

    assert response.status_code == 404
    assert response.json() == {"detail": "No market data found for UNKNOWN"}


def test_stock_fundamentals_returns_statements_and_metrics() -> None:
    periods = [pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")]
    income = pd.DataFrame(
        {
            periods[0]: [1_000.0, 400.0, 250.0, 200.0, 2.0],
            periods[1]: [800.0, 320.0, 192.0, 160.0, 1.6],
        },
        index=[
            "Total Revenue",
            "Gross Profit",
            "Operating Income",
            "Net Income",
            "Diluted EPS",
        ],
    )
    balance = pd.DataFrame(
        {
            periods[0]: [2_000.0, 1_000.0, 300.0, 500.0, 1_000.0, 1_200.0, 600.0],
        },
        index=[
            "Total Assets",
            "Total Liabilities Net Minority Interest",
            "Cash Cash Equivalents And Short Term Investments",
            "Total Debt",
            "Stockholders Equity",
            "Current Assets",
            "Current Liabilities",
        ],
    )
    cash_flow = pd.DataFrame(
        {
            periods[0]: [200.0, -50.0, 150.0],
            periods[1]: [160.0, -40.0, 120.0],
        },
        index=["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"],
    )
    ticker = Mock()
    ticker.income_stmt = income
    ticker.balance_sheet = balance
    ticker.cashflow = cash_flow

    with patch("app.services.fundamentals_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/NVDA/fundamentals")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "NVDA"
    assert body["income_statement"][0]["revenue"] == 1_000.0
    assert body["income_statement"][0]["eps"] == 2.0
    assert body["balance_sheet"][0]["equity"] == 1_000.0
    assert body["cash_flow"][0]["free_cash_flow"] == 150.0
    assert body["growth"]["revenue_growth"] == 0.25
    assert body["profitability"]["gross_margin"] == 0.4
    assert body["profitability"]["roe"] == 0.2
    assert body["financial_health"]["debt_to_equity"] == 0.5
    assert body["financial_health"]["current_ratio"] == 2.0
    assert body["financial_health"]["free_cash_flow_margin"] == 0.15
    assert "quick_ratio" in body["financial_health"]
    assert "cash_ratio" in body["financial_health"]
    assert "interest_coverage" in body["financial_health"]
    assert "valuation" in body
    assert "dividend" in body
    assert "ownership" in body


def test_stock_fundamentals_missing_tables_returns_404() -> None:
    ticker = Mock()
    ticker.income_stmt = pd.DataFrame()
    ticker.balance_sheet = pd.DataFrame()
    ticker.cashflow = pd.DataFrame()

    with patch("app.services.fundamentals_service.yf.Ticker", return_value=ticker):
        response = client.get("/stocks/UNKNOWN/fundamentals")

    assert response.status_code == 404
    assert response.json() == {"detail": "No fundamental data found for UNKNOWN"}


def test_stock_news_normalizes_classifies_and_deduplicates() -> None:
    provider_response = Mock()
    provider_response.json.return_value = [
        {
            "headline": "NVIDIA beats earnings estimates with record revenue",
            "source": "Reuters",
            "datetime": 1_754_240_000,
            "url": "https://example.com/earnings",
            "summary": "The company reported strong quarterly growth.",
        },
        {
            "headline": "NVIDIA beats earnings estimates with record revenue!",
            "source": "Small Blog",
            "datetime": 1_754_230_000,
            "url": "https://example.com/duplicate",
            "summary": "The company reported strong quarterly growth.",
        },
        {
            "headline": "NVIDIA faces new export regulation risk",
            "source": "CNBC",
            "datetime": 1_754_220_000,
            "url": "https://example.com/regulation",
            "summary": "New regulation may affect shipments.",
        },
    ]

    with (
        patch.dict(os.environ, {"FINNHUB_API_KEY": "test-key"}),
        patch("app.services.news_service.httpx.get", return_value=provider_response),
    ):
        response = client.get("/stocks/NVDA/news")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert len(body["articles"]) == 2
    assert body["articles"][0]["category"] == "Earnings"
    assert body["articles"][0]["sentiment"] == "Positive"
    assert body["articles"][0]["importance"] == 5
    assert body["articles"][1]["category"] == "Regulation"


def test_stock_news_without_api_key_returns_config_state() -> None:
    with patch.dict(os.environ, {}, clear=True):
        response = client.get("/stocks/NVDA/news")

    assert response.status_code == 200
    assert response.json() == {
        "symbol": "NVDA",
        "provider": "Finnhub",
        "available": False,
        "data_status": {
            "status": "unavailable",
            "source": "Finnhub",
            "as_of": None,
            "message": "尚未設定 FINNHUB_API_KEY。",
            "missing_fields": [],
        },
        "message": "尚未設定 FINNHUB_API_KEY。",
        "articles": [],
    }


def test_stock_news_provider_failure_returns_502() -> None:
    with (
        patch.dict(os.environ, {"FINNHUB_API_KEY": "test-key"}),
        patch(
            "app.services.news_service.httpx.get",
            side_effect=httpx.ConnectTimeout("upstream timeout"),
        ),
    ):
        response = client.get("/stocks/NVDA/news")

    assert response.status_code == 502
    assert response.json() == {"detail": "News data source is unavailable."}


def test_swagger_ui_and_openapi_describe_stock_endpoint() -> None:
    docs_response = client.get("/docs")
    redoc_response = client.get("/redoc")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "swagger-ui" in docs_response.text
    assert redoc_response.status_code == 200
    assert "redoc" in redoc_response.text.lower()
    assert openapi_response.status_code == 200

    openapi = openapi_response.json()
    assert openapi["info"] == {
        "title": "FinSight API",
        "description": "Backend API for an AI-powered investment research platform.",
        "version": "0.1.0",
    }

    stock_operation = openapi["paths"]["/stocks/{symbol}"]["get"]
    assert stock_operation["summary"] == "查詢股票資料"
    symbol_parameter = stock_operation["parameters"][0]
    assert (
        symbol_parameter["description"] == "股票代號，例如 NVDA、AAPL 或台股 2330.TW。"
    )
    assert symbol_parameter["schema"]["examples"] == [
        "NVDA",
        "AAPL",
        "2330.TW",
    ]
    assert (
        stock_operation["responses"]["200"]["content"]["application/json"]["schema"][
            "$ref"
        ]
        == "#/components/schemas/StockResponse"
    )
    assert "404" in stock_operation["responses"]
    assert "502" in stock_operation["responses"]
    assert "500" in stock_operation["responses"]

    stock_schema = openapi["components"]["schemas"]["StockResponse"]
    assert stock_schema["properties"]["history"]["description"] == (
        "最近一年的每日 OHLCV 歷史資料。"
    )
