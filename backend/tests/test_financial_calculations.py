import math
import statistics
from datetime import date
from unittest.mock import Mock, patch

import pandas as pd

from app.services.analytics_service import (
    TRADING_DAYS_PER_YEAR,
    _annualized_return,
    _period_return,
    _volatility,
)
from app.services.comparison_service import _price_to_earnings
from app.services.fundamentals_service import _growth, _ratio, get_fundamentals


def test_revenue_growth_and_current_ratio_use_standard_ratios() -> None:
    assert _growth(1_250.0, 1_000.0) == 0.25
    assert _ratio(1_200.0, 600.0) == 2.0
    assert _growth(1_000.0, 0.0) is None
    assert _ratio(1_200.0, 0.0) is None


def test_price_to_earnings_rejects_negative_or_missing_eps() -> None:
    assert _price_to_earnings(100.0, 5.0) == 20.0
    assert _price_to_earnings(100.0, -5.0) is None
    assert _price_to_earnings(100.0, None) is None


def test_one_year_return_uses_chronological_start_and_end_prices() -> None:
    history = [
        {"date": date(2025, 1, 1), "close": 100.0},
        {"date": date(2025, 7, 1), "close": 110.0},
        {"date": date(2026, 1, 1), "close": 125.0},
    ]

    assert _period_return(history, 12) == 0.25


def test_annualized_volatility_uses_sample_daily_std_and_sqrt_252() -> None:
    returns = [0.01, -0.005, 0.02, 0.0]

    expected = statistics.stdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR)

    assert _volatility(returns) == expected


def test_cagr_uses_elapsed_years() -> None:
    history = [
        {"date": date(2020, 1, 1), "close": 100.0},
        {"date": date(2025, 1, 1), "close": 200.0},
    ]

    assert _annualized_return(history) is not None
    assert 0.14 < _annualized_return(history) < 0.15


def test_roic_uses_after_tax_operating_income_over_invested_capital() -> None:
    current = pd.Timestamp("2025-12-31")
    previous = pd.Timestamp("2024-12-31")
    ticker = Mock()
    ticker.income_stmt = pd.DataFrame(
        {
            current: [1_000.0, 250.0, 250.0, 50.0, 200.0, 2.0],
            previous: [900.0, 220.0, 220.0, 44.0, 176.0, 1.8],
        },
        index=[
            "Total Revenue",
            "Operating Income",
            "Pretax Income",
            "Tax Provision",
            "Net Income",
            "Diluted EPS",
        ],
    )
    ticker.balance_sheet = pd.DataFrame(
        {
            current: [500.0, 1_000.0, 300.0],
            previous: [400.0, 900.0, 250.0],
        },
        index=[
            "Total Debt",
            "Stockholders Equity",
            "Cash Cash Equivalents And Short Term Investments",
        ],
    )
    ticker.cashflow = pd.DataFrame()
    ticker.info = {}

    with patch("app.services.fundamentals_service.yf.Ticker", return_value=ticker):
        result = get_fundamentals("TEST")

    # NOPAT = 250 * (1 - 50 / 250) = 200;
    # invested capital = avg debt + avg equity - avg cash = 1,125.
    assert result["profitability"]["roic"] == 200 / 1_125
