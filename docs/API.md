# FinSight API Notes

The API is served by FastAPI and exposes interactive OpenAPI documentation at
`/docs` when the backend is running.

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Health check |
| `GET` | `/stocks/{symbol}` | Profile and historical prices |
| `GET` | `/stocks/{symbol}/analytics` | Returns, volatility and benchmark metrics |
| `GET` | `/stocks/{symbol}/fundamentals` | Statements and derived financial metrics |
| `GET` | `/stocks/{symbol}/news` | Recent normalized company news |
| `GET` | `/compare` | Comparison for 2–5 symbols |

## Comparison example

```bash
curl "http://127.0.0.1:8000/compare?symbols=NVDA,AMD,INTC&period=5y&frequency=1d"
```

## Data status

Analytics, fundamentals and news responses expose `data_status`:

- `available` — requested data was returned with no known missing fields.
- `partial` — the provider responded, but some metrics or fields were unavailable.
- `unavailable` — the service is not configured or the provider could not return data.

The status includes `source`, `as_of`, `message` and `missing_fields` so clients can
show the difference between a real zero, an unavailable value and a provider failure.

## Provider limitations

- Market and financial data comes from Yahoo Finance through `yfinance`.
- News comes from Finnhub when `FINNHUB_API_KEY` is configured.
- Provider data can be delayed, revised, rate-limited or temporarily unavailable.
- Missing financial inputs are preserved as `null`; clients should render them as
  unavailable rather than as zero.
