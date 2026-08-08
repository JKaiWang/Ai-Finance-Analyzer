from datetime import date as date_type

from pydantic import BaseModel, Field


class DailyReturnRecord(BaseModel):
    date: date_type = Field(description="交易日期。")
    daily_return: float | None = Field(
        description="相對前一交易日收盤價的報酬率；第一筆資料為 null。"
    )


class PeriodReturns(BaseModel):
    one_week: float | None = Field(default=None, description="近一週報酬率。")
    one_month: float | None = Field(default=None, description="近一個月報酬率。")
    three_months: float | None = Field(default=None, description="近三個月報酬率。")
    six_months: float | None = Field(default=None, description="近六個月報酬率。")
    ytd: float | None = Field(default=None, description="今年以來報酬率。")
    one_year: float | None = Field(default=None, description="近一年報酬率。")
    three_years: float | None = Field(default=None, description="近三年報酬率。")
    five_years: float | None = Field(default=None, description="近五年報酬率。")


class MovingAverageRecord(BaseModel):
    date: date_type = Field(description="交易日期。")
    ma20: float | None = Field(default=None, description="20 日移動平均線。")
    ma50: float | None = Field(default=None, description="50 日移動平均線。")
    ma200: float | None = Field(default=None, description="200 日移動平均線。")


class BenchmarkComparison(BaseModel):
    symbol: str = Field(description="Benchmark 代號。")
    one_year_return: float | None = Field(
        default=None, description="Benchmark 近一年報酬率。"
    )
    relative_performance: float | None = Field(
        default=None, description="股票近一年報酬率減去 Benchmark 報酬率。"
    )


class AnalyticsResponse(BaseModel):
    symbol: str = Field(description="股票代號。")
    daily_returns: list[DailyReturnRecord] = Field(description="每日報酬率序列。")
    period_returns: PeriodReturns = Field(description="不同期間的累積報酬率。")
    annualized_volatility: float | None = Field(
        default=None, description="以 252 個交易日年化的波動率。"
    )
    maximum_drawdown: float | None = Field(
        default=None, description="歷史價格序列的最大回撤。"
    )
    moving_averages: list[MovingAverageRecord] = Field(
        description="MA20、MA50、MA200 序列。"
    )
    risk_free_rate: float = Field(description="Sharpe Ratio 使用的年化無風險利率。")
    sharpe_ratio: float | None = Field(default=None, description="年化 Sharpe Ratio。")
    downside_volatility: float | None = Field(
        default=None, description="年化下行波動率。"
    )
    sortino_ratio: float | None = Field(
        default=None, description="年化 Sortino Ratio。"
    )
    calmar_ratio: float | None = Field(
        default=None, description="CAGR 除以最大回撤絕對值。"
    )
    cagr: float | None = Field(
        default=None, description="完整可用期間的年化複合報酬率。"
    )
    alpha: float | None = Field(
        default=None, description="相對 Benchmark 的 CAPM Alpha。"
    )
    beta: float | None = Field(default=None, description="相對 Benchmark 的 Beta。")
    benchmark: BenchmarkComparison | None = Field(
        default=None, description="與對應市場 Benchmark 的比較結果。"
    )
