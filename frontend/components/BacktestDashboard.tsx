"use client";

import { useState } from "react";
import { fetchBacktest, StockApiError, type BacktestResponse } from "@/lib/api";

function percent(value: number | null) { return value === null ? "N/A" : `${(value * 100).toFixed(2)}%`; }

export default function BacktestDashboard() {
  const [symbols, setSymbols] = useState("NVDA,AMD,INTC,AAPL,MSFT");
  const [horizon, setHorizon] = useState("3m");
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    const values = symbols.split(",").map((value) => value.trim()).filter(Boolean);
    setLoading(true); setError(null);
    try { setResult(await fetchBacktest(values, { horizon })); }
    catch (caught: unknown) { setError(caught instanceof StockApiError ? caught.message : "回測失敗。"); }
    finally { setLoading(false); }
  }

  return <section className="panel backtest-panel" aria-labelledby="backtest-heading">
    <div className="section-heading"><div><h2 id="backtest-heading">Formula Backtest</h2><span>用歷史資料訓練可解釋的因子權重，再做 out-of-sample 測試。</span></div></div>
    <div className="backtest-controls"><input className="comparison-input" value={symbols} onChange={(event) => setSymbols(event.target.value.toUpperCase())} aria-label="回測股票代號" /><select value={horizon} onChange={(event) => setHorizon(event.target.value)} aria-label="預測期間"><option value="1m">1M</option><option value="3m">3M</option><option value="6m">6M</option><option value="12m">12M</option></select><button className="comparison-button" type="button" onClick={() => void run()} disabled={loading}>{loading ? "訓練中" : "開始回測"}</button></div>
    {error && <p className="comparison-error" role="alert">{error}</p>}
    {result && <div className="backtest-results"><div className="backtest-metrics"><div><small>Train CAGR</small><strong>{percent(result.train.cagr)}</strong></div><div><small>Test CAGR</small><strong>{percent(result.test.cagr)}</strong></div><div><small>Test Drawdown</small><strong>{percent(result.test.maximum_drawdown)}</strong></div><div><small>Test Hit Rate</small><strong>{percent(result.test.hit_rate)}</strong></div></div><div className="backtest-weight-list"><strong>Trained formula</strong>{Object.entries(result.weights).map(([key, value]) => <span key={key}>{key.replaceAll("_", " ")} {Math.round(value * 100)}%</span>)}</div><div className="backtest-recommendations"><strong>Current research ranking</strong>{result.recommendations.map((item) => <div key={item.symbol}><b>#{item.rank} {item.symbol}</b><span>{item.label} · score {item.score.toFixed(1)}</span></div>)}</div><p className="comparison-disclaimer">此排名只代表歷史回測模型訊號，不是保證報酬或個人化投資建議。</p></div>}
  </section>;
}
