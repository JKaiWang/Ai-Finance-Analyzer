export type PriceRecord = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type DataStatus = {
  status: "available" | "partial" | "unavailable";
  source: string;
  as_of: string | null;
  message: string | null;
  missing_fields: string[];
};

export type StockResponse = {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  country: string | null;
  exchange: string | null;
  currency: string | null;
  current_price: number | null;
  market_cap: number | null;
  enterprise_value: number | null;
  history: PriceRecord[];
};

export type MovingAverageRecord = {
  date: string;
  ma20: number | null;
  ma50: number | null;
  ma200: number | null;
};

export type AnalyticsResponse = {
  symbol: string;
  data_status: DataStatus;
  daily_returns: Array<{ date: string; daily_return: number | null }>;
  period_returns: {
    one_month: number | null;
    three_months: number | null;
    six_months: number | null;
    one_year: number | null;
  };
  annualized_volatility: number | null;
  maximum_drawdown: number | null;
  moving_averages: MovingAverageRecord[];
  risk_free_rate: number;
  sharpe_ratio: number | null;
  benchmark: {
    symbol: string;
    one_year_return: number | null;
    relative_performance: number | null;
  } | null;
};

export type FundamentalsResponse = {
  symbol: string;
  data_status: DataStatus;
  income_statement: Array<{
    period: string;
    revenue: number | null;
    gross_profit: number | null;
    operating_income: number | null;
    net_income: number | null;
    eps: number | null;
  }>;
  balance_sheet: Array<{
    period: string;
    total_assets: number | null;
    total_liabilities: number | null;
    cash: number | null;
    debt: number | null;
    equity: number | null;
    current_assets: number | null;
    current_liabilities: number | null;
  }>;
  cash_flow: Array<{
    period: string;
    operating_cash_flow: number | null;
    capital_expenditure: number | null;
    free_cash_flow: number | null;
  }>;
  growth: {
    revenue_growth: number | null;
    eps_growth: number | null;
    net_income_growth: number | null;
    free_cash_flow_growth: number | null;
  };
  profitability: {
    gross_margin: number | null;
    operating_margin: number | null;
    net_margin: number | null;
    roe: number | null;
  };
  financial_health: {
    debt_to_equity: number | null;
    current_ratio: number | null;
    free_cash_flow_margin: number | null;
  };
};

export type NewsArticle = {
  headline: string;
  source: string;
  published_at: string;
  url: string;
  summary: string | null;
  category: string;
  sentiment: "Positive" | "Neutral" | "Negative";
  sentiment_confidence: number;
  importance: number;
};

export type NewsResponse = {
  symbol: string;
  data_status: DataStatus;
  provider: string;
  available: boolean;
  message: string | null;
  articles: NewsArticle[];
};

export type ComparisonCompany = {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  country: string | null;
  exchange: string | null;
  currency: string | null;
  current_price: number | null;
  market_cap: number | null;
  enterprise_value: number | null;
  one_week_return: number | null;
  one_month_return: number | null;
  three_month_return: number | null;
  six_month_return: number | null;
  ytd_return: number | null;
  one_year_return: number | null;
  three_year_return: number | null;
  five_year_return: number | null;
  annualized_volatility: number | null;
  maximum_drawdown: number | null;
  sharpe_ratio: number | null;
  downside_volatility: number | null;
  sortino_ratio: number | null;
  calmar_ratio: number | null;
  cagr: number | null;
  alpha: number | null;
  beta: number | null;
  revenue_growth: number | null;
  eps_growth: number | null;
  net_income_growth: number | null;
  free_cash_flow_growth: number | null;
  book_value_growth: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  ebitda_margin: number | null;
  net_margin: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  cash_ratio: number | null;
  debt_to_equity: number | null;
  interest_coverage: number | null;
  free_cash_flow: number | null;
  eps: number | null;
  free_cash_flow_margin: number | null;
  price_to_earnings: number | null;
  forward_pe: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;
  price_to_sales: number | null;
  enterprise_to_ebitda: number | null;
  enterprise_to_revenue: number | null;
  dividend_yield: number | null;
  dividend_growth: number | null;
  payout_ratio: number | null;
  insider_ownership: number | null;
  institutional_ownership: number | null;
  float_shares: number | null;
  shares_outstanding: number | null;
  normalized_history: Array<{ date: string; value: number }>;
  available: boolean;
  errors: string[];
  factor_scores: Record<string, number | null>;
  peer_scores: Record<string, {
    value: number | null;
    score: number | null;
    percentile: number | null;
    sample_size: number;
    confidence: string;
    reason: string | null;
  }>;
  heatmap: Record<string, {
    value: number | null;
    score: number | null;
    direction: string;
    state: string;
  }>;
  research_summary: {
    strengths: Array<{ factor: string; reason: string; score: number | null }>;
    weaknesses: Array<{ factor: string; reason: string; score: number | null }>;
    disclaimer: string;
  } | null;
  financial_trends: Record<string, Array<{ period: string; value: number | null }>>;
};

export type ComparisonResponse = {
  symbols: string[];
  period: string;
  frequency: string;
  benchmark: string | null;
  companies: ComparisonCompany[];
};

export type BacktestResponse = {
  symbols: string[];
  benchmark: string | null;
  period: string;
  horizon_months: number;
  rebalance: string;
  trained_from: string | null;
  tested_from: string | null;
  tested_to: string | null;
  weights: Record<string, number>;
  train: { cagr: number | null; volatility: number | null; sharpe: number | null; maximum_drawdown: number | null; hit_rate: number | null; observations: number };
  test: { cagr: number | null; volatility: number | null; sharpe: number | null; maximum_drawdown: number | null; hit_rate: number | null; observations: number };
  recommendations: Array<{ symbol: string; score: number; rank: number; latest_as_of: string; features: Record<string, number | null>; label: string }>;
  data_quality: Record<string, string | number | string[] | null>;
};

export class StockApiError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "StockApiError";
    this.status = status;
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function fetchStock(symbol: string): Promise<StockResponse> {
  const normalizedSymbol = symbol.trim().toUpperCase();

  try {
    const response = await fetch(
      `${API_URL}/stocks/${encodeURIComponent(normalizedSymbol)}`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      let detail = "無法取得股票資料。";

      try {
        const body: unknown = await response.json();
        if (
          typeof body === "object" &&
          body !== null &&
          "detail" in body &&
          typeof body.detail === "string"
        ) {
          detail = body.detail;
        }
      } catch {
        // Keep the generic message when the server does not return JSON.
      }

      if (response.status === 404) {
        throw new StockApiError(`找不到股票代號 ${normalizedSymbol}。`, 404);
      }

      if (response.status === 502) {
        throw new StockApiError("市場資料服務暫時無法使用，請稍後再試。", 502);
      }

      throw new StockApiError(detail, response.status);
    }

    return (await response.json()) as StockResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) {
      throw error;
    }

    throw new StockApiError("無法連線到 FinSight API，請確認後端服務已啟動。");
  }
}

export async function fetchStockAnalytics(
  symbol: string,
): Promise<AnalyticsResponse> {
  const normalizedSymbol = symbol.trim().toUpperCase();

  try {
    const response = await fetch(
      `${API_URL}/stocks/${encodeURIComponent(normalizedSymbol)}/analytics`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new StockApiError(`找不到股票代號 ${normalizedSymbol}。`, 404);
      }
      if (response.status === 502) {
        throw new StockApiError("市場資料服務暫時無法使用，請稍後再試。", 502);
      }
      throw new StockApiError("無法取得量化分析資料。", response.status);
    }

    return (await response.json()) as AnalyticsResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) {
      throw error;
    }

    throw new StockApiError("無法連線到 FinSight API，請確認後端服務已啟動。");
  }
}

export async function fetchFundamentals(
  symbol: string,
): Promise<FundamentalsResponse> {
  const normalizedSymbol = symbol.trim().toUpperCase();

  try {
    const response = await fetch(
      `${API_URL}/stocks/${encodeURIComponent(normalizedSymbol)}/fundamentals`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new StockApiError(`找不到股票代號 ${normalizedSymbol} 的財務資料。`, 404);
      }
      if (response.status === 502) {
        throw new StockApiError("財務資料服務暫時無法使用，請稍後再試。", 502);
      }
      throw new StockApiError("無法取得基本面資料。", response.status);
    }

    return (await response.json()) as FundamentalsResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) {
      throw error;
    }
    throw new StockApiError("無法連線到 FinSight API，請確認後端服務已啟動。");
  }
}

export async function fetchNews(symbol: string): Promise<NewsResponse> {
  const normalizedSymbol = symbol.trim().toUpperCase();

  try {
    const response = await fetch(
      `${API_URL}/stocks/${encodeURIComponent(normalizedSymbol)}/news`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      if (response.status === 502) {
        throw new StockApiError("新聞資料服務暫時無法使用，請稍後再試。", 502);
      }
      throw new StockApiError("無法取得公司新聞。", response.status);
    }

    return (await response.json()) as NewsResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) {
      throw error;
    }
    throw new StockApiError("無法連線到 FinSight API，請確認後端服務已啟動。");
  }
}

export async function fetchComparison(
  symbols: string[],
  options: { period?: string; benchmark?: string; frequency?: string } = {},
): Promise<ComparisonResponse> {
  const normalizedSymbols = [...new Set(symbols.map((symbol) => symbol.trim().toUpperCase()))].filter(Boolean);

  try {
    const params = new URLSearchParams({
      symbols: normalizedSymbols.join(","),
      ...(options.period ? { period: options.period } : {}),
      ...(options.benchmark ? { benchmark: options.benchmark } : {}),
      ...(options.frequency ? { frequency: options.frequency } : {}),
    });
    const response = await fetch(
      `${API_URL}/compare?${params.toString()}`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      let detail = "無法取得公司比較資料。";
      try {
        const body: unknown = await response.json();
        if (typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string") {
          detail = body.detail;
        }
      } catch {
        // Keep the generic message when the server does not return JSON.
      }
      throw new StockApiError(detail, response.status);
    }
    return (await response.json()) as ComparisonResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) {
      throw error;
    }
    throw new StockApiError("無法連線到 FinSight API，請確認後端服務已啟動。");
  }
}

export async function fetchBacktest(
  symbols: string[],
  options: { period?: string; horizon?: string; benchmark?: string } = {},
): Promise<BacktestResponse> {
  const params = new URLSearchParams({
    symbols: [...new Set(symbols.map((symbol) => symbol.trim().toUpperCase()))].filter(Boolean).join(","),
    period: options.period ?? "10y",
    horizon: options.horizon ?? "3m",
    ...(options.benchmark ? { benchmark: options.benchmark } : {}),
  });
  try {
    const response = await fetch(`${API_URL}/backtest?${params.toString()}`, { cache: "no-store" });
    if (!response.ok) {
      const body = await response.json().catch(() => ({})) as { detail?: string };
      throw new StockApiError(body.detail ?? "無法取得回測資料。", response.status);
    }
    return (await response.json()) as BacktestResponse;
  } catch (error: unknown) {
    if (error instanceof StockApiError) throw error;
    throw new StockApiError("無法連線到 FinSight 回測 API，請確認後端服務已啟動。");
  }
}
