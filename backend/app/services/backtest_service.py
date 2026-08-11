"""Explainable, price-based walk-forward formula research.

This is deliberately a small baseline. It ranks momentum and risk features using
only information available at each rebalance date, trains weights on the past,
and evaluates the selected formula on a later out-of-sample period.
"""

from __future__ import annotations

import itertools
import math
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Any

from app.services.fundamentals_service import get_fundamentals
from app.services.stock_service import (
    StockDataUnavailable,
    StockNotFound,
    get_stock_data,
)

FEATURES = (
    "momentum_3m",
    "momentum_6m",
    "momentum_12m",
    "low_volatility",
    "low_drawdown",
    "revenue_growth",
    "roic",
    "net_margin",
    "current_ratio",
    "low_debt_to_equity",
    "low_pe",
)
MAX_BACKTEST_SYMBOLS = 20
HORIZON_MONTHS = {"1m": 1, "3m": 3, "6m": 6, "12m": 12}


def _months(history: list[dict[str, Any]]) -> list[tuple[date, float]]:
    latest: dict[tuple[int, int], tuple[date, float]] = {}
    for record in history:
        record_date = record.get("date")
        close = record.get("adjusted_close", record.get("close"))
        if (
            isinstance(record_date, date)
            and isinstance(close, (int, float))
            and math.isfinite(float(close))
            and close > 0
        ):
            latest[(record_date.year, record_date.month)] = (record_date, float(close))
    return sorted(latest.values())


def _fundamental_snapshots(fundamentals: dict[str, Any]) -> list[dict[str, Any]]:
    """Build annual factor snapshots with a conservative 90-day availability lag."""
    income = sorted(
        fundamentals.get("income_statement", []),
        key=lambda row: row.get("period", date.min),
    )
    balances = {row.get("period"): row for row in fundamentals.get("balance_sheet", [])}
    snapshots: list[dict[str, Any]] = []
    for index, current in enumerate(income):
        period = current.get("period")
        if not isinstance(period, date):
            continue
        previous = income[index - 1] if index else {}
        balance = balances.get(period, {})
        previous_balance = balances.get(previous.get("period"), {})
        revenue = current.get("revenue")
        equity = balance.get("equity")
        average_equity = _average(equity, previous_balance.get("equity"))
        average_debt = _average(balance.get("debt"), previous_balance.get("debt"))
        average_cash = _average(balance.get("cash"), previous_balance.get("cash"))
        invested_capital = (
            average_debt + average_equity - average_cash
            if average_debt is not None
            and average_equity is not None
            and average_cash is not None
            else None
        )
        tax_rate = _ratio(current.get("tax_provision"), current.get("pretax_income"))
        nopat = (
            current.get("operating_income") * (1 - tax_rate)
            if current.get("operating_income") is not None and tax_rate is not None
            else None
        )
        snapshots.append(
            {
                "available_as_of": period + timedelta(days=90),
                "revenue_growth": _growth(revenue, previous.get("revenue")),
                "roic": _ratio(nopat, invested_capital),
                "net_margin": _ratio(current.get("net_income"), revenue),
                "current_ratio": _ratio(
                    balance.get("current_assets"), balance.get("current_liabilities")
                ),
                "low_debt_to_equity": _inverse_ratio(balance.get("debt"), equity),
                "low_pe": _inverse_ratio(None, None),
                "eps": current.get("eps"),
            }
        )
    return snapshots


def _average(current: float | None, previous: float | None) -> float | None:
    if current is None:
        return None
    return current if previous is None else (current + previous) / 2


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _growth(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return current / previous - 1


def _inverse_ratio(numerator: float | None, denominator: float | None) -> float | None:
    ratio = _ratio(numerator, denominator)
    return -ratio if ratio is not None and ratio > 0 else None


def _snapshot_at(
    snapshots: list[dict[str, Any]], observation_date: date
) -> dict[str, Any]:
    available = [row for row in snapshots if row["available_as_of"] <= observation_date]
    return max(available, key=lambda row: row["available_as_of"]) if available else {}


def _feature(
    values: list[tuple[date, float]],
    index: int,
    snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, float | None] | None:
    if index < 12:
        return None
    current = values[index][1]

    def return_for(months: int) -> float:
        return current / values[index - months][1] - 1

    window = [
        values[item][1] / values[item - 1][1] - 1
        for item in range(index - 3 + 1, index + 1)
    ]
    peak = max(value for _, value in values[index - 12 : index + 1])
    drawdown = current / peak - 1
    volatility = statistics.stdev(window) * math.sqrt(12) if len(window) >= 2 else 0.0
    fundamental = _snapshot_at(snapshots or [], values[index][0])
    return {
        "momentum_3m": return_for(3),
        "momentum_6m": return_for(6),
        "momentum_12m": return_for(12),
        "low_volatility": -volatility,
        "low_drawdown": drawdown,
        "revenue_growth": fundamental.get("revenue_growth"),
        "roic": fundamental.get("roic"),
        "net_margin": fundamental.get("net_margin"),
        "current_ratio": fundamental.get("current_ratio"),
        "low_debt_to_equity": fundamental.get("low_debt_to_equity"),
        "low_pe": _inverse_ratio(values[index][1], fundamental.get("eps")),
    }


def _observations(
    histories: dict[str, list[tuple[date, float]]],
    fundamentals: dict[str, list[dict[str, Any]]],
    horizon: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for symbol, values in histories.items():
        for index in range(12, len(values) - horizon):
            features = _feature(values, index, fundamentals.get(symbol, []))
            if features is None:
                continue
            future_return = values[index + horizon][1] / values[index][1] - 1
            result.append(
                {
                    "symbol": symbol,
                    "date": values[index][0],
                    "features": features,
                    "future_return": future_return,
                }
            )
    return result


def _percentile(values: list[float | None], value: float | None) -> float | None:
    usable = [
        item
        for item in values
        if isinstance(item, (int, float)) and math.isfinite(float(item))
    ]
    if value is None or not usable:
        return None
    if len(usable) <= 1:
        return 50.0
    return sum(item <= value for item in usable) / len(usable) * 100


def _scores(observations: list[dict[str, Any]], weights: dict[str, float]) -> None:
    by_date: dict[date, list[dict[str, Any]]] = {}
    for observation in observations:
        by_date.setdefault(observation["date"], []).append(observation)
    for rows in by_date.values():
        for feature in FEATURES:
            values = [row["features"].get(feature) for row in rows]
            for row in rows:
                percentile = _percentile(values, row["features"].get(feature))
                if percentile is not None:
                    row["score"] = (
                        row.get("score", 0.0) + weights[feature] * percentile / 100
                    )
                    row["available_weight"] = (
                        row.get("available_weight", 0.0) + weights[feature]
                    )
        for row in rows:
            available_weight = row.get("available_weight", 0.0)
            row["score"] = (
                row.get("score", 0.0) / available_weight if available_weight else 0.5
            )


def _portfolio_returns(
    observations: list[dict[str, Any]],
    weights: dict[str, float],
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> list[float]:
    copied = [dict(row) for row in observations]
    _scores(copied, weights)
    by_date: dict[date, list[dict[str, Any]]] = {}
    for row in copied:
        by_date.setdefault(row["date"], []).append(row)
    returns: list[float] = []
    previous_symbol: str | None = None
    friction = (transaction_cost_bps + slippage_bps) / 10_000
    for rows in sorted(by_date.values(), key=lambda group: group[0]["date"]):
        selected = max(rows, key=lambda row: row["score"])
        cost = friction if selected["symbol"] != previous_symbol else 0.0
        returns.append((1 + selected["future_return"]) * (1 - cost) - 1)
        previous_symbol = selected["symbol"]
    return returns


def _metrics(returns: list[float]) -> dict[str, Any]:
    if not returns:
        return {
            "cagr": None,
            "volatility": None,
            "sharpe": None,
            "maximum_drawdown": None,
            "hit_rate": None,
            "observations": 0,
        }
    growth = 1.0
    peak = 1.0
    drawdown = 0.0
    for value in returns:
        growth *= 1 + value
        peak = max(peak, growth)
        drawdown = min(drawdown, growth / peak - 1)
    years = len(returns) / 12
    average = statistics.fmean(returns)
    volatility = (
        statistics.stdev(returns) * math.sqrt(12) if len(returns) >= 2 else None
    )
    return {
        "cagr": growth ** (1 / years) - 1 if years > 0 and growth > 0 else None,
        "volatility": volatility,
        "sharpe": average / statistics.stdev(returns) * math.sqrt(12)
        if volatility not in (None, 0)
        else None,
        "maximum_drawdown": drawdown,
        "hit_rate": sum(value > 0 for value in returns) / len(returns),
        "observations": len(returns),
    }


def _weight_grid() -> list[dict[str, float]]:
    grid = []
    for values in itertools.product((0.0, 0.25, 0.5, 0.75, 1.0), repeat=len(FEATURES)):
        if math.isclose(sum(values), 1.0):
            grid.append(dict(zip(FEATURES, values, strict=True)))
    return grid


def _load(
    symbol: str, period: str
) -> tuple[str, list[tuple[date, float]], list[dict[str, Any]]]:
    data = get_stock_data(symbol, period=period, interval="1mo")
    try:
        fundamentals = get_fundamentals(symbol)
    except (StockDataUnavailable, StockNotFound, RuntimeError):
        fundamentals = {}
    return (
        data["symbol"],
        _months(data["history"]),
        _fundamental_snapshots(fundamentals),
    )


def run_backtest(
    symbols: list[str],
    period: str = "10y",
    horizon: str = "3m",
    benchmark: str | None = None,
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    horizon_months = HORIZON_MONTHS[horizon]
    with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as executor:
        loaded = list(executor.map(lambda symbol: _load(symbol, period), symbols))
    histories = {symbol: values for symbol, values, _ in loaded if len(values) >= 18}
    fundamentals = {symbol: snapshots for symbol, _, snapshots in loaded}
    if len(histories) < 2:
        raise StockNotFound("Not enough historical data for a multi-stock backtest")
    observations = _observations(histories, fundamentals, horizon_months)
    dates = sorted({row["date"] for row in observations})
    if len(dates) < 24:
        raise ValueError("Backtest needs at least 24 monthly observations")
    train_end = dates[len(dates) * 3 // 5]
    test_start = dates[len(dates) * 4 // 5]
    train_rows = [row for row in observations if row["date"] < train_end]
    test_rows = [row for row in observations if row["date"] >= test_start]
    candidates = [
        (
            weights,
            _metrics(
                _portfolio_returns(
                    train_rows,
                    weights,
                    transaction_cost_bps,
                    slippage_bps,
                )
            )["cagr"]
            or -1,
        )
        for weights in _weight_grid()
    ]
    weights = max(candidates, key=lambda item: item[1])[0]
    latest_date = max(dates)
    latest_rows = [row for row in observations if row["date"] == latest_date]
    _scores(latest_rows, weights)
    ranked = sorted(latest_rows, key=lambda row: row.get("score", 0), reverse=True)
    recommendations = [
        {
            "symbol": row["symbol"],
            "score": round(row["score"] * 100, 2),
            "rank": index,
            "latest_as_of": row["date"],
            "features": row["features"],
            "label": "Candidate" if index == 1 else "Watchlist",
        }
        for index, row in enumerate(ranked, start=1)
    ]
    return {
        "symbols": list(histories),
        "benchmark": benchmark,
        "period": period,
        "horizon_months": horizon_months,
        "rebalance": "monthly",
        "trained_from": min(dates),
        "tested_from": min((row["date"] for row in test_rows), default=None),
        "tested_to": max((row["date"] for row in test_rows), default=None),
        "weights": weights,
        "train": _metrics(
            _portfolio_returns(train_rows, weights, transaction_cost_bps, slippage_bps)
        ),
        "test": _metrics(
            _portfolio_returns(test_rows, weights, transaction_cost_bps, slippage_bps)
        ),
        "benchmark_test": None,
        "recommendations": recommendations,
        "data_quality": {
            "source": "Yahoo Finance via yfinance",
            "symbols_loaded": len(histories),
            "symbols_missing": [
                symbol for symbol in symbols if symbol not in histories
            ],
            "fundamental_snapshots": sum(
                bool(fundamentals.get(symbol)) for symbol in histories
            ),
            "fundamental_lag_days": 90,
            "transaction_cost_bps": transaction_cost_bps,
            "slippage_bps": slippage_bps,
        },
    }
