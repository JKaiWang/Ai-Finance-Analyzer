from datetime import date as date_type

from pydantic import BaseModel, Field

from app.schemas.metrics import DataStatus


class IncomeStatementRecord(BaseModel):
    period: date_type = Field(description="財務期間。")
    revenue: float | None = Field(default=None, description="營收。")
    gross_profit: float | None = Field(default=None, description="毛利。")
    operating_income: float | None = Field(default=None, description="營業利益。")
    ebitda: float | None = Field(default=None, description="EBITDA。")
    pretax_income: float | None = Field(default=None, description="稅前利益。")
    tax_provision: float | None = Field(default=None, description="所得稅費用。")
    interest_expense: float | None = Field(default=None, description="利息費用。")
    net_income: float | None = Field(default=None, description="淨利。")
    eps: float | None = Field(default=None, description="每股盈餘。")


class BalanceSheetRecord(BaseModel):
    period: date_type = Field(description="財務期間。")
    total_assets: float | None = Field(default=None, description="總資產。")
    total_liabilities: float | None = Field(default=None, description="總負債。")
    cash: float | None = Field(default=None, description="現金與約當現金。")
    debt: float | None = Field(default=None, description="總負債性借款。")
    equity: float | None = Field(default=None, description="股東權益。")
    current_assets: float | None = Field(default=None, description="流動資產。")
    current_liabilities: float | None = Field(default=None, description="流動負債。")
    receivables: float | None = Field(default=None, description="應收帳款。")


class CashFlowRecord(BaseModel):
    period: date_type = Field(description="財務期間。")
    operating_cash_flow: float | None = Field(
        default=None, description="營業活動現金流。"
    )
    capital_expenditure: float | None = Field(default=None, description="資本支出。")
    free_cash_flow: float | None = Field(default=None, description="自由現金流。")


class GrowthMetrics(BaseModel):
    revenue_growth: float | None = Field(default=None, description="營收成長率。")
    eps_growth: float | None = Field(default=None, description="EPS 成長率。")
    net_income_growth: float | None = Field(default=None, description="淨利成長率。")
    free_cash_flow_growth: float | None = Field(
        default=None, description="自由現金流成長率。"
    )
    book_value_growth: float | None = Field(
        default=None, description="帳面價值成長率。"
    )


class ProfitabilityMetrics(BaseModel):
    gross_margin: float | None = Field(default=None, description="毛利率。")
    operating_margin: float | None = Field(default=None, description="營業利益率。")
    net_margin: float | None = Field(default=None, description="淨利率。")
    roe: float | None = Field(default=None, description="股東權益報酬率。")
    ebitda_margin: float | None = Field(default=None, description="EBITDA 利潤率。")
    roa: float | None = Field(default=None, description="資產報酬率。")
    roic: float | None = Field(default=None, description="投入資本報酬率。")


class FinancialHealthMetrics(BaseModel):
    debt_to_equity: float | None = Field(default=None, description="負債權益比。")
    current_ratio: float | None = Field(default=None, description="流動比率。")
    free_cash_flow_margin: float | None = Field(
        default=None, description="自由現金流利潤率。"
    )
    quick_ratio: float | None = Field(default=None, description="速動比率。")
    cash_ratio: float | None = Field(default=None, description="現金比率。")
    interest_coverage: float | None = Field(default=None, description="利息保障倍數。")


class ValuationMetrics(BaseModel):
    trailing_pe: float | None = Field(default=None, description="本益比。")
    forward_pe: float | None = Field(default=None, description="預估本益比。")
    peg_ratio: float | None = Field(default=None, description="PEG。")
    price_to_book: float | None = Field(default=None, description="股價淨值比。")
    price_to_sales: float | None = Field(default=None, description="股價營收比。")
    enterprise_to_ebitda: float | None = Field(default=None, description="EV/EBITDA。")
    enterprise_to_revenue: float | None = Field(default=None, description="EV/Sales。")


class DividendMetrics(BaseModel):
    dividend_yield: float | None = Field(default=None, description="股利殖利率。")
    dividend_rate: float | None = Field(default=None, description="每股股利。")
    payout_ratio: float | None = Field(default=None, description="配息率。")


class OwnershipMetrics(BaseModel):
    insider_ownership: float | None = Field(
        default=None, description="內部人持股比例。"
    )
    institutional_ownership: float | None = Field(
        default=None, description="機構持股比例。"
    )
    float_shares: int | None = Field(default=None, description="可流通股數。")
    shares_outstanding: int | None = Field(default=None, description="流通在外股數。")


class FundamentalsResponse(BaseModel):
    symbol: str = Field(description="股票代號。")
    data_status: DataStatus = Field(description="財務資料來源與可用狀態。")
    income_statement: list[IncomeStatementRecord] = Field(
        description="年度損益表資料。"
    )
    balance_sheet: list[BalanceSheetRecord] = Field(description="年度資產負債表資料。")
    cash_flow: list[CashFlowRecord] = Field(description="年度現金流量表資料。")
    growth: GrowthMetrics = Field(description="成長指標。")
    profitability: ProfitabilityMetrics = Field(description="獲利能力指標。")
    financial_health: FinancialHealthMetrics = Field(description="財務健康指標。")
    valuation: ValuationMetrics = Field(description="估值指標。")
    dividend: DividendMetrics = Field(description="股利指標。")
    ownership: OwnershipMetrics = Field(description="股權結構指標。")
