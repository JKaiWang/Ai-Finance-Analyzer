"""Peer-relative scoring and deterministic research outputs for comparisons."""

from __future__ import annotations

import math
from typing import Any

MIN_SAMPLE_SIZE = 2

RANKING_DIRECTIONS = {
    "revenue_growth": "desc",
    "eps": "desc",
    "eps_growth": "desc",
    "net_income_growth": "desc",
    "free_cash_flow_growth": "desc",
    "gross_margin": "desc",
    "operating_margin": "desc",
    "ebitda_margin": "desc",
    "net_margin": "desc",
    "roe": "desc",
    "roa": "desc",
    "roic": "desc",
    "current_ratio": "desc",
    "quick_ratio": "desc",
    "cash_ratio": "desc",
    "interest_coverage": "desc",
    "free_cash_flow_margin": "desc",
    "free_cash_flow": "desc",
    "sharpe_ratio": "desc",
    "sortino_ratio": "desc",
    "calmar_ratio": "desc",
    "beta": "asc",
    "cagr": "desc",
    "one_year_return": "desc",
    "alpha": "desc",
    "maximum_drawdown": "desc",
    "annualized_volatility": "asc",
    "downside_volatility": "asc",
    "debt_to_equity": "asc",
    "price_to_earnings": "asc",
    "forward_pe": "asc",
    "peg_ratio": "asc",
    "price_to_book": "asc",
    "price_to_sales": "asc",
    "enterprise_to_ebitda": "asc",
    "enterprise_to_revenue": "asc",
}

FACTOR_METRICS = {
    "growth": (
        "revenue_growth",
        "eps_growth",
        "net_income_growth",
        "free_cash_flow_growth",
    ),
    "profitability": (
        "gross_margin",
        "operating_margin",
        "ebitda_margin",
        "net_margin",
        "roe",
        "roa",
        "roic",
    ),
    "valuation": (
        "price_to_earnings",
        "forward_pe",
        "peg_ratio",
        "price_to_book",
        "price_to_sales",
        "enterprise_to_ebitda",
        "enterprise_to_revenue",
    ),
    "risk": (
        "annualized_volatility",
        "downside_volatility",
        "maximum_drawdown",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
    ),
    "financial_health": (
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "debt_to_equity",
        "interest_coverage",
        "free_cash_flow_margin",
    ),
    "momentum": ("one_year_return", "cagr", "alpha"),
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _rank_score(value: float, values: list[float], direction: str) -> float:
    if len(values) < MIN_SAMPLE_SIZE:
        return 50.0
    if direction == "desc":
        rank = sum(item <= value for item in values)
    elif direction == "asc":
        rank = sum(item >= value for item in values)
    else:
        raise ValueError("Ranking direction must be 'asc' or 'desc'.")
    return rank / len(values) * 100


def score_metric(
    companies: list[dict[str, Any]], metric: str, direction: str | None = None
) -> dict[str, dict[str, Any]]:
    """Return scores for one metric, excluding missing values from the peer set."""
    direction = direction or RANKING_DIRECTIONS.get(metric, "desc")
    values = {company["symbol"]: _number(company.get(metric)) for company in companies}
    available = [value for value in values.values() if value is not None]
    sample_size = len(available)
    result: dict[str, dict[str, Any]] = {}
    for symbol, value in values.items():
        if value is None:
            result[symbol] = {
                "value": None,
                "score": None,
                "percentile": None,
                "sample_size": sample_size,
                "confidence": "unavailable",
                "reason": "provider_unavailable_or_not_applicable",
            }
            continue
        if sample_size < MIN_SAMPLE_SIZE:
            result[symbol] = {
                "value": value,
                "score": None,
                "percentile": None,
                "sample_size": sample_size,
                "confidence": "low",
                "reason": "insufficient_peer_sample",
            }
            continue
        score = _rank_score(value, available, direction)
        confidence = (
            "high"
            if sample_size >= 4
            else "medium"
            if sample_size >= MIN_SAMPLE_SIZE
            else "low"
        )
        result[symbol] = {
            "value": value,
            "score": round(score, 2),
            "percentile": round(score, 2),
            "sample_size": sample_size,
            "confidence": confidence,
            "reason": None
            if sample_size >= MIN_SAMPLE_SIZE
            else "insufficient_peer_sample",
        }
    return result


def _average_metric_scores(
    peer_scores: dict[str, dict[str, Any]], metrics: tuple[str, ...], symbol: str
) -> float | None:
    scores = [
        peer_scores[metric][symbol]["score"]
        for metric in metrics
        if peer_scores[metric][symbol]["score"] is not None
    ]
    return round(sum(scores) / len(scores), 2) if scores else None


def _summary(
    company: dict[str, Any],
    factor_scores: dict[str, float | None],
    peer_scores: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    symbol = company["symbol"]
    strengths: list[dict[str, Any]] = []
    weaknesses: list[dict[str, Any]] = []

    for factor, score in factor_scores.items():
        if score is not None and score >= 80:
            strengths.append(
                {
                    "factor": factor,
                    "reason": "factor_score_at_or_above_80",
                    "score": score,
                }
            )
        if score is not None and score <= 25:
            weaknesses.append(
                {
                    "factor": factor,
                    "reason": "factor_score_at_or_below_25",
                    "score": score,
                }
            )

    for metric in ("roic", "revenue_growth", "free_cash_flow_growth"):
        item = peer_scores[metric][symbol]
        if item["score"] is not None and item["score"] >= 75:
            strengths.append(
                {
                    "factor": metric,
                    "reason": "peer_percentile_at_or_above_75",
                    "score": item["score"],
                }
            )
        if item["score"] is not None and item["score"] <= 25:
            weaknesses.append(
                {
                    "factor": metric,
                    "reason": "peer_percentile_at_or_below_25",
                    "score": item["score"],
                }
            )

    if (
        _number(company.get("free_cash_flow_growth")) is not None
        and company["free_cash_flow_growth"] < 0
    ):
        weaknesses.append(
            {
                "factor": "free_cash_flow_growth",
                "reason": "negative_growth",
                "score": peer_scores["free_cash_flow_growth"][symbol]["score"],
            }
        )

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "disclaimer": (
            "This is a deterministic comparison summary, not investment advice. "
            "Missing data is not treated as zero."
        ),
    }


def build_research_outputs(
    companies: list[dict[str, Any]],
    ranking_directions: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Add metric scores, six-factor scores, heatmap cells, and summary to companies."""
    directions = {**RANKING_DIRECTIONS, **(ranking_directions or {})}
    invalid = {
        metric: direction
        for metric, direction in directions.items()
        if direction not in {"asc", "desc"}
    }
    if invalid:
        raise ValueError("Ranking directions must be 'asc' or 'desc'.")
    peer_scores = {
        metric: score_metric(companies, metric, directions[metric])
        for metric in directions
    }
    outputs: list[dict[str, Any]] = []
    for company in companies:
        symbol = company["symbol"]
        factor_scores = {
            factor: _average_metric_scores(peer_scores, metrics, symbol)
            for factor, metrics in FACTOR_METRICS.items()
        }
        company = {
            **company,
            "peer_scores": {
                metric: peer_scores[metric][symbol] for metric in directions
            },
            "factor_scores": factor_scores,
            "heatmap": {
                metric: {
                    "value": peer_scores[metric][symbol]["value"],
                    "score": peer_scores[metric][symbol]["score"],
                    "direction": directions[metric],
                    "state": "available"
                    if peer_scores[metric][symbol]["score"] is not None
                    else "unavailable",
                }
                for metric in directions
            },
            "research_summary": _summary(company, factor_scores, peer_scores),
        }
        outputs.append(company)
    return outputs
