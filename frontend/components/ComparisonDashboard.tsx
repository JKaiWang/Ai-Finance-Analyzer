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
import {
  COMPARISON_ALERTS_KEY,
  SAVED_COMPARISONS_KEY,
  csvForComparison,
  matchingAlerts,
  shareUrl,
  type ComparisonAlert,
  type SavedComparison,
} from "@/lib/comparison-tools";

export default function ComparisonDashboard() {
  const [selected, setSelected] = useState<string[]>(() => {
    if (typeof window === "undefined") return ["NVDA", "AMD", "INTC"];
    return new URLSearchParams(window.location.search).get("symbols")?.split(",").filter(Boolean).slice(0, 5) ?? ["NVDA", "AMD", "INTC"];
  });
  const [custom, setCustom] = useState("");
  const [period, setPeriod] = useState(() => typeof window === "undefined" ? "5y" : new URLSearchParams(window.location.search).get("period") ?? "5y");
  const [frequency, setFrequency] = useState(() => typeof window === "undefined" ? "1d" : new URLSearchParams(window.location.search).get("frequency") ?? "1d");
  const [benchmark, setBenchmark] = useState(() => typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get("benchmark") ?? "");
  const [revenueMode, setRevenueMode] = useState<RevenueMode>("indexed");
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState<SavedComparison[]>(() => {
    if (typeof window === "undefined") return [];
    try { return JSON.parse(localStorage.getItem(SAVED_COMPARISONS_KEY) ?? "[]") as SavedComparison[]; } catch { return []; }
  });
  const [savedId, setSavedId] = useState("");
  const [alerts, setAlerts] = useState<ComparisonAlert[]>(() => {
    if (typeof window === "undefined") return [];
    try { return JSON.parse(localStorage.getItem(COMPARISON_ALERTS_KEY) ?? "[]") as ComparisonAlert[]; } catch { return []; }
  });
  const [notice, setNotice] = useState<string | null>(null);

  function persistSaved(next: SavedComparison[]) {
    setSaved(next); localStorage.setItem(SAVED_COMPARISONS_KEY, JSON.stringify(next));
  }

  function saveComparison() {
    const item: SavedComparison = { id: crypto.randomUUID(), name: selected.join(" / "), symbols: selected, period, frequency, benchmark, createdAt: new Date().toISOString() };
    persistSaved([item, ...saved]); setNotice(`已保存比較：${item.name}`);
  }

  function loadComparison(item: SavedComparison) {
    setSavedId(item.id); setSelected(item.symbols); setPeriod(item.period); setFrequency(item.frequency); setBenchmark(item.benchmark); setNotice(`已載入：${item.name}`);
  }

  function renameSaved() {
    const item = saved.find((value) => value.id === savedId); if (!item) return;
    const name = window.prompt("新的比較名稱", item.name)?.trim(); if (!name) return;
    persistSaved(saved.map((value) => value.id === savedId ? { ...value, name } : value)); setNotice(`已重新命名：${name}`);
  }

  function deleteSaved() {
    if (!savedId || !window.confirm("刪除這個已保存的比較？")) return;
    persistSaved(saved.filter((value) => value.id !== savedId)); setSavedId(""); setNotice("已刪除保存的比較。");
  }

  function exportCsv() {
    if (!result) return;
    const blob = new Blob(["\ufeff" + csvForComparison(result)], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `finsight-${result.symbols.join("-")}.csv`; link.click(); URL.revokeObjectURL(link.href);
  }

  async function exportPng() {
    const svg = document.querySelector(".comparison-results svg") as SVGSVGElement | null;
    if (!svg) return;
    const source = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const image = new Image(); image.src = URL.createObjectURL(blob);
    await new Promise<void>((resolve) => { image.onload = () => resolve(); image.onerror = () => resolve(); });
    const canvas = document.createElement("canvas"); canvas.width = svg.viewBox.baseVal.width || 800; canvas.height = svg.viewBox.baseVal.height || 400;
    canvas.getContext("2d")?.drawImage(image, 0, 0, canvas.width, canvas.height); URL.revokeObjectURL(image.src);
    canvas.toBlob((png) => { if (!png) return; const link = document.createElement("a"); link.href = URL.createObjectURL(png); link.download = `finsight-${result?.symbols.join("-") ?? "comparison"}.png`; link.click(); URL.revokeObjectURL(link.href); }, "image/png");
    setNotice("已匯出目前圖表 PNG。");
  }

  function addAlert() {
    const symbol = selected[0];
    if (!symbol) return;
    const alert: ComparisonAlert = { id: crypto.randomUUID(), symbol, metric: "one_year_return", operator: "below", threshold: 0 };
    const next = [...alerts, alert]; setAlerts(next); localStorage.setItem(COMPARISON_ALERTS_KEY, JSON.stringify(next)); setNotice(`${symbol} 已建立 1Y 報酬提醒（低於 0%）。`);
  }

  function copyShareUrl() {
    void navigator.clipboard?.writeText(shareUrl({ symbols: selected, period, frequency, benchmark })); setNotice("已複製分享連結。");
  }

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
        <button className="comparison-button secondary" type="button" onClick={saveComparison}>保存</button>
        {saved.length > 0 && <><select className="comparison-saved-select" aria-label="載入已保存比較" value={savedId} onChange={(event) => { const item = saved.find((value) => value.id === event.target.value); if (item) loadComparison(item); }}><option value="">載入比較…</option>{saved.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><button className="comparison-button secondary" type="button" onClick={renameSaved} disabled={!savedId}>改名</button><button className="comparison-button secondary" type="button" onClick={deleteSaved} disabled={!savedId}>刪除</button></>}
      </div>

      {result && <div className="comparison-actions" aria-label="比較工具"><button type="button" onClick={exportCsv}>CSV</button><button type="button" onClick={() => void exportPng()}>PNG</button><button type="button" onClick={() => window.print()}>PDF / Print</button><button type="button" onClick={copyShareUrl}>分享連結</button><button type="button" onClick={addAlert}>建立 1Y 報酬提醒</button>{matchingAlerts(result, alerts).length > 0 && <span className="comparison-alert-notice" role="status">已觸發 {matchingAlerts(result, alerts).length} 個提醒</span>}</div>}
      {notice && <p className="comparison-notice" role="status">{notice}</p>}

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
