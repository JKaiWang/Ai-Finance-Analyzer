from app.services.research_service import build_research_outputs, score_metric


def test_score_metric_ranks_higher_values_and_excludes_missing_values() -> None:
    companies = [
        {"symbol": "AAA", "revenue_growth": 0.30},
        {"symbol": "BBB", "revenue_growth": 0.10},
        {"symbol": "CCC", "revenue_growth": None},
    ]

    scores = score_metric(companies, "revenue_growth")

    assert scores["AAA"]["score"] == 100.0
    assert scores["BBB"]["score"] == 50.0
    assert scores["CCC"]["score"] is None
    assert scores["CCC"]["reason"] == "provider_unavailable_or_not_applicable"


def test_score_metric_inverts_valuation_direction() -> None:
    companies = [
        {"symbol": "CHEAP", "price_to_earnings": 10},
        {"symbol": "EXPENSIVE", "price_to_earnings": 30},
    ]

    scores = score_metric(companies, "price_to_earnings")

    assert scores["CHEAP"]["score"] == 100.0
    assert scores["EXPENSIVE"]["score"] == 50.0


def test_score_metric_accepts_explicit_ranking_direction_and_ignores_nan() -> None:
    companies = [
        {"symbol": "AAA", "annualized_volatility": 0.10},
        {"symbol": "BBB", "annualized_volatility": 0.20},
        {"symbol": "CCC", "annualized_volatility": float("nan")},
    ]

    scores = score_metric(companies, "annualized_volatility", "asc")

    assert scores["AAA"]["score"] == 100.0
    assert scores["BBB"]["score"] == 50.0
    assert scores["CCC"]["score"] is None
    assert scores["AAA"]["sample_size"] == 2


def test_build_research_outputs_contains_radar_heatmap_and_summary() -> None:
    companies = [
        {
            "symbol": "AAA",
            "revenue_growth": 0.30,
            "gross_margin": 0.70,
            "price_to_earnings": 10,
            "annualized_volatility": 0.20,
            "current_ratio": 2.0,
            "one_year_return": 0.40,
        },
        {
            "symbol": "BBB",
            "revenue_growth": 0.10,
            "gross_margin": 0.40,
            "price_to_earnings": 30,
            "annualized_volatility": 0.40,
            "current_ratio": 1.0,
            "one_year_return": 0.10,
        },
    ]

    outputs = build_research_outputs(companies)

    assert outputs[0]["factor_scores"]["growth"] is not None
    assert outputs[0]["heatmap"]["revenue_growth"]["state"] == "available"
    assert outputs[0]["research_summary"]["disclaimer"]
