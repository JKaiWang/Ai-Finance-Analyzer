from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services.backtest_service import (
    _feature,
    _fundamental_snapshots,
    _metrics,
    _weight_grid,
)

client = TestClient(app)


def test_feature_uses_only_history_before_observation() -> None:
    values = [
        (date(2020 + index // 12, index % 12 + 1, 1), 100 + index)
        for index in range(16)
    ]
    features = _feature(values, 12)
    assert features is not None
    assert features["momentum_3m"] > 0
    assert set(features) == {
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
    }


def test_weight_grid_is_normalized() -> None:
    assert _weight_grid()
    assert all(sum(weights.values()) == 1 for weights in _weight_grid())


def test_metrics_preserve_empty_series_as_unavailable() -> None:
    metrics = _metrics([])
    assert metrics["observations"] == 0
    assert metrics["cagr"] is None


def test_fundamental_snapshot_is_not_available_until_reporting_lag() -> None:
    snapshots = _fundamental_snapshots(
        {
            "income_statement": [
                {
                    "period": date(2024, 12, 31),
                    "revenue": 200.0,
                    "net_income": 20.0,
                    "operating_income": 30.0,
                    "tax_provision": 5.0,
                    "pretax_income": 25.0,
                    "eps": 2.0,
                },
                {
                    "period": date(2023, 12, 31),
                    "revenue": 100.0,
                    "net_income": 10.0,
                    "operating_income": 15.0,
                    "tax_provision": 2.0,
                    "pretax_income": 12.0,
                    "eps": 1.0,
                },
            ],
            "balance_sheet": [
                {
                    "period": date(2024, 12, 31),
                    "debt": 20.0,
                    "equity": 100.0,
                    "cash": 10.0,
                    "current_assets": 150.0,
                    "current_liabilities": 75.0,
                },
                {
                    "period": date(2023, 12, 31),
                    "debt": 10.0,
                    "equity": 80.0,
                    "cash": 8.0,
                },
            ],
        }
    )
    assert snapshots[0]["available_as_of"] == date(2024, 3, 30)
    assert snapshots[0]["revenue_growth"] is None
    assert snapshots[1]["available_as_of"] == date(2025, 3, 31)
    assert snapshots[1]["revenue_growth"] is not None


def test_backtest_endpoint_validates_symbol_count() -> None:
    response = client.get("/backtest?symbols=NVDA")
    assert response.status_code == 400
    assert "至少需要兩支" in response.json()["detail"]


def test_backtest_endpoint_returns_formula_and_oos_metrics(monkeypatch) -> None:
    def fake_run_backtest(
        symbols,
        period="10y",
        horizon="3m",
        benchmark=None,
        transaction_cost_bps=10.0,
        slippage_bps=5.0,
    ):
        return {
            "symbols": symbols,
            "benchmark": benchmark,
            "period": period,
            "horizon_months": 3,
            "rebalance": "monthly",
            "trained_from": date(2018, 1, 1),
            "tested_from": date(2024, 1, 1),
            "tested_to": date(2025, 1, 1),
            "weights": {"momentum_3m": 1.0},
            "train": _metrics([0.1, 0.2]),
            "test": _metrics([0.05, -0.01]),
            "benchmark_test": None,
            "recommendations": [
                {
                    "symbol": symbols[0],
                    "score": 82.0,
                    "rank": 1,
                    "latest_as_of": date(2025, 1, 1),
                    "features": {},
                    "label": "Candidate",
                }
            ],
            "data_quality": {
                "source": "test",
                "symbols_loaded": 2,
                "symbols_missing": [],
            },
        }

    monkeypatch.setattr("app.main.run_backtest", fake_run_backtest)
    response = client.get("/backtest?symbols=NVDA,AMD&horizon=3m")
    assert response.status_code == 200
    assert response.json()["test"]["observations"] == 2
    assert response.json()["recommendations"][0]["label"] == "Candidate"
