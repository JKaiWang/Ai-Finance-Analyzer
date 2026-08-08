import logging
import math
from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf

from app.services.stock_service import StockDataUnavailable, StockNotFound

logger = logging.getLogger("finsight.fundamentals_service")


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _period(value: Any) -> date | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.date()


def _table_value(
    table: pd.DataFrame, labels: tuple[str, ...], column: Any
) -> float | None:
    for label in labels:
        if label in table.index:
            return _safe_float(table.loc[label, column])
    return None


def _load_table(ticker: yf.Ticker, attribute: str) -> pd.DataFrame:
    try:
        table = getattr(ticker, attribute)
    except Exception as exc:  # noqa: BLE001 - yfinance has varied provider errors.
        logger.warning("Fundamental table %s unavailable: %s", attribute, exc)
        return pd.DataFrame()
    if not isinstance(table, pd.DataFrame):
        return pd.DataFrame()
    return table


def _income_statement(table: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for column in table.columns:
        period = _period(column)
        if period is None:
            continue
        records.append(
            {
                "period": period,
                "revenue": _table_value(table, ("Total Revenue",), column),
                "gross_profit": _table_value(table, ("Gross Profit",), column),
                "operating_income": _table_value(table, ("Operating Income",), column),
                "ebitda": _table_value(table, ("EBITDA", "Normalized EBITDA"), column),
                "pretax_income": _table_value(table, ("Pretax Income",), column),
                "tax_provision": _table_value(table, ("Tax Provision",), column),
                "interest_expense": _table_value(
                    table,
                    ("Interest Expense", "Interest Expense Non Operating"),
                    column,
                ),
                "net_income": _table_value(
                    table, ("Net Income", "Net Income Common Stockholders"), column
                ),
                "eps": _table_value(
                    table,
                    ("Diluted EPS", "Basic EPS", "Diluted EPS Other GAAP"),
                    column,
                ),
            }
        )
    return sorted(records, key=lambda record: record["period"], reverse=True)


def _balance_sheet(table: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for column in table.columns:
        period = _period(column)
        if period is None:
            continue
        records.append(
            {
                "period": period,
                "total_assets": _table_value(table, ("Total Assets",), column),
                "total_liabilities": _table_value(
                    table,
                    ("Total Liabilities Net Minority Interest", "Total Liabilities"),
                    column,
                ),
                "cash": _table_value(
                    table,
                    (
                        "Cash Cash Equivalents And Short Term Investments",
                        "Cash And Cash Equivalents",
                        "Cash Financial",
                    ),
                    column,
                ),
                "debt": _table_value(
                    table,
                    ("Total Debt", "Long Term Debt And Capital Lease Obligation"),
                    column,
                ),
                "equity": _table_value(
                    table,
                    ("Stockholders Equity", "Common Stock Equity"),
                    column,
                ),
                "current_assets": _table_value(table, ("Current Assets",), column),
                "current_liabilities": _table_value(
                    table, ("Current Liabilities",), column
                ),
                "receivables": _table_value(
                    table,
                    ("Accounts Receivable", "Receivables", "Net Receivables"),
                    column,
                ),
            }
        )
    return sorted(records, key=lambda record: record["period"], reverse=True)


def _cash_flow(table: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for column in table.columns:
        period = _period(column)
        if period is None:
            continue
        operating_cash_flow = _table_value(table, ("Operating Cash Flow",), column)
        capital_expenditure = _table_value(
            table, ("Capital Expenditure", "Capital Expenditure Reported"), column
        )
        free_cash_flow = _table_value(table, ("Free Cash Flow",), column)
        if (
            free_cash_flow is None
            and operating_cash_flow is not None
            and capital_expenditure is not None
        ):
            free_cash_flow = operating_cash_flow + capital_expenditure
        records.append(
            {
                "period": period,
                "operating_cash_flow": operating_cash_flow,
                "capital_expenditure": capital_expenditure,
                "free_cash_flow": free_cash_flow,
            }
        )
    return sorted(records, key=lambda record: record["period"], reverse=True)


def _growth(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return current / previous - 1


def _latest(records: list[dict[str, Any]]) -> dict[str, Any]:
    return records[0] if records else {}


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _info_value(info: dict[str, Any], key: str) -> float | int | None:
    return _safe_float(info.get(key))


def _average(current: float | None, previous: float | None) -> float | None:
    if current is None:
        return None
    if previous is None:
        return current
    return (current + previous) / 2


def get_fundamentals(symbol: str) -> dict[str, Any]:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise StockNotFound("Stock symbol cannot be empty")

    try:
        ticker = yf.Ticker(normalized_symbol)
    except Exception as exc:
        logger.exception(
            "Failed to initialize fundamentals ticker for %s", normalized_symbol
        )
        raise StockDataUnavailable(
            f"Failed to initialize fundamentals for {normalized_symbol}"
        ) from exc

    income = _income_statement(_load_table(ticker, "income_stmt"))
    balance = _balance_sheet(_load_table(ticker, "balance_sheet"))
    cash_flow = _cash_flow(_load_table(ticker, "cashflow"))
    if not income and not balance and not cash_flow:
        raise StockNotFound(f"No fundamental data found for {normalized_symbol}")

    current_income = _latest(income)
    previous_income = income[1] if len(income) > 1 else {}
    current_cash_flow = _latest(cash_flow)
    previous_cash_flow = cash_flow[1] if len(cash_flow) > 1 else {}
    current_balance = _latest(balance)
    previous_balance = balance[1] if len(balance) > 1 else {}

    try:
        info = ticker.info
    except Exception as exc:  # noqa: BLE001 - provider fields are optional.
        logger.warning(
            "Optional valuation data unavailable for %s: %s", normalized_symbol, exc
        )
        info = {}
    if not isinstance(info, dict):
        info = {}

    revenue = current_income.get("revenue")
    gross_profit = current_income.get("gross_profit")
    operating_income = current_income.get("operating_income")
    net_income = current_income.get("net_income")
    equity = current_balance.get("equity")
    free_cash_flow = current_cash_flow.get("free_cash_flow")
    ebitda = current_income.get("ebitda")
    average_assets = _average(
        current_balance.get("total_assets"), previous_balance.get("total_assets")
    )
    average_equity = _average(equity, previous_balance.get("equity"))
    average_debt = _average(current_balance.get("debt"), previous_balance.get("debt"))
    average_cash = _average(current_balance.get("cash"), previous_balance.get("cash"))
    invested_capital = (
        average_debt + average_equity - average_cash
        if average_debt is not None
        and average_equity is not None
        and average_cash is not None
        else None
    )
    tax_rate = _ratio(
        current_income.get("tax_provision"), current_income.get("pretax_income")
    )
    nopat = (
        operating_income * (1 - tax_rate)
        if operating_income is not None and tax_rate is not None
        else None
    )
    interest_expense = current_income.get("interest_expense")
    cash = current_balance.get("cash")
    receivables = current_balance.get("receivables")
    quick_assets = (
        cash + receivables if cash is not None and receivables is not None else None
    )

    return {
        "symbol": normalized_symbol,
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cash_flow,
        "growth": {
            "revenue_growth": _growth(revenue, previous_income.get("revenue")),
            "eps_growth": _growth(
                current_income.get("eps"), previous_income.get("eps")
            ),
            "net_income_growth": _growth(net_income, previous_income.get("net_income")),
            "free_cash_flow_growth": _growth(
                free_cash_flow, previous_cash_flow.get("free_cash_flow")
            ),
            "book_value_growth": _growth(equity, previous_balance.get("equity")),
        },
        "profitability": {
            "gross_margin": _ratio(gross_profit, revenue),
            "operating_margin": _ratio(operating_income, revenue),
            "net_margin": _ratio(net_income, revenue),
            "roe": _ratio(net_income, average_equity),
            "ebitda_margin": _ratio(ebitda, revenue),
            "roa": _ratio(net_income, average_assets),
            "roic": _ratio(nopat, invested_capital),
        },
        "financial_health": {
            "debt_to_equity": _ratio(current_balance.get("debt"), equity),
            "current_ratio": _ratio(
                current_balance.get("current_assets"),
                current_balance.get("current_liabilities"),
            ),
            "free_cash_flow_margin": _ratio(free_cash_flow, revenue),
            "quick_ratio": _ratio(
                quick_assets,
                current_balance.get("current_liabilities"),
            ),
            "cash_ratio": _ratio(
                current_balance.get("cash"), current_balance.get("current_liabilities")
            ),
            "interest_coverage": _ratio(
                operating_income,
                abs(interest_expense) if interest_expense is not None else None,
            ),
        },
        "valuation": {
            "trailing_pe": _info_value(info, "trailingPE"),
            "forward_pe": _info_value(info, "forwardPE"),
            "peg_ratio": _info_value(info, "pegRatio"),
            "price_to_book": _info_value(info, "priceToBook"),
            "price_to_sales": _info_value(info, "priceToSalesTrailing12Months"),
            "enterprise_to_ebitda": _info_value(info, "enterpriseToEbitda"),
            "enterprise_to_revenue": _info_value(info, "enterpriseToRevenue"),
        },
        "dividend": {
            "dividend_yield": _info_value(info, "dividendYield"),
            "dividend_rate": _info_value(info, "dividendRate"),
            "payout_ratio": _info_value(info, "payoutRatio"),
        },
        "ownership": {
            "insider_ownership": _info_value(info, "heldPercentInsiders"),
            "institutional_ownership": _info_value(info, "heldPercentInstitutions"),
            "float_shares": int(info["floatShares"])
            if _safe_float(info.get("floatShares")) is not None
            else None,
            "shares_outstanding": int(info["sharesOutstanding"])
            if _safe_float(info.get("sharesOutstanding")) is not None
            else None,
        },
    }
