from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any

from app.services.analytics_service import get_stock_analytics
from app.services.fundamentals_service import get_fundamentals
from app.services.research_service import build_research_outputs
from app.services.stock_service import (
    StockDataUnavailable,
    StockNotFound,
    get_stock_data,
)

MAX_COMPARISON_SYMBOLS = 5
VALID_PERIODS = ("1y", "5y", "10y")
VALID_FREQUENCIES = ("1d", "1wk", "1mo")


def parse_symbols(raw_symbols: str) -> list[str]:
    symbols: list[str] = []
    for raw_symbol in raw_symbols.split(","):
        symbol = raw_symbol.strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)

    if len(symbols) < 2:
        raise ValueError("請至少提供兩個不同的股票代號。")
    if len(symbols) > MAX_COMPARISON_SYMBOLS:
        raise ValueError(f"一次最多比較 {MAX_COMPARISON_SYMBOLS} 支股票。")
    return symbols


def _latest_value(records: list[dict[str, Any]], key: str) -> float | None:
    if not records:
        return None
    value = records[0].get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _price_to_earnings(price: float | None, eps: float | None) -> float | None:
    if price is None or eps is None or eps <= 0:
        return None
    return price / eps


def _positive_metric(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _chronological(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(record: dict[str, Any]) -> tuple[int, str]:
        period = record.get("period")
        if isinstance(period, date):
            return (0, period.isoformat())
        return (1, str(period or ""))

    return sorted(records, key=sort_key)


def _normalized_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [
        record
        for record in history
        if record.get("date") is not None
        and isinstance(record.get("adjusted_close", record.get("close")), (int, float))
        and record.get("adjusted_close", record.get("close")) > 0
    ]
    if not valid:
        return []
    base = float(valid[0].get("adjusted_close", valid[0].get("close")))
    return [
        {
            "date": record["date"],
            "value": float(record.get("adjusted_close", record.get("close")))
            / base
            * 100,
        }
        for record in valid
    ]


def _call_stock(symbol: str, period: str, frequency: str) -> dict[str, Any]:
    if frequency == "1d":
        return get_stock_data(symbol, period=period)
    return get_stock_data(symbol, period=period, interval=frequency)


def _call_analytics(
    symbol: str, period: str, frequency: str, benchmark: str | None
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"period": period}
    if frequency != "1d":
        kwargs["interval"] = frequency
    if benchmark:
        kwargs["benchmark"] = benchmark
    return get_stock_analytics(symbol, **kwargs)


def _empty_company(symbol: str, error: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "company_name": None,
        "sector": None,
        "industry": None,
        "country": None,
        "exchange": None,
        "currency": None,
        "current_price": None,
        "market_cap": None,
        "enterprise_value": None,
        "normalized_history": [],
        "available": False,
        "errors": [error],
        "financial_trends": {},
    }


def _load_company(
    symbol: str, period: str, frequency: str, benchmark: str | None
) -> dict[str, Any]:
    try:
        stock = _call_stock(symbol, period, frequency)
    except (StockNotFound, StockDataUnavailable, ValueError) as exc:
        return _empty_company(symbol, str(exc))

    errors: list[str] = []
    try:
        analytics = _call_analytics(symbol, period, frequency, benchmark)
    except Exception as exc:  # noqa: BLE001 - isolate optional provider failures.
        analytics = {"period_returns": {}}
        errors.append(f"analytics: {exc}")
    try:
        fundamentals = get_fundamentals(symbol)
    except Exception as exc:  # noqa: BLE001 - isolate optional provider failures.
        fundamentals = {
            "income_statement": [],
            "cash_flow": [],
            "growth": {},
            "profitability": {},
            "financial_health": {},
            "valuation": {},
            "dividend": {},
            "ownership": {},
        }
        errors.append(f"fundamentals: {exc}")

    income_records = fundamentals.get("income_statement", [])
    latest_income = income_records[0] if income_records else {}
    growth = fundamentals.get("growth", {})
    profitability = fundamentals.get("profitability", {})
    financial_health = fundamentals.get("financial_health", {})
    valuation = fundamentals.get("valuation", {})
    dividend = fundamentals.get("dividend", {})
    ownership = fundamentals.get("ownership", {})
    period_returns = analytics.get("period_returns", {})
    income_trends = _chronological(fundamentals.get("income_statement", []))
    cash_flow_trends = _chronological(fundamentals.get("cash_flow", []))
    financial_trends = {
        "revenue": [
            {
                "period": str(record.get("period", f"period_{index + 1}")),
                "value": record.get("revenue"),
            }
            for index, record in enumerate(reversed(income_trends))
        ],
        "eps": [
            {
                "period": str(record.get("period", f"period_{index + 1}")),
                "value": record.get("eps"),
            }
            for index, record in enumerate(reversed(income_trends))
        ],
        "free_cash_flow": [
            {
                "period": str(record.get("period", f"period_{index + 1}")),
                "value": record.get("free_cash_flow"),
            }
            for index, record in enumerate(reversed(cash_flow_trends))
        ],
        "net_margin": [
            {
                "period": str(record.get("period", f"period_{index + 1}")),
                "value": (
                    record.get("net_income") / record["revenue"]
                    if isinstance(record.get("net_income"), (int, float))
                    and isinstance(record.get("revenue"), (int, float))
                    and record["revenue"] != 0
                    else None
                ),
            }
            for index, record in enumerate(reversed(income_trends))
        ],
    }

    return {
        "symbol": stock["symbol"],
        "company_name": stock.get("company_name"),
        "sector": stock.get("sector"),
        "industry": stock.get("industry"),
        "country": stock.get("country"),
        "exchange": stock.get("exchange"),
        "currency": stock.get("currency"),
        "current_price": stock.get("current_price"),
        "market_cap": stock.get("market_cap"),
        "enterprise_value": stock.get("enterprise_value"),
        "one_week_return": period_returns.get("one_week"),
        "one_month_return": period_returns.get("one_month"),
        "three_month_return": period_returns.get("three_months"),
        "six_month_return": period_returns.get("six_months"),
        "ytd_return": period_returns.get("ytd"),
        "one_year_return": period_returns.get("one_year"),
        "three_year_return": period_returns.get("three_years"),
        "five_year_return": period_returns.get("five_years"),
        "annualized_volatility": analytics.get("annualized_volatility"),
        "maximum_drawdown": analytics.get("maximum_drawdown"),
        "sharpe_ratio": analytics.get("sharpe_ratio"),
        "downside_volatility": analytics.get("downside_volatility"),
        "sortino_ratio": analytics.get("sortino_ratio"),
        "calmar_ratio": analytics.get("calmar_ratio"),
        "cagr": analytics.get("cagr"),
        "alpha": analytics.get("alpha"),
        "beta": analytics.get("beta"),
        "revenue_growth": growth.get("revenue_growth"),
        "eps_growth": growth.get("eps_growth"),
        "net_income_growth": growth.get("net_income_growth"),
        "free_cash_flow_growth": growth.get("free_cash_flow_growth"),
        "book_value_growth": growth.get("book_value_growth"),
        "gross_margin": profitability.get("gross_margin"),
        "operating_margin": profitability.get("operating_margin"),
        "ebitda_margin": profitability.get("ebitda_margin"),
        "net_margin": profitability.get("net_margin"),
        "roe": profitability.get("roe"),
        "roa": profitability.get("roa"),
        "roic": profitability.get("roic"),
        "current_ratio": financial_health.get("current_ratio"),
        "quick_ratio": financial_health.get("quick_ratio"),
        "cash_ratio": financial_health.get("cash_ratio"),
        "debt_to_equity": financial_health.get("debt_to_equity"),
        "interest_coverage": financial_health.get("interest_coverage"),
        "free_cash_flow": _latest_value(
            fundamentals.get("cash_flow", []), "free_cash_flow"
        ),
        "eps": latest_income.get("eps"),
        "free_cash_flow_margin": financial_health.get("free_cash_flow_margin"),
        "price_to_earnings": _positive_metric(valuation.get("trailing_pe"))
        or _price_to_earnings(stock.get("current_price"), latest_income.get("eps")),
        "forward_pe": valuation.get("forward_pe"),
        "peg_ratio": valuation.get("peg_ratio"),
        "price_to_book": valuation.get("price_to_book"),
        "price_to_sales": valuation.get("price_to_sales"),
        "enterprise_to_ebitda": valuation.get("enterprise_to_ebitda"),
        "enterprise_to_revenue": valuation.get("enterprise_to_revenue"),
        "dividend_yield": dividend.get("dividend_yield"),
        "dividend_growth": dividend.get("dividend_growth"),
        "payout_ratio": dividend.get("payout_ratio"),
        "insider_ownership": ownership.get("insider_ownership"),
        "institutional_ownership": ownership.get("institutional_ownership"),
        "float_shares": ownership.get("float_shares"),
        "shares_outstanding": ownership.get("shares_outstanding"),
        "normalized_history": _normalized_history(stock.get("history", [])),
        "available": True,
        "errors": errors,
        "financial_trends": financial_trends,
    }


def get_comparison(
    raw_symbols: str,
    period: str = "5y",
    benchmark: str | None = None,
    frequency: str = "1d",
) -> dict[str, Any]:
    symbols = parse_symbols(raw_symbols)
    if period not in VALID_PERIODS:
        raise ValueError(f"Unsupported comparison period: {period}.")
    if frequency not in VALID_FREQUENCIES:
        raise ValueError(f"Unsupported comparison frequency: {frequency}.")
    if benchmark is not None and not benchmark.strip():
        raise ValueError("Benchmark cannot be blank.")

    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        companies = list(
            executor.map(
                lambda symbol: _load_company(symbol, period, frequency, benchmark),
                symbols,
            )
        )
    companies = build_research_outputs(companies)
    return {
        "symbols": symbols,
        "period": period,
        "frequency": frequency,
        "benchmark": benchmark,
        "companies": companies,
    }
