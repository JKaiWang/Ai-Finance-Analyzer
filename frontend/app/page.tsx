"use client";

import { FormEvent, useState } from "react";
import { ArrowUpRight, BarChart3, LoaderCircle, Search } from "lucide-react";

import FundamentalCharts from "@/components/FundamentalCharts";
import ComparisonDashboard from "@/components/ComparisonDashboard";
import NewsTimeline from "@/components/NewsTimeline";
import PriceChart from "@/components/PriceChart";
import {
  fetchFundamentals,
  fetchNews,
  fetchStock,
  fetchStockAnalytics,
  type AnalyticsResponse,
  type FundamentalsResponse,
  type NewsResponse,
  type PriceRecord,
  type StockResponse,
  StockApiError,
} from "@/lib/api";

const suggestions = ["NVDA", "AAPL", "2330.TW"];

function formatNumber(value: number | null): string {
  if (value === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null) {
    return "-";
  }

  return `${(value * 100).toFixed(2)}%`;
}

function formatRatio(value: number | null): string {
  return value === null ? "-" : value.toFixed(2);
}

function formatCurrency(value: number | null, currency: string | null): string {
  if (value === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency ?? "USD",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatMarketCap(value: number | null, currency: string | null): string {
  if (value === null) {
    return "-";
  }

  const units = [
    { threshold: 1_000_000_000_000, suffix: "T" },
    { threshold: 1_000_000_000, suffix: "B" },
    { threshold: 1_000_000, suffix: "M" },
  ];
  const unit = units.find((item) => value >= item.threshold);

  if (!unit) {
    return `${currency ?? ""} ${formatNumber(value)}`.trim();
  }

  return `${currency ?? ""} ${(value / unit.threshold).toFixed(2)}${unit.suffix}`.trim();
}

function formatVolume(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function latestRecords(history: PriceRecord[]): PriceRecord[] {
  return [...history].slice(-5).reverse();
}

function exchangeFor(symbol: string): string {
  if (symbol.endsWith(".TW")) {
    return "台股市場";
  }

  return "美股市場";
}

function EmptyState() {
  return (
    <section className="panel empty-state" aria-live="polite">
      <div className="empty-inner">
        <BarChart3 className="empty-icon" strokeWidth={1} aria-hidden="true" />
        <h2>開始一項研究</h2>
        <p>輸入股票代號，查看價格、交易統計與一年收盤走勢。</p>
      </div>
    </section>
  );
}

type ErrorStateProps = {
  message: string;
  onRetry: () => void;
};

function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <section className="panel error-state" role="alert">
      <div>
        <h2>查詢未完成</h2>
        <p>{message}</p>
        <button className="retry-button" type="button" onClick={onRetry}>
          再試一次
        </button>
      </div>
    </section>
  );
}

function AnalyticsPanel({ analytics }: { analytics: AnalyticsResponse }) {
  const benchmark = analytics.benchmark;
  const periodCards = [
    ["1 個月報酬", analytics.period_returns.one_month],
    ["3 個月報酬", analytics.period_returns.three_months],
    ["6 個月報酬", analytics.period_returns.six_months],
    ["1 年報酬", analytics.period_returns.one_year],
  ] as const;

  return (
    <section className="panel analytics-panel" aria-labelledby="analytics-heading">
      <div className="section-heading">
        <h2 id="analytics-heading">量化分析</h2>
        <span>根據每日收盤價計算</span>
      </div>
      <div className="analytics-grid">
        {periodCards.map(([label, value]) => (
          <div className="analytics-metric" key={label}>
            <div className="metric-label">{label}</div>
            <p className={`analytics-value ${value !== null && value >= 0 ? "positive" : "negative"}`}>
              {formatPercent(value)}
            </p>
          </div>
        ))}
        <div className="analytics-metric">
          <div className="metric-label">年化波動率</div>
          <p className="analytics-value">{formatPercent(analytics.annualized_volatility)}</p>
        </div>
        <div className="analytics-metric">
          <div className="metric-label">最大回撤</div>
          <p className="analytics-value negative">{formatPercent(analytics.maximum_drawdown)}</p>
        </div>
        <div className="analytics-metric">
          <div className="metric-label">Sharpe Ratio</div>
          <p className="analytics-value">{analytics.sharpe_ratio?.toFixed(2) ?? "-"}</p>
        </div>
        <div className="analytics-metric">
          <div className="metric-label">相對 {benchmark?.symbol ?? "基準指數"}</div>
          <p className={`analytics-value ${benchmark?.relative_performance !== null && benchmark?.relative_performance !== undefined && benchmark.relative_performance >= 0 ? "positive" : "negative"}`}>
            {formatPercent(benchmark?.relative_performance ?? null)}
          </p>
        </div>
      </div>
    </section>
  );
}

function FundamentalsPanel({ fundamentals }: { fundamentals: FundamentalsResponse }) {
  const profitability = fundamentals.profitability;
  const health = fundamentals.financial_health;
  const growth = fundamentals.growth;
  const metrics = [
    ["營收成長", formatPercent(growth.revenue_growth), growth.revenue_growth],
    ["EPS 成長", formatPercent(growth.eps_growth), growth.eps_growth],
    ["淨利率", formatPercent(profitability.net_margin), profitability.net_margin],
    ["ROE", formatPercent(profitability.roe), profitability.roe],
    ["負債 / 權益", formatRatio(health.debt_to_equity), null],
    ["流動比率", formatRatio(health.current_ratio), null],
    ["自由現金流率", formatPercent(health.free_cash_flow_margin), health.free_cash_flow_margin],
  ] as const;

  return (
    <>
      <FundamentalCharts fundamentals={fundamentals} />
      <section className="panel fundamentals-metrics" aria-labelledby="fundamental-metrics-heading">
        <div className="section-heading">
          <h2 id="fundamental-metrics-heading">基本面指標</h2>
          <span>最新可用期間</span>
        </div>
        <div className="fundamental-metric-grid">
          {metrics.map(([label, value, signedValue]) => (
            <div className="fundamental-metric" key={label}>
              <div className="metric-label">{label}</div>
              <p className={`analytics-value ${signedValue !== null && signedValue !== undefined ? signedValue >= 0 ? "positive" : "negative" : ""}`}>
                {value}
              </p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function NewsPanel({ news }: { news: NewsResponse }) {
  return (
    <section className="panel news-panel" aria-labelledby="news-heading">
      <div className="section-heading">
        <h2 id="news-heading">公司新聞</h2>
        <span>{news.provider} · 近 30 天</span>
      </div>
      {!news.available || news.articles.length === 0 ? (
        <div className="news-empty">
          <p>{news.message ?? "目前沒有可用的公司新聞。"}</p>
          <span>新聞情緒僅供整理參考，不代表買賣建議。</span>
        </div>
      ) : (
        <>
          <NewsTimeline articles={news.articles} />
          <p className="news-disclaimer">情緒與重要度為規則式整理結果，不代表買賣建議。</p>
        </>
      )}
    </section>
  );
}

function StockWorkspace({
  stock,
  analytics,
  fundamentals,
  news,
}: {
  stock: StockResponse;
  analytics: AnalyticsResponse;
  fundamentals: FundamentalsResponse;
  news: NewsResponse;
}) {
  const recentRecords = latestRecords(stock.history);
  const latest = recentRecords[0];

  return (
    <div className="content-stack">
      <section className="panel" aria-labelledby="stock-heading">
        <div className="stock-header">
          <div>
            <div className="stock-label">
              <h2 className="stock-symbol" id="stock-heading">
                {stock.symbol}
              </h2>
              <span className="exchange-label">{exchangeFor(stock.symbol)}</span>
            </div>
            <p className="company-name">{stock.company_name ?? "公司名稱未提供"}</p>
          </div>
          <div className="price-block">
            <p className="price-value">
              {formatCurrency(stock.current_price, stock.currency)}
            </p>
            <p className="price-note">最新可用價格 · {stock.currency ?? "-"}</p>
          </div>
        </div>

        <div className="metric-grid" aria-label="公司摘要">
          <div className="metric">
            <div className="metric-label">市值</div>
            <p className="metric-value">
              {formatMarketCap(stock.market_cap, stock.currency)}
            </p>
          </div>
          <div className="metric">
            <div className="metric-label">幣別</div>
            <p className="metric-value">{stock.currency ?? "-"}</p>
          </div>
          <div className="metric">
            <div className="metric-label">最新開盤</div>
            <p className="metric-value">
              {latest ? formatCurrency(latest.open, stock.currency) : "-"}
            </p>
          </div>
          <div className="metric">
            <div className="metric-label">最新收盤</div>
            <p className="metric-value">
              {latest ? formatCurrency(latest.close, stock.currency) : "-"}
            </p>
          </div>
        </div>
      </section>

      <section className="panel chart-panel" aria-labelledby="chart-heading">
        <div className="section-heading">
          <h2 id="chart-heading">收盤價走勢</h2>
          <div className="chart-heading-meta">
            <span>一年 · 每日</span>
            <span className="chart-key"><i className="key-line close" />收盤</span>
            <span className="chart-key"><i className="key-line ma20" />20 日均線</span>
            <span className="chart-key"><i className="key-line ma50" />50 日均線</span>
            <span className="chart-key"><i className="key-line ma200" />200 日均線</span>
          </div>
        </div>
        <PriceChart
          history={stock.history}
          currency={stock.currency}
          movingAverages={analytics.moving_averages}
        />
      </section>

      <AnalyticsPanel analytics={analytics} />

      <FundamentalsPanel fundamentals={fundamentals} />

      <NewsPanel news={news} />

      <section className="panel table-panel" aria-labelledby="market-heading">
        <div className="section-heading">
          <h2 id="market-heading">最近交易日</h2>
          <span>由新到舊</span>
        </div>
        <div className="table-scroll">
          <table className="market-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>開盤</th>
                <th>最高</th>
                <th>最低</th>
                <th>收盤</th>
                <th>成交量</th>
              </tr>
            </thead>
            <tbody>
              {recentRecords.map((record) => (
                <tr key={record.date}>
                  <td>{record.date}</td>
                  <td>{formatNumber(record.open)}</td>
                  <td>{formatNumber(record.high)}</td>
                  <td>{formatNumber(record.low)}</td>
                  <td>{formatNumber(record.close)}</td>
                  <td>{formatVolume(record.volume)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="footer-note">市場資料由 Yahoo Finance 透過 yfinance 提供。</p>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [stock, setStock] = useState<StockResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [fundamentals, setFundamentals] = useState<FundamentalsResponse | null>(null);
  const [news, setNews] = useState<NewsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState("");

  async function runSearch(symbol: string) {
    const normalizedSymbol = symbol.trim().toUpperCase();
    if (!normalizedSymbol || isLoading) {
      return;
    }

    setQuery(normalizedSymbol);
    setLastQuery(normalizedSymbol);
    setError(null);
    setIsLoading(true);

    try {
      const [stockResult, analyticsResult, fundamentalsResult] = await Promise.all([
        fetchStock(normalizedSymbol),
        fetchStockAnalytics(normalizedSymbol),
        fetchFundamentals(normalizedSymbol),
      ]);
      let newsResult: NewsResponse;
      try {
        newsResult = await fetchNews(normalizedSymbol);
      } catch (newsError: unknown) {
        newsResult = {
          symbol: normalizedSymbol,
          provider: "Finnhub",
          available: false,
          message: newsError instanceof StockApiError
            ? newsError.message
            : "目前無法取得公司新聞。",
          articles: [],
        };
      }
      setStock(stockResult);
      setAnalytics(analyticsResult);
      setFundamentals(fundamentalsResult);
      setNews(newsResult);
    } catch (caughtError: unknown) {
      if (caughtError instanceof StockApiError) {
        setError(caughtError.message);
      } else {
        setError("發生未知錯誤，請稍後再試。");
      }
      setStock(null);
      setAnalytics(null);
      setFundamentals(null);
      setNews(null);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(query);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">F</span>
          <span>FINSIGHT</span>
        </div>
        <div className="topbar-meta">
          <span><i className="status-dot" aria-hidden="true" />市場資料連線正常</span>
          <span>研究工作台</span>
        </div>
      </header>

      <main className="dashboard">
        <section className="intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">市場研究 / 工作台</p>
            <h1 id="page-title">深入了解一家公司。</h1>
            <p className="intro-copy">
              在一個安靜清晰的工作台，整理公開公司的重要資料。從股票代號開始。
            </p>
          </div>

          <div>
            <form className="search-form" onSubmit={handleSubmit}>
              <Search className="search-icon" size={17} strokeWidth={1.5} aria-hidden="true" />
              <input
                className="search-input"
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value.toUpperCase())}
                placeholder="輸入股票代號，例如 NVDA"
                aria-label="股票代號"
                autoComplete="off"
              />
              <button className="search-button" type="submit" disabled={isLoading || !query.trim()}>
                {isLoading ? <LoaderCircle className="spin" size={15} aria-hidden="true" /> : <ArrowUpRight size={15} aria-hidden="true" />}
                {isLoading ? "載入中" : "搜尋"}
              </button>
            </form>
            <div className="suggestions" aria-label="Suggested symbols">
              <span className="eyebrow" style={{ margin: "3px 4px 0 0" }}>試試</span>
              {suggestions.map((suggestion) => (
                <button className="suggestion" type="button" key={suggestion} onClick={() => void runSearch(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </section>

        <ComparisonDashboard />

        {isLoading && (
          <section className="panel empty-state" aria-live="polite">
            <div className="empty-inner">
              <LoaderCircle className="empty-icon spin" strokeWidth={1} aria-hidden="true" />
              <h2>正在讀取市場資料</h2>
              <p>正在取得 {lastQuery} 最新可用的資訊。</p>
            </div>
          </section>
        )}
        {!isLoading && error && <ErrorState message={error} onRetry={() => void runSearch(lastQuery)} />}
        {!isLoading && !error && stock && analytics && fundamentals && news && (
          <StockWorkspace
            stock={stock}
            analytics={analytics}
            fundamentals={fundamentals}
            news={news}
          />
        )}
        {!isLoading && !error && !stock && <EmptyState />}
      </main>
    </div>
  );
}
