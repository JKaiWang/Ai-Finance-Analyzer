import logging
import math
import statistics
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf  # Compatibility alias for provider-level test doubles.

from app.services.data_provider import get_market_data_provider, retry_call
from app.services.stock_service import DATA_SOURCE, StockNotFound, get_stock_data

logger = logging.getLogger("finsight.analytics_service")

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.0


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(value.day, 28)
    return date(year, month, day)


def _ordered_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = []
    for record in history:
        record_date = record.get("date")
        close = _safe_float(record.get("adjusted_close")) or _safe_float(
            record.get("close")
        )
        if isinstance(record_date, date) and close is not None and close > 0:
            ordered.append({"date": record_date, "close": close})
    return sorted(ordered, key=lambda record: record["date"])


def align_histories(
    stock_history: list[dict[str, Any]], benchmark_history: list[dict[str, Any]]
) -> list[tuple[date, float, float]]:
    """Align stock and benchmark prices on shared trading dates.

    Missing dates are not forward-filled; only dates present in both series are
    retained so return and beta calculations do not invent observations.
    """
    stock = {
        record["date"]: record["close"] for record in _ordered_history(stock_history)
    }
    benchmark = {
        record["date"]: record["close"]
        for record in _ordered_history(benchmark_history)
    }
    return [
        (record_date, stock[record_date], benchmark[record_date])
        for record_date in sorted(stock.keys() & benchmark.keys())
    ]


def _daily_returns(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    previous_close: float | None = None

    for record in history:
        close = record["close"]
        daily_return = None
        if previous_close is not None and previous_close != 0:
            daily_return = close / previous_close - 1
        result.append({"date": record["date"], "daily_return": daily_return})
        previous_close = close

    return result


def _period_return(history: list[dict[str, Any]], months: int) -> float | None:
    """Calculate cumulative return from the first observation at the cutoff."""
    if len(history) < 2:
        return None

    end = history[-1]
    cutoff = _subtract_months(end["date"], months)
    start = next((record for record in history if record["date"] >= cutoff), None)
    if start is None or start["close"] == 0:
        return None
    return end["close"] / start["close"] - 1


def _return_from_date(history: list[dict[str, Any]], cutoff: date) -> float | None:
    if len(history) < 2:
        return None
    end = history[-1]
    start = next((record for record in history if record["date"] >= cutoff), None)
    if start is None or start["close"] == 0:
        return None
    return end["close"] / start["close"] - 1


def _annualized_return(history: list[dict[str, Any]]) -> float | None:
    """Annualize total price return using elapsed calendar years."""
    if len(history) < 2 or history[0]["close"] <= 0:
        return None
    years = (history[-1]["date"] - history[0]["date"]).days / 365.25
    if years <= 0:
        return None
    return (history[-1]["close"] / history[0]["close"]) ** (1 / years) - 1


def _moving_averages(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    closes = [record["close"] for record in history]

    for index, record in enumerate(history):
        values: dict[str, Any] = {"date": record["date"]}
        for window in (20, 50, 200):
            key = f"ma{window}"
            values[key] = (
                statistics.fmean(closes[index - window + 1 : index + 1])
                if index + 1 >= window
                else None
            )
        result.append(values)

    return result


def _volatility(returns: list[float]) -> float | None:
    """Annualize sample daily standard deviation with sqrt(252)."""
    if len(returns) < 2:
        return None
    return statistics.stdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR)


def _maximum_drawdown(history: list[dict[str, Any]]) -> float | None:
    if not history:
        return None

    peak = history[0]["close"]
    maximum_drawdown = 0.0
    for record in history:
        peak = max(peak, record["close"])
        maximum_drawdown = min(maximum_drawdown, record["close"] / peak - 1)
    return maximum_drawdown


def _sharpe_ratio(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    standard_deviation = statistics.stdev(returns)
    if standard_deviation == 0:
        return None
    daily_risk_free_rate = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess_returns = [value - daily_risk_free_rate for value in returns]
    return (
        statistics.fmean(excess_returns)
        / standard_deviation
        * math.sqrt(TRADING_DAYS_PER_YEAR)
    )


def _downside_volatility(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    downside = [min(value, 0.0) for value in returns]
    return statistics.stdev(downside) * math.sqrt(TRADING_DAYS_PER_YEAR)


def _sortino_ratio(returns: list[float]) -> float | None:
    downside = _downside_volatility(returns)
    if downside in (None, 0):
        return None
    annualized_return = statistics.fmean(returns) * TRADING_DAYS_PER_YEAR
    return annualized_return / downside


def _calmar_ratio(cagr: float | None, maximum_drawdown: float | None) -> float | None:
    if cagr is None or maximum_drawdown in (None, 0):
        return None
    return cagr / abs(maximum_drawdown)


def _benchmark_metrics(
    symbol: str,
    stock_history: list[dict[str, Any]],
    stock_cagr: float | None,
    benchmark_symbol: str | None = None,
) -> dict[str, Any] | None:
    benchmark_symbol = benchmark_symbol or _benchmark_symbol(symbol)
    try:
        benchmark_ticker = get_market_data_provider().ticker(benchmark_symbol)
        history = retry_call(
            lambda: benchmark_ticker.history(
                period="5y", interval="1d", auto_adjust=False, timeout=15
            ),
            operation_name=f"retrieve benchmark history for {benchmark_symbol}",
        )
    except Exception as exc:  # noqa: BLE001 - upstream errors vary by yfinance endpoint.
        logger.warning("Benchmark unavailable for %s: %s", symbol, exc)
        return None

    if history is None or not isinstance(history, pd.DataFrame) or history.empty:
        return None

    benchmark_records: list[dict[str, Any]] = []
    for timestamp, row in history.iterrows():
        record_date = pd.Timestamp(timestamp).date()
        close = _safe_float(row.get("Adj Close")) or _safe_float(row.get("Close"))
        if close is not None and close > 0:
            benchmark_records.append({"date": record_date, "close": close})

    aligned = align_histories(stock_history, benchmark_records)
    if len(aligned) < 2:
        if len(benchmark_records) < 2:
            return None
        benchmark_return = (
            benchmark_records[-1]["close"] / benchmark_records[0]["close"] - 1
        )
        return {
            "symbol": benchmark_symbol,
            "one_year_return": benchmark_return,
            "relative_performance": (
                stock_cagr - benchmark_return if stock_cagr is not None else None
            ),
            "alpha": None,
            "beta": None,
        }

    benchmark_closes = [item[2] for item in aligned]
    benchmark_returns = [
        benchmark_closes[index] / benchmark_closes[index - 1] - 1
        for index in range(1, len(benchmark_closes))
    ]
    stock_aligned_closes = [item[1] for item in aligned]
    aligned_stock_returns = [
        stock_aligned_closes[index] / stock_aligned_closes[index - 1] - 1
        for index in range(1, len(stock_aligned_closes))
    ]
    if len(benchmark_returns) != len(aligned_stock_returns):
        return None
    benchmark_return = benchmark_closes[-1] / benchmark_closes[0] - 1
    benchmark_cagr = _annualized_return(
        [{"date": item[0], "close": item[2]} for item in aligned]
    )
    benchmark_variance = statistics.pvariance(benchmark_returns)
    beta = None
    if len(benchmark_returns) >= 2 and benchmark_variance > 0:
        beta = (
            statistics.covariance(aligned_stock_returns, benchmark_returns)
            / benchmark_variance
        )
    alpha = (
        stock_cagr - (RISK_FREE_RATE + beta * (benchmark_cagr - RISK_FREE_RATE))
        if stock_cagr is not None and beta is not None and benchmark_cagr is not None
        else None
    )
    return {
        "symbol": benchmark_symbol,
        "one_year_return": benchmark_return,
        "relative_performance": (
            stock_cagr - benchmark_cagr
            if stock_cagr is not None and benchmark_cagr is not None
            else None
        ),
        "alpha": alpha,
        "beta": beta,
    }


def _benchmark_symbol(symbol: str) -> str:
    return "^TWII" if symbol.endswith(".TW") else "^GSPC"


def _get_benchmark_return(
    symbol: str, stock_return: float | None
) -> dict[str, Any] | None:
    benchmark_symbol = _benchmark_symbol(symbol)
    try:
        history = yf.Ticker(benchmark_symbol).history(period="1y", interval="1d")
    except Exception as exc:  # noqa: BLE001 - upstream errors vary by yfinance endpoint.
        logger.warning("Benchmark unavailable for %s: %s", symbol, exc)
        return None

    if history is None or not isinstance(history, pd.DataFrame) or history.empty:
        logger.warning("Benchmark returned no data for %s", benchmark_symbol)
        return None

    closes: list[tuple[date, float]] = []
    for timestamp, row in history.iterrows():
        close = _safe_float(row.get("Close"))
        if close is None or close <= 0:
            continue
        try:
            record_date = pd.Timestamp(timestamp).date()
        except (TypeError, ValueError):
            continue
        closes.append((record_date, close))

    if len(closes) < 2 or closes[0][1] == 0:
        return None

    benchmark_return = closes[-1][1] / closes[0][1] - 1
    return {
        "symbol": benchmark_symbol,
        "one_year_return": benchmark_return,
        "relative_performance": (
            stock_return - benchmark_return if stock_return is not None else None
        ),
    }


def get_stock_analytics(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    benchmark: str | None = None,
) -> dict[str, Any]:
    stock_data = get_stock_data(symbol, period=period, interval=interval)
    normalized_symbol = stock_data["symbol"]
    history = _ordered_history(stock_data["history"])
    if not history:
        raise StockNotFound(f"No usable market data found for {normalized_symbol}")

    daily_returns = _daily_returns(history)
    numeric_returns = [
        record["daily_return"]
        for record in daily_returns
        if record["daily_return"] is not None
    ]
    end_date = history[-1]["date"]
    one_year_return = _period_return(history, 12)
    cagr = _annualized_return(history)
    maximum_drawdown = _maximum_drawdown(history)
    benchmark_data = _benchmark_metrics(normalized_symbol, history, cagr, benchmark)
    missing_fields = [
        name
        for name, value in {
            "annualized_volatility": _volatility(numeric_returns),
            "maximum_drawdown": maximum_drawdown,
            "sharpe_ratio": _sharpe_ratio(numeric_returns),
            "downside_volatility": _downside_volatility(numeric_returns),
            "sortino_ratio": _sortino_ratio(numeric_returns),
            "calmar_ratio": _calmar_ratio(cagr, maximum_drawdown),
            "cagr": cagr,
            "benchmark": benchmark_data,
        }.items()
        if value is None
    ]

    return {
        "symbol": normalized_symbol,
        "data_status": {
            "status": "partial" if missing_fields else "available",
            "source": DATA_SOURCE,
            "as_of": end_date,
            "message": "部分量化指標因可用資料不足而無法計算。"
            if missing_fields
            else None,
            "missing_fields": missing_fields,
        },
        "daily_returns": daily_returns,
        "period_returns": {
            "one_week": _return_from_date(history, end_date - timedelta(days=7)),
            "one_month": _period_return(history, 1),
            "three_months": _period_return(history, 3),
            "six_months": _period_return(history, 6),
            "ytd": _return_from_date(history, date(end_date.year, 1, 1)),
            "one_year": one_year_return,
            "three_years": _period_return(history, 36),
            "five_years": _period_return(history, 60),
        },
        "annualized_volatility": _volatility(numeric_returns),
        "maximum_drawdown": maximum_drawdown,
        "moving_averages": _moving_averages(history),
        "risk_free_rate": RISK_FREE_RATE,
        "sharpe_ratio": _sharpe_ratio(numeric_returns),
        "downside_volatility": _downside_volatility(numeric_returns),
        "sortino_ratio": _sortino_ratio(numeric_returns),
        "calmar_ratio": _calmar_ratio(cagr, maximum_drawdown),
        "cagr": cagr,
        "alpha": benchmark_data.get("alpha") if benchmark_data else None,
        "beta": benchmark_data.get("beta") if benchmark_data else None,
        "benchmark": benchmark_data,
    }
