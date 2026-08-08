"use client";

import { useState } from "react";

import {
  fetchComparison,
  StockApiError,
  type ComparisonResponse,
} from "@/lib/api";

import {
  fundamentalMetrics,
  performanceMetrics,
  riskMetrics,
  suggestions,
  valuationMetrics,
  type RevenueMode,
} from "./comparison/config";
import {
  Heatmap,
  NormalizedChart,
  RadarComparison,
  TrendChart,
} from "./comparison/ComparisonCharts";
import {
  Overview,
  ResearchSummary,
  SectionTable,
} from "./comparison/ComparisonSections";

export default function ComparisonDashboard() {
  const [selected, setSelected] = useState<string[]>(["NVDA", "AMD", "INTC"]);
  const [custom, setCustom] = useState("");
  const [period, setPeriod] = useState("5y");
  const [frequency, setFrequency] = useState("1d");
  const [benchmark, setBenchmark] = useState("");
  const [revenueMode, setRevenueMode] = useState<RevenueMode>("indexed");
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function toggle(symbol: string) {
    setSelected((current) => current.includes(symbol)
      ? current.filter((value) => value !== symbol)
      : [...current, symbol]);
  }

  async function compare() {
    const customSymbols = custom
      .split(",")
      .map((value) => value.trim().toUpperCase())
      .filter(Boolean);
    const symbols = [...new Set([...selected, ...customSymbols])];

    if (symbols.length < 2 || symbols.length > 5) {
      setError("請選擇 2–5 支股票再開始比較。");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      setResult(await fetchComparison(symbols, {
        period,
        frequency,
        benchmark: benchmark.trim().toUpperCase(),
      }));
    } catch (caughtError: unknown) {
      setError(caughtError instanceof StockApiError ? caughtError.message : "比較資料取得失敗。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel comparison-panel" aria-labelledby="comparison-heading">
      <div className="section-heading">
        <div>
          <h2 id="comparison-heading">公司比較</h2>
          <span>Overview、Performance、Risk、Valuation、Fundamentals 與 Summary</span>
        </div>
      </div>

      <div className="comparison-controls">
        <div className="comparison-options">
          {suggestions.map((symbol) => (
            <label key={symbol} className="comparison-option">
              <input type="checkbox" checked={selected.includes(symbol)} onChange={() => toggle(symbol)} />
              {symbol}
            </label>
          ))}
        </div>
        <input className="comparison-input" value={custom} onChange={(event) => setCustom(event.target.value.toUpperCase())} placeholder="其他代號，以逗號分隔" aria-label="其他比較股票代號" />
        <label className="comparison-select-label">Period<select value={period} onChange={(event) => setPeriod(event.target.value)}><option value="1y">1Y</option><option value="5y">5Y</option><option value="10y">10Y</option></select></label>
        <label className="comparison-select-label">Frequency<select value={frequency} onChange={(event) => setFrequency(event.target.value)}><option value="1d">Daily</option><option value="1wk">Weekly</option><option value="1mo">Monthly</option></select></label>
        <input className="comparison-input comparison-benchmark-input" value={benchmark} onChange={(event) => setBenchmark(event.target.value.toUpperCase())} placeholder="Benchmark（選填）" aria-label="Benchmark" />
        <button className="comparison-button" type="button" onClick={() => void compare()} disabled={loading}>{loading ? "比較中" : "開始比較"}</button>
      </div>

      {error && <p className="comparison-error" role="alert">{error}</p>}

      {result && (
        <div className="comparison-results">
          <Overview result={result} />
          <div className="comparison-visuals">
            <div>
              <div className="comparison-visual-heading"><h3>Normalized Price</h3><span>起始值 = 100</span></div>
              <NormalizedChart companies={result.companies} />
            </div>
            <div>
              <div className="comparison-visual-heading"><h3>Six-factor Radar</h3><span>Peer score 0–100</span></div>
              <RadarComparison companies={result.companies} />
            </div>
          </div>

          <div className="comparison-section-grid">
            <SectionTable title="Performance" metrics={performanceMetrics} companies={result.companies} />
            <SectionTable title="Risk" metrics={riskMetrics} companies={result.companies} />
            <SectionTable title="Valuation" metrics={valuationMetrics} companies={result.companies} />
          </div>
          <SectionTable title="Growth · Profitability · Financial Health · Dividend · Ownership" metrics={fundamentalMetrics} companies={result.companies} />

          <section className="comparison-section" aria-labelledby="comparison-heatmap-heading">
            <div className="comparison-section-heading"><h3 id="comparison-heatmap-heading">Heatmap</h3><span>Score + raw value · Green = stronger · Red = weaker</span></div>
            <Heatmap companies={result.companies} />
          </section>

          <section className="comparison-section" aria-labelledby="comparison-trend-heading">
            <div className="comparison-section-heading">
              <h3 id="comparison-trend-heading">Trend Comparison</h3>
              <label className="comparison-select-label">Revenue<select value={revenueMode} onChange={(event) => setRevenueMode(event.target.value as RevenueMode)} aria-label="Revenue display mode"><option value="indexed">Indexed Growth</option><option value="absolute">Absolute Value</option><option value="yoy">YoY Growth</option></select></label>
            </div>
            <div className="comparison-trend-grid">
              <TrendChart companies={result.companies} trend="revenue" title="Revenue" format="number" mode={revenueMode} />
              <TrendChart companies={result.companies} trend="eps" title="EPS" format="number" />
              <TrendChart companies={result.companies} trend="free_cash_flow" title="Free Cash Flow" format="number" />
              <TrendChart companies={result.companies} trend="net_margin" title="Net Margin" format="percent" />
            </div>
          </section>

          <ResearchSummary companies={result.companies} />
        </div>
      )}
    </section>
  );
}
