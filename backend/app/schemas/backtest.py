from datetime import date

from pydantic import BaseModel, Field


class BacktestMetric(BaseModel):
    cagr: float | None = None
    volatility: float | None = None
    sharpe: float | None = None
    maximum_drawdown: float | None = None
    hit_rate: float | None = None
    observations: int = 0


class BacktestRecommendation(BaseModel):
    symbol: str
    score: float
    rank: int
    latest_as_of: date
    features: dict[str, float | None]
    label: str


class BacktestResponse(BaseModel):
    symbols: list[str]
    benchmark: str | None = None
    period: str
    horizon_months: int
    rebalance: str
    trained_from: date | None = None
    tested_from: date | None = None
    tested_to: date | None = None
    weights: dict[str, float] = Field(default_factory=dict)
    train: BacktestMetric
    test: BacktestMetric
    benchmark_test: BacktestMetric | None = None
    recommendations: list[BacktestRecommendation]
    data_quality: dict[str, str | int | float | list[str] | None] = Field(
        default_factory=dict
    )
