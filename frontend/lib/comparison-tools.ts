import type { ComparisonResponse } from "./api";

export type SavedComparison = {
  id: string;
  name: string;
  symbols: string[];
  period: string;
  frequency: string;
  benchmark: string;
  createdAt: string;
};

export type ComparisonAlert = {
  id: string;
  symbol: string;
  metric: "price_to_earnings" | "net_margin" | "current_price" | "one_year_return";
  operator: "above" | "below";
  threshold: number;
};

export const SAVED_COMPARISONS_KEY = "finsight.saved-comparisons";
export const COMPARISON_ALERTS_KEY = "finsight.comparison-alerts";

export function csvForComparison(result: ComparisonResponse): string {
  const columns = [
    "symbol", "company_name", "current_price", "market_cap", "one_year_return",
    "annualized_volatility", "maximum_drawdown", "revenue_growth", "net_margin",
    "roic", "current_ratio", "debt_to_equity", "price_to_earnings", "free_cash_flow",
  ] as const;
  const escape = (value: unknown) => {
    const text = value === null || value === undefined ? "" : String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  const rows = result.companies.map((company) => columns.map((column) => escape(company[column])).join(","));
  return [columns.join(","), ...rows].join("\n");
}

export function matchingAlerts(result: ComparisonResponse, alerts: ComparisonAlert[]): ComparisonAlert[] {
  return alerts.filter((alert) => {
    const company = result.companies.find((item) => item.symbol === alert.symbol);
    const value = company?.[alert.metric];
    if (typeof value !== "number" || !Number.isFinite(value)) return false;
    return alert.operator === "above" ? value >= alert.threshold : value <= alert.threshold;
  });
}

export function shareUrl(state: { symbols: string[]; period: string; frequency: string; benchmark: string }): string {
  const params = new URLSearchParams({
    symbols: state.symbols.join(","),
    period: state.period,
    frequency: state.frequency,
    ...(state.benchmark ? { benchmark: state.benchmark } : {}),
  });
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}
