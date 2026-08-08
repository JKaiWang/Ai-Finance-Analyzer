import type { ComparisonCompany } from "@/lib/api";

export const suggestions = ["NVDA", "AMD", "INTC", "AAPL", "MSFT"];
export const colors = ["#38bdf8", "#fb7185", "#facc15", "#34d399", "#c084fc"];

export const factorLabels: Record<string, string> = {
  growth: "Growth",
  profitability: "Profitability",
  valuation: "Valuation",
  risk: "Risk",
  financial_health: "Financial Health",
  momentum: "Momentum",
};

export type RevenueMode = "absolute" | "yoy" | "indexed";

export type MetricDefinition = {
  label: string;
  key: keyof ComparisonCompany;
  format: "percent" | "number" | "compact";
};

export type HeatmapMetric = MetricDefinition & { key: string };

export const performanceMetrics: MetricDefinition[] = [
  { label: "1W Return", key: "one_week_return", format: "percent" },
  { label: "1M Return", key: "one_month_return", format: "percent" },
  { label: "3M Return", key: "three_month_return", format: "percent" },
  { label: "6M Return", key: "six_month_return", format: "percent" },
  { label: "YTD Return", key: "ytd_return", format: "percent" },
  { label: "1Y Return", key: "one_year_return", format: "percent" },
  { label: "3Y Return", key: "three_year_return", format: "percent" },
  { label: "5Y Return", key: "five_year_return", format: "percent" },
  { label: "CAGR", key: "cagr", format: "percent" },
  { label: "Alpha", key: "alpha", format: "percent" },
  { label: "Beta", key: "beta", format: "number" },
];

export const riskMetrics: MetricDefinition[] = [
  { label: "Annualized Volatility", key: "annualized_volatility", format: "percent" },
  { label: "Maximum Drawdown", key: "maximum_drawdown", format: "percent" },
  { label: "Sharpe Ratio", key: "sharpe_ratio", format: "number" },
  { label: "Downside Volatility", key: "downside_volatility", format: "percent" },
  { label: "Sortino Ratio", key: "sortino_ratio", format: "number" },
  { label: "Calmar Ratio", key: "calmar_ratio", format: "number" },
];

export const valuationMetrics: MetricDefinition[] = [
  { label: "Trailing PE", key: "price_to_earnings", format: "number" },
  { label: "Forward PE", key: "forward_pe", format: "number" },
  { label: "PEG", key: "peg_ratio", format: "number" },
  { label: "PB", key: "price_to_book", format: "number" },
  { label: "PS", key: "price_to_sales", format: "number" },
  { label: "EV / EBITDA", key: "enterprise_to_ebitda", format: "number" },
  { label: "EV / Sales", key: "enterprise_to_revenue", format: "number" },
];

export const fundamentalMetrics: MetricDefinition[] = [
  { label: "Revenue Growth", key: "revenue_growth", format: "percent" },
  { label: "EPS Growth", key: "eps_growth", format: "percent" },
  { label: "Net Income Growth", key: "net_income_growth", format: "percent" },
  { label: "FCF Growth", key: "free_cash_flow_growth", format: "percent" },
  { label: "Gross Margin", key: "gross_margin", format: "percent" },
  { label: "Operating Margin", key: "operating_margin", format: "percent" },
  { label: "EBITDA Margin", key: "ebitda_margin", format: "percent" },
  { label: "Net Margin", key: "net_margin", format: "percent" },
  { label: "ROE", key: "roe", format: "percent" },
  { label: "ROA", key: "roa", format: "percent" },
  { label: "ROIC", key: "roic", format: "percent" },
  { label: "Current Ratio", key: "current_ratio", format: "number" },
  { label: "Quick Ratio", key: "quick_ratio", format: "number" },
  { label: "Cash Ratio", key: "cash_ratio", format: "number" },
  { label: "Debt / Equity", key: "debt_to_equity", format: "number" },
  { label: "Interest Coverage", key: "interest_coverage", format: "number" },
  { label: "Free Cash Flow", key: "free_cash_flow", format: "compact" },
  { label: "FCF Margin", key: "free_cash_flow_margin", format: "percent" },
  { label: "Dividend Yield", key: "dividend_yield", format: "percent" },
  { label: "Payout Ratio", key: "payout_ratio", format: "percent" },
  { label: "Insider Ownership", key: "insider_ownership", format: "percent" },
  { label: "Institutional Ownership", key: "institutional_ownership", format: "percent" },
];

export const heatmapMetrics: HeatmapMetric[] = [
  { label: "Revenue Growth", key: "revenue_growth", format: "percent" },
  { label: "ROIC", key: "roic", format: "percent" },
  { label: "Annualized Volatility", key: "annualized_volatility", format: "percent" },
  { label: "Price-to-Earnings", key: "price_to_earnings", format: "number" },
  { label: "Current Ratio", key: "current_ratio", format: "number" },
  { label: "One Year Return", key: "one_year_return", format: "percent" },
  { label: "Free Cash Flow", key: "free_cash_flow", format: "compact" },
  { label: "EPS", key: "eps", format: "number" },
  { label: "Net Margin", key: "net_margin", format: "percent" },
];
