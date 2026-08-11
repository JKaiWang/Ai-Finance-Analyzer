ㄎ

# FinSight Product & Engineering Roadmap

## 1. Product Direction

FinSight 是 AI Investment Research Platform，不是單純股票查詢網站。

核心問題：

> 哪家公司成長較快、品質較高、估值較合理、風險較低，以及目前價格動能是否支持投資觀點？

設計原則：

- 使用 Equity Research workflow
- 所有資料顯示 source、as_of、period 與 reported/estimated 狀態
- 缺失資料顯示 `N/A`，不可當成 0
- Radar 與 Heatmap 是 peer-relative score，不是絕對投資評級
- Investment Summary 只使用結構化資料與規則引擎，不直接呼叫 LLM
- 不輸出 Buy、Sell 或保證報酬

## 2. Compare Page Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FinSight / Compare                                                           │
│ Compare: [ NVDA ] [ AMD ] [ INTC ] [+ Add company]       [Compare] [Save]   │
│ Benchmark: [S&P 500 ▼]   Currency: [USD ▼]   Period: [5Y ▼]                │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ Research Snapshot                                                            │
│ Company | Sector | Market Cap | Enterprise Value | Overall Score             │
│ Strongest Dimension | Main Risk                                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. Overview                                                                  │
│ Company | Industry | Sector | Country | Exchange | Market Cap | EV | Beta    │
├──────────────────────────────────────────────────────────────────────────────┤
│ 2. Price Performance                                                         │
│ 1W | 1M | 3M | 6M | YTD | 1Y | 3Y | 5Y | CAGR | Alpha | Beta                │
│ Normalized Price Chart                                                       │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ 3. Risk                       │ 4. Valuation                                  │
│ Volatility / Drawdown         │ PE / Forward PE / PEG                         │
│ Sharpe / Sortino / Calmar     │ PB / PS / EV/EBITDA / EV/Sales                │
│ Beta / Downside Volatility    │                                              │
├───────────────────────────────┼──────────────────────────────────────────────┤
│ 5. Growth                     │ 6. Profitability                              │
│ Revenue / EPS / Net Income    │ Gross / Operating / EBITDA / Net Margin       │
│ FCF / Book Value Growth       │ ROE / ROA / ROIC                              │
├───────────────────────────────┼──────────────────────────────────────────────┤
│ 7. Financial Health            │ 8. Dividend                                  │
│ Current / Quick / Cash Ratio  │ Yield / Growth / Payout Ratio                 │
│ Debt/Equity / Interest Cover  │ Dividend History                             │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ 9. Ownership: Insider | Institutional | Float | Shares Outstanding           │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ 10. Six-Factor Radar           │ 11. Metric Heatmap                            │
│ Growth / Profitability        │ Revenue Growth / ROIC / Debt / Equity         │
│ Valuation / Risk              │ N/A 顯示灰色，估值指標使用反向 ranking          │
│ Financial Health / Momentum   │                                              │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ 12. Trend: Revenue | EPS | Free Cash Flow | Gross Margin                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ 13. Investment Summary: Strengths | Weaknesses | Growth | Risk | Valuation   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 3. Component Tree

```text
ComparePage
├── CompareHeader
│   ├── CompanySelector
│   ├── BenchmarkSelector
│   ├── CurrencySelector
│   ├── PeriodSelector
│   ├── SaveComparisonButton
│   └── ExportButton
├── ResearchSnapshot
├── OverviewSection
├── PerformanceSection
│   ├── ReturnPeriodTabs
│   ├── PerformanceTable
│   ├── CAGRTable
│   └── NormalizedPriceChart
├── RiskSection
├── ValuationSection
├── GrowthSection
├── ProfitabilitySection
├── FinancialHealthSection
├── DividendSection
├── OwnershipSection
├── ScorecardSection
│   ├── InvestmentRadar
│   ├── ScoreMethodologyPopover
│   └── ScoreDisclaimer
├── HeatmapSection
│   ├── HeatmapFilter
│   ├── MetricHeatmap
│   └── HeatmapLegend
├── TrendComparisonSection
│   ├── RevenueTrendChart
│   ├── EPSTrendChart
│   ├── FreeCashFlowTrendChart
│   └── MarginTrendChart
├── InvestmentSummarySection
│   ├── StrengthsCard
│   ├── WeaknessesCard
│   ├── GrowthCard
│   ├── RiskCard
│   ├── ValuationCard
│   └── InvestmentHighlightsCard
└── DataQualityFooter
```

## 4. Metric Design

### Performance

```text
period_return = current_price / period_start_price - 1
CAGR = (ending_value / beginning_value) ^ (1 / years) - 1
Beta = Cov(stock_returns, benchmark_returns) / Variance(benchmark_returns)
Alpha = R_stock - [Rf + Beta × (R_benchmark - Rf)]
```

支援 `1W`, `1M`, `3M`, `6M`, `YTD`, `1Y`, `3Y`, `5Y`。

### Risk

```text
Annualized Volatility = stdev(daily_returns) × sqrt(252)
Downside Volatility = stdev(min(return - target, 0)) × sqrt(252)
Sharpe = annualized_return / annualized_volatility
Sortino = annualized_return / downside_volatility
Calmar = CAGR / abs(maximum_drawdown)
```

### Valuation

```text
PE = Price / EPS
PEG = PE / EPS_growth_percentage
PB = Market Cap / Book Equity
PS = Market Cap / Revenue
EV/EBITDA = Enterprise Value / EBITDA
EV/Sales = Enterprise Value / Revenue
```

負 EPS 顯示 `N/M`。Forward PE 必須來自 estimates，不可用歷史 EPS 假裝。

### Profitability and Health

```text
Gross Margin = Gross Profit / Revenue
Operating Margin = Operating Income / Revenue
EBITDA Margin = EBITDA / Revenue
Net Margin = Net Income / Revenue
ROE = Net Income / Average Equity
ROA = Net Income / Average Assets
ROIC = NOPAT / Average Invested Capital
Current Ratio = Current Assets / Current Liabilities
Quick Ratio = (Cash + Short-term Investments + Receivables) / Current Liabilities
Cash Ratio = Cash / Current Liabilities
Debt / Equity = Total Debt / Total Equity
Interest Coverage = EBIT / Interest Expense
```

## 5. Six-Factor Radar

所有分數使用本次 peer group 的 percentile ranking，範圍為 0–100。

```text
Growth:
  Revenue Growth 25%, EPS Growth 25%, FCF Growth 20%,
  Net Income Growth 15%, Book Value Growth 15%

Profitability:
  ROIC 25%, Operating Margin 20%, Net Margin 20%, ROE 20%, ROA 15%

Valuation:
  PE 20%, Forward PE 20%, EV/EBITDA 20%, EV/Sales 15%, PEG 15%, FCF Yield 10%

Risk:
  Sharpe 25%, Sortino 20%, low Volatility 20%,
  low Downside Volatility 15%, low Maximum Drawdown 20%

Financial Health:
  Current Ratio 20%, Quick Ratio 15%, Cash Ratio 15%,
  Interest Coverage 20%, low Debt/Equity 20%, FCF/Debt 10%

Momentum:
  1M Return 15%, 3M Return 20%, 6M Return 20%, 1Y Return 20%,
  Price vs MA200 15%, Relative Strength 10%
```

## 6. Heatmap

```text
90–100  深綠 / 強
70–89   綠
40–69   黃
20–39   橘
0–19    紅 / 弱
N/A     灰色
```

估值與風險指標使用反向 ranking。例如低 PE、低 Debt/Equity、低 Drawdown 才得到較高分。

## 7. Deterministic Investment Summary

### Strength Rules

- 維度分數 >= 80 percentile：加入該維度為 Strength
- ROIC 高於 peer median：加入資本效率優勢
- Revenue Growth 或 FCF Growth 高於 peer median：加入成長優勢

### Weakness Rules

- Valuation Score <= 25：加入估值偏高
- Drawdown 或 volatility 位於最差 25%：加入歷史風險
- Debt/Equity 高於 peer median：加入槓桿風險
- FCF Growth < 0：加入自由現金流轉弱

輸出格式：

```text
Strengths
Weaknesses
Growth
Risk
Valuation
Investment Highlights
```

## 8. Backend API

### Aggregated Compare API

```text
GET /compare?
symbols=NVDA,AMD,INTC
&benchmark=^GSPC
&period=5y
&frequency=annual
&currency=USD
```

```json
{
  "symbols": ["NVDA", "AMD", "INTC"],
  "benchmark": "^GSPC",
  "period": "5y",
  "as_of": "2026-08-05",
  "companies": [],
  "scores": [],
  "heatmap": [],
  "trends": [],
  "summary": {},
  "data_quality": {}
}
```

### Detail APIs

```text
GET /compare/{symbol}/overview
GET /compare/{symbol}/performance?period=5y
GET /compare/{symbol}/risk?period=5y
GET /compare/{symbol}/valuation
GET /compare/{symbol}/growth?frequency=annual
GET /compare/{symbol}/profitability?frequency=annual
GET /compare/{symbol}/financial-health
GET /compare/{symbol}/dividend
GET /compare/{symbol}/ownership
GET /compare/{symbol}/estimates
GET /stocks/{symbol}/peers
POST /compare/summary
```

`POST /compare/summary` 只執行 deterministic rules，不呼叫 LLM。

## 9. Future Database Tables

```text
instruments
price_bars
financial_periods
income_statements
balance_sheets
cash_flows
valuation_snapshots
analyst_estimates
dividend_records
ownership_snapshots
benchmark_returns
metric_snapshots
comparison_runs
saved_comparisons
data_quality_events
```

每個金融資料表至少需要 `instrument_id`、`period/as_of`、`source`、`currency`、`reported_or_estimated`、`created_at` 與 `updated_at`。

## 10. Features to Add Later

### Recommended

- 自動與自訂 Peer Group
- Annual / Quarterly / TTM selector
- Analyst estimates 與 earnings surprise
- Valuation history
- Price vs benchmark
- MA、RSI、MACD、relative strength
- Saved comparison
- CSV / PNG / PDF export
- Valuation、margin、earnings alerts
- 完整 data quality 與 freshness 顯示

### Not Recommended Yet

- 即時行情：需要專業 market data provider 與授權
- 完整 DCF：需要 forecast、WACC、terminal growth 與 scenario model
- 自動 Buy/Sell 建議
- 社群情緒
- Portfolio optimization：應放在 Epic 7 之後

## 11. Existing Project Roadmap

### Epic 0：Project Initialization

- [X] 建立 backend 與 frontend 目錄
- [X] 初始化 Git 與 Python 專案
- [X] 安裝 FastAPI、yfinance、pandas、pytest、ruff
- [X] 建立基本 `.gitignore`

### Epic 1：Market Data API

- [X] `GET /stocks/{symbol}`
- [X] yfinance 市場資料串接
- [X] 公司名稱、價格、市值與歷史資料
- [X] 美股與台股代號
- [X] Swagger 文件
- [X] 404、502、500 錯誤處理
- [X] Logging、pytest、Ruff

### Epic 2：Frontend Dashboard

- [X] Next.js、TypeScript、App Router
- [X] 股票搜尋與 API Client
- [X] 公司基本資訊
- [X] 交易統計與價格圖
- [X] Loading、錯誤與空狀態
- [X] Responsive layout、lint、build

### Epic 3：Quant Analytics

- [X] Daily Return
- [X] 1M / 3M / 6M / 1Y Return
- [X] Annualized Volatility
- [X] Maximum Drawdown
- [X] MA20 / MA50 / MA200
- [X] Sharpe Ratio
- [X] Benchmark Comparison
- [X] Analytics API 與前端指標卡

### Epic 4：Fundamental Analysis

- [X] Income Statement
- [X] Balance Sheet
- [X] Cash Flow
- [X] Growth Metrics
- [X] Profitability Metrics
- [X] Financial Health Metrics
- [X] Fundamentals API
- [X] Financial Trend Charts

### Epic 5：News Intelligence

- [X] 選擇 Finnhub News API
- [X] 使用環境變數保存 API Key
- [X] 新聞列表、摘要、來源、日期與連結
- [X] URL 與標題相似度去重
- [X] Earnings、Product、Regulation、Management、Supply Chain、Macroeconomics、Geopolitics 分類
- [X] Positive、Neutral、Negative 情緒與信心分數
- [X] Event Timeline
- [ ] 比較 Finnhub、Alpha Vantage、News API 的完整研究報告

### Epic 6：Company Comparison

#### Task 6-1：Comparison API

- [X] 接收多個股票代號
- [X] 限制 2–5 支股票
- [X] 統一比較格式
- [X] 擴充為本文件定義的完整聚合 API

#### Task 6-2：價格與風險

- [X] 一年報酬
- [X] 波動率
- [X] 最大回撤
- [X] Sharpe Ratio
- [X] 1W / 1M / 3M / 6M / YTD / 3Y / 5Y
- [X] CAGR / Alpha / Beta / Sortino / Calmar

#### Task 6-3：基本面

- [X] Revenue Growth
- [X] Gross Margin
- [X] Net Margin
- [X] ROE
- [X] Free Cash Flow
- [X] 本益比估值
- [X] Forward PE / PEG / PB / PS / EV/EBITDA / EV/Sales（provider 有資料時）
- [X] EBITDA Margin / ROA / ROIC
- [X] Dividend / Ownership metrics（provider 有資料時）

#### Task 6-4：比較 UI

- [X] 股票多選
- [X] 比較表格
- [X] 正規化價格圖
- [X] Radar Chart
- [X] Overview / Risk / Valuation / Growth / Profitability sections
- [X] Heatmap
- [X] Trend Comparison
- [X] Deterministic Investment Summary

## 12. Detailed Delivery Roadmap

### Epic 6A：Comparison Data Foundation

#### Task 6A-1：擴充市場資料（1.5 天）

- [X] 5Y / 10Y history
- [X] adjusted close
- [X] Benchmark 對齊基礎工具
- [X] 交易日缺口處理（只保留共同交易日，不補造資料）
- [X] source / as_of

#### Task 6A-2：擴充公司資訊（1 天）

- [X] Sector
- [X] Industry
- [X] Country
- [X] Exchange
- [X] Enterprise Value
- [X] Shares Outstanding

#### Task 6A-3：統一 Metric Model（1.5 天）

- [X] value、period、source、as_of
- [X] reported / estimated
- [X] N/A reason / provider availability metadata

### Epic 6B：Performance & Risk Engine

#### Task 6B-1：多期間報酬（1 天）

- [X] 1W / 1M / 3M / 6M / YTD / 1Y / 3Y / 5Y

#### Task 6B-2：CAGR / Alpha / Beta（1.5 天）

- [X] Benchmark alignment
- [ ] Rolling beta
- [X] CAPM alpha
- [X] CAGR

#### Task 6B-3：風險指標（1.5 天）

- [X] Sortino
- [X] Calmar
- [X] Downside volatility
- [ ] Rolling drawdown
- [X] Edge-case tests

> Dashboard review notes are tracked under Epic 6H so implementation requirements and delivery status stay separate.

### Epic 6C：Fundamental Intelligence

#### Task 6C-1：Valuation Engine（2 天）

- [X] PE / Forward PE / PEG
- [X] PB / PS
- [X] EV/EBITDA / EV/Sales
- [X] Negative EPS handling

#### Task 6C-2：Growth Engine（1.5 天）

- [X] Revenue / EPS / Net Income growth
- [X] FCF / Book Value growth
- [ ] 3Y / 5Y CAGR

#### Task 6C-3：Profitability Engine（1.5 天）

- [X] EBITDA Margin
- [X] ROA
- [X] ROIC
- [ ] Average balance calculation
- [ ] Tax rate fallback

#### Task 6C-4：Health / Dividend / Ownership（2 天）

- [X] Quick Ratio
- [X] Cash Ratio
- [X] Interest Coverage
- [X] Dividend metrics
- [X] Ownership metrics
- [X] Missing data handling

### Epic 6D：Score & Research Logic

#### Task 6D-1：Peer-relative Scoring（1.5 天）

- [X] Percentile ranking
- [X] Inverse valuation metrics
- [X] N/A exclusion
- [X] Minimum sample size
- [X] Score confidence

#### Task 6D-2：Six-factor Radar（1 天）

- [X] Growth
- [X] Profitability
- [X] Valuation
- [X] Risk
- [X] Financial Health
- [X] Momentum

#### Task 6D-3：Heatmap Engine（1 天）

- [X] Metric ranking
- [X] Color buckets
- [X] Metric direction
- [X] N/A state

#### Task 6D-4：Deterministic Summary（1.5 天）

- [X] Strength rules
- [X] Weakness rules
- [X] Growth / Risk / Valuation rules
- [X] Disclaimer

### Epic 6E：Compare API

#### Task 6E-1：聚合 API（1.5 天）

- [X] Single `/compare` response
- [X] Benchmark / period / frequency
- [X] Parallel data loading
- [X] Partial data isolation

#### Task 6E-2：API Tests（1 天）

- [X] 2–5 symbols
- [X] Missing fundamentals
- [X] Missing dividends
- [X] Provider failure
- [X] Partial response

### Epic 6F：Compare UI

#### Task 6F-1：Header 與 Overview（1 天）

- [X] Company selector
- [X] Benchmark selector
- [X] Period selector
- [X] Overview cards
- [X] Responsive layout

#### Task 6F-2：Performance / Risk / Valuation（2 天）

- [X] Comparison tables
- [X] Normalized chart
- [X] Risk tables
- [X] Valuation tables
- [X] N/A styling

#### Task 6F-3：Fundamental Sections（2 天）

- [X] Growth
- [X] Profitability
- [X] Financial health
- [X] Dividend
- [X] Ownership

#### Task 6F-4：Radar / Heatmap / Trend（2 天）

- [X] Six-factor radar
- [X] Heatmap
- [X] Revenue trend
- [X] EPS trend
- [X] FCF trend
- [X] Margin trend

#### Task 6F-5：Investment Summary（1 天）

- [X] Strength cards
- [X] Weakness cards
- [X] Growth / Risk / Valuation summary
- [X] Data quality footer

### Epic 6G：Research Product Features

#### Task 6G-1：Saved Comparison（1.5 天）

- [X] Save / Load
- [X] Rename / Delete（localStorage-backed saved records）

#### Task 6G-2：Export（1.5 天）

- [X] CSV export with raw comparison values
- [X] PNG chart export
- [X] PDF / print export
- [X] Shareable URL containing symbols, period, frequency and benchmark

#### Task 6G-3：Alerts（2 天）

- [X] Persisted threshold alert foundation
- [X] 1Y return alert creation and triggered-state display
- [ ] Valuation / margin / price / earnings alert editors

> Saved comparisons and alerts are intentionally client-local in this iteration. Cross-device sync and scheduled notifications require a future database-backed account layer.

### Epic 6H：Quality & Validation

#### Task 6H-1：Financial Validation（2 天）

- [X] Known financial statement checks and chronological trend ordering
- [ ] Cross-currency tests
- [X] Negative EPS / FCF and unavailable-value tests
- [ ] Industry-specific tests
- [X] Configurable ranking direction and null-safe percentile tests
- [X] Formula review for growth, ROIC, volatility, P/E, current ratio and return

#### Task 6H-2：UX Validation（1 天）

- [X] Mobile layout and horizontally scrollable comparison tables
- [X] Large company lists bounded to 2–5 symbols
- [X] Missing fields rendered as N/A without zero substitution
- [X] Long company names and partial-provider errors rendered safely
- [ ] Formal color-contrast audit
- [X] Native controls and buttons remain keyboard accessible

#### Task 6H-3：Performance（1 天）

- [X] Parallel API loading
- [X] Response caching and upstream retry controls
- [ ] Lazy chart loading
- [X] Loading skeleton

## 13. Estimate and Order

MVP：18–24 engineering days。

完整產品化版本：28–38 engineering days（6G client-local foundation included）。

```text
6A Data Foundation
  ↓
6B Performance & Risk
  ↓
6C Fundamental Intelligence
  ↓
6D Score & Summary
  ↓
6E Compare API
  ↓
6F Compare UI
  ↓
6G Saved / Export / Alerts
  ↓
6H Validation
```

## 14. Epic 7：Backtesting & Formula Research（進行中）

第一階段採用可解釋、price-based 的 walk-forward baseline；不使用隨機切分，也不把未來資料放入特徵。

### 7A：Historical Research Dataset

- [X] 5Y / 10Y 月資料
- [X] Adjusted close
- [X] 3M / 6M / 12M momentum features
- [X] Rolling volatility 與 trailing drawdown features
- [X] Future-return labels
- [X] Annual fundamental snapshots with conservative 90-day availability lag

### 7B：Formula Training

- [X] Cross-sectional percentile scoring
- [X] Weight-grid training
- [X] Monthly rebalance baseline
- [X] Train / out-of-sample test split
- [X] Fundamental factors: revenue growth、ROIC、net margin、current ratio、debt/equity、P/E
- [X] Transaction cost and slippage parameters
- [ ] Full point-in-time filing publication dates
- [ ] Survivorship-bias controls

### 7C：Backtest API & Research UI

- [X] `GET /backtest`
- [X] CAGR、volatility、Sharpe、maximum drawdown、hit rate
- [X] Current formula weights
- [X] Current research ranking
- [X] 前端 Formula Backtest panel
- [ ] Persistent experiment runs
- [ ] Fundamental-factor formula training
- [ ] Recommendation history 與 model versioning

> 回測排名是歷史研究訊號，不是保證報酬、個人化投資建議或直接 Buy/Sell 指令。
