from datetime import date as date_type

from pydantic import BaseModel, Field


class NormalizedPriceRecord(BaseModel):
    date: date_type = Field(description="交易日期。")
    value: float = Field(description="以第一個有效收盤價標準化為 100 的價格。")


class PeerScore(BaseModel):
    value: float | None = None
    score: float | None = None
    percentile: float | None = None
    sample_size: int = 0
    confidence: str
    reason: str | None = None


class HeatmapCell(BaseModel):
    value: float | None = None
    score: float | None = None
    direction: str
    state: str


class ResearchPoint(BaseModel):
    factor: str
    reason: str
    score: float | None = None


class ResearchSummary(BaseModel):
    strengths: list[ResearchPoint]
    weaknesses: list[ResearchPoint]
    disclaimer: str


class TrendPoint(BaseModel):
    period: str
    value: float | None = None


class ComparisonCompany(BaseModel):
    symbol: str = Field(description="標準化後的股票代號。")
    company_name: str | None = Field(default=None, description="公司名稱。")
    sector: str | None = Field(default=None, description="產業部門。")
    industry: str | None = Field(default=None, description="細分產業。")
    country: str | None = Field(default=None, description="公司所在國家。")
    exchange: str | None = Field(default=None, description="交易所。")
    currency: str | None = Field(default=None, description="報價幣別。")
    current_price: float | None = Field(default=None, description="目前價格。")
    market_cap: int | None = Field(default=None, description="公司市值。")
    enterprise_value: int | None = Field(default=None, description="企業價值。")
    one_week_return: float | None = None
    one_month_return: float | None = None
    three_month_return: float | None = None
    six_month_return: float | None = None
    ytd_return: float | None = None
    one_year_return: float | None = Field(default=None, description="近一年報酬率。")
    three_year_return: float | None = None
    five_year_return: float | None = None
    annualized_volatility: float | None = Field(
        default=None, description="年化波動率。"
    )
    maximum_drawdown: float | None = Field(default=None, description="最大回撤。")
    sharpe_ratio: float | None = Field(default=None, description="Sharpe Ratio。")
    downside_volatility: float | None = Field(default=None, description="下行波動率。")
    sortino_ratio: float | None = Field(default=None, description="Sortino Ratio。")
    calmar_ratio: float | None = Field(default=None, description="Calmar Ratio。")
    cagr: float | None = Field(default=None, description="年化複合報酬率。")
    alpha: float | None = Field(default=None, description="Alpha。")
    beta: float | None = Field(default=None, description="Beta。")
    revenue_growth: float | None = Field(default=None, description="營收成長率。")
    eps_growth: float | None = Field(default=None, description="EPS 成長率。")
    net_income_growth: float | None = Field(default=None, description="淨利成長率。")
    free_cash_flow_growth: float | None = Field(
        default=None, description="FCF 成長率。"
    )
    book_value_growth: float | None = Field(
        default=None, description="帳面價值成長率。"
    )
    gross_margin: float | None = Field(default=None, description="毛利率。")
    operating_margin: float | None = Field(default=None, description="營業利益率。")
    ebitda_margin: float | None = Field(default=None, description="EBITDA 利潤率。")
    net_margin: float | None = Field(default=None, description="淨利率。")
    roe: float | None = Field(default=None, description="股東權益報酬率。")
    roa: float | None = Field(default=None, description="ROA。")
    roic: float | None = Field(default=None, description="ROIC。")
    current_ratio: float | None = Field(default=None, description="流動比率。")
    quick_ratio: float | None = Field(default=None, description="速動比率。")
    cash_ratio: float | None = Field(default=None, description="現金比率。")
    debt_to_equity: float | None = Field(default=None, description="Debt/Equity。")
    interest_coverage: float | None = Field(default=None, description="利息保障倍數。")
    free_cash_flow: float | None = Field(default=None, description="最新自由現金流。")
    eps: float | None = Field(default=None, description="最新年度 EPS。")
    free_cash_flow_margin: float | None = Field(
        default=None, description="FCF 利潤率。"
    )
    price_to_earnings: float | None = Field(
        default=None, description="本益比；以目前價格除以最新年度 EPS 計算。"
    )
    forward_pe: float | None = Field(default=None, description="預估本益比。")
    peg_ratio: float | None = Field(default=None, description="PEG。")
    price_to_book: float | None = Field(default=None, description="PB。")
    price_to_sales: float | None = Field(default=None, description="PS。")
    enterprise_to_ebitda: float | None = Field(default=None, description="EV/EBITDA。")
    enterprise_to_revenue: float | None = Field(default=None, description="EV/Sales。")
    dividend_yield: float | None = Field(default=None, description="股利殖利率。")
    dividend_growth: float | None = Field(default=None, description="股利成長率。")
    payout_ratio: float | None = Field(default=None, description="配息率。")
    insider_ownership: float | None = Field(default=None, description="內部人持股。")
    institutional_ownership: float | None = Field(
        default=None, description="機構持股。"
    )
    float_shares: int | None = Field(default=None, description="可流通股數。")
    shares_outstanding: int | None = Field(default=None, description="流通在外股數。")
    normalized_history: list[NormalizedPriceRecord] = Field(
        description="標準化價格序列，第一筆有效價格為 100。"
    )
    available: bool = True
    errors: list[str] = Field(default_factory=list)
    peer_scores: dict[str, PeerScore] = Field(default_factory=dict)
    factor_scores: dict[str, float | None] = Field(default_factory=dict)
    heatmap: dict[str, HeatmapCell] = Field(default_factory=dict)
    research_summary: ResearchSummary | None = None
    financial_trends: dict[str, list[TrendPoint]] = Field(default_factory=dict)


class ComparisonResponse(BaseModel):
    symbols: list[str] = Field(description="比較的股票代號。")
    period: str = Field(default="5y", description="比較所使用的市場資料期間。")
    frequency: str = Field(default="1d", description="比較所使用的市場資料頻率。")
    benchmark: str | None = Field(default=None, description="比較使用的 benchmark。")
    companies: list[ComparisonCompany] = Field(description="統一格式的公司比較資料。")
