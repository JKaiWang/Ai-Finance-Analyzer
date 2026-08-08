from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.comparison_service import _chronological

client = TestClient(app)


def test_financial_trend_records_are_sorted_oldest_to_newest() -> None:
    records = [
        {"period": "2023-12-31", "revenue": 3.0},
        {"period": "2025-12-31", "revenue": 5.0},
        {"period": "2021-12-31", "revenue": 1.0},
    ]

    assert [record["period"] for record in _chronological(records)] == [
        "2021-12-31",
        "2023-12-31",
        "2025-12-31",
    ]


def _stock(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "company_name": f"{symbol} Company",
        "currency": "USD",
        "current_price": 100.0,
        "market_cap": 1_000_000,
        "history": [],
    }


def _analytics() -> dict:
    return {
        "period_returns": {"one_year": 0.2},
        "annualized_volatility": 0.3,
        "maximum_drawdown": -0.15,
        "sharpe_ratio": 0.8,
    }


def _fundamentals() -> dict:
    return {
        "income_statement": [{"eps": 5.0}],
        "cash_flow": [{"free_cash_flow": 250.0}],
        "growth": {"revenue_growth": 0.1},
        "profitability": {
            "gross_margin": 0.6,
            "net_margin": 0.2,
            "roe": 0.25,
        },
        "financial_health": {},
        "valuation": {},
        "dividend": {},
        "ownership": {},
    }


def test_compare_stocks_returns_unified_market_risk_and_fundamental_metrics() -> None:
    with (
        patch(
            "app.services.comparison_service.get_stock_data",
            side_effect=lambda symbol, period="1y": _stock(symbol),
        ),
        patch(
            "app.services.comparison_service.get_stock_analytics",
            side_effect=lambda symbol, period="1y": _analytics(),
        ),
        patch(
            "app.services.comparison_service.get_fundamentals",
            return_value=_fundamentals(),
        ),
    ):
        response = client.get("/compare?symbols=nvda,AMD,NVDA")

    assert response.status_code == 200
    body = response.json()
    assert body["symbols"] == ["NVDA", "AMD"]
    assert len(body["companies"]) == 2
    assert body["companies"][0]["one_year_return"] == 0.2
    assert body["companies"][0]["price_to_earnings"] == 20.0
    assert body["companies"][0]["free_cash_flow"] == 250.0


def test_compare_stocks_rejects_more_than_five_symbols() -> None:
    response = client.get("/compare?symbols=A,B,C,D,E,F")

    assert response.status_code == 400
    assert "最多比較 5" in response.json()["detail"]


def test_compare_stocks_requires_two_symbols() -> None:
    response = client.get("/compare?symbols=NVDA")

    assert response.status_code == 400
    assert "至少提供兩個" in response.json()["detail"]


def test_compare_stocks_supports_period_benchmark_and_frequency() -> None:
    with (
        patch(
            "app.services.comparison_service.get_stock_data",
            side_effect=lambda symbol, **kwargs: _stock(symbol),
        ),
        patch(
            "app.services.comparison_service.get_stock_analytics",
            side_effect=lambda symbol, **kwargs: _analytics(),
        ),
        patch(
            "app.services.comparison_service.get_fundamentals",
            return_value=_fundamentals(),
        ),
    ):
        response = client.get(
            "/compare?symbols=NVDA,AMD&period=1y&benchmark=%5EGSPC&frequency=1wk"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == "1y"
    assert body["frequency"] == "1wk"
    assert body["benchmark"] == "^GSPC"


def test_compare_stocks_isolates_optional_provider_failures() -> None:
    def analytics(symbol: str, **kwargs: object) -> dict:
        if symbol == "AMD":
            raise RuntimeError("benchmark timeout")
        return _analytics()

    with (
        patch(
            "app.services.comparison_service.get_stock_data",
            side_effect=lambda symbol, **kwargs: _stock(symbol),
        ),
        patch(
            "app.services.comparison_service.get_stock_analytics",
            side_effect=analytics,
        ),
        patch(
            "app.services.comparison_service.get_fundamentals",
            return_value=_fundamentals(),
        ),
    ):
        response = client.get("/compare?symbols=NVDA,AMD")

    assert response.status_code == 200
    companies = {company["symbol"]: company for company in response.json()["companies"]}
    assert companies["NVDA"]["available"] is True
    assert companies["AMD"]["available"] is True
    assert any(error.startswith("analytics:") for error in companies["AMD"]["errors"])
