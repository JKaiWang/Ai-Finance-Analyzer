import type { ComparisonCompany, ComparisonResponse } from "@/lib/api";

import { colors, factorLabels, type MetricDefinition } from "./config";
import { compact, formatMetric, number, valueFor } from "./formatters";

export function SectionTable({
  title,
  metrics,
  companies,
}: {
  title: string;
  metrics: MetricDefinition[];
  companies: ComparisonCompany[];
}) {
  return (
    <section className="comparison-section" aria-labelledby={`comparison-${title}`}>
      <div className="comparison-section-heading">
        <h3 id={`comparison-${title}`}>{title}</h3>
        <span>{metrics.length} metrics</span>
      </div>
      <div className="table-scroll comparison-table-wrap">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Metric</th>
              {companies.map((company) => <th key={company.symbol}>{company.symbol}</th>)}
            </tr>
          </thead>
          <tbody>
            {metrics.map((metric) => (
              <tr key={metric.key}>
                <th>{metric.label}</th>
                {companies.map((company) => (
                  <td key={company.symbol}>
                    {formatMetric(valueFor(company, metric.key), metric.format)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function Overview({ result }: { result: ComparisonResponse }) {
  return (
    <section className="comparison-overview" aria-labelledby="comparison-overview-heading">
      <div className="comparison-section-heading">
        <h3 id="comparison-overview-heading">Overview</h3>
        <span>{result.period} · {result.frequency} · {result.benchmark ?? "default benchmark"}</span>
      </div>
      <div className="comparison-company-grid">
        {result.companies.map((company, index) => (
          <article
            className="comparison-company-card"
            key={company.symbol}
            style={{ borderTopColor: colors[index] }}
          >
            <div className="comparison-company-card-heading">
              <div>
                <strong>{company.symbol}</strong>
                <span>{company.company_name ?? "Company information unavailable"}</span>
              </div>
              <b>{company.available ? "READY" : "N/A"}</b>
            </div>
            <div className="comparison-company-facts">
              <span>{company.sector ?? "Sector -"}</span>
              <span>{company.currency ?? "Currency -"}</span>
              <span>{company.exchange ?? "Exchange -"}</span>
            </div>
            <div className="comparison-company-price">
              {number(company.current_price)} <small>{company.currency ?? ""}</small>
            </div>
            <div className="comparison-company-facts">
              <span>Market Cap {compact(company.market_cap)}</span>
              <span>EV {compact(company.enterprise_value)}</span>
            </div>
            {company.errors.length > 0 && (
              <p className="comparison-data-note">Partial data: {company.errors.join("; ")}</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

export function ResearchSummary({ companies }: { companies: ComparisonCompany[] }) {
  return (
    <section className="comparison-section" aria-labelledby="comparison-summary-heading">
      <div className="comparison-section-heading">
        <h3 id="comparison-summary-heading">Investment Summary</h3>
        <span>Deterministic · no buy/sell advice</span>
      </div>
      <div className="comparison-summary-grid">
        {companies.map((company) => (
          <article className="comparison-summary-card" key={company.symbol}>
            <h4>{company.symbol}</h4>
            <div>
              <strong>Strengths</strong>
              {company.research_summary?.strengths.length ? (
                company.research_summary.strengths.slice(0, 4).map((item) => (
                  <p key={`${item.factor}-${item.reason}`}>
                    + {factorLabels[item.factor] ?? item.factor} <small>{item.score === null ? "" : Math.round(item.score)}</small>
                  </p>
                ))
              ) : <p className="comparison-empty">No strong peer signal.</p>}
            </div>
            <div>
              <strong>Weaknesses</strong>
              {company.research_summary?.weaknesses.length ? (
                company.research_summary.weaknesses.slice(0, 4).map((item) => (
                  <p key={`${item.factor}-${item.reason}`}>
                    − {factorLabels[item.factor] ?? item.factor} <small>{item.score === null ? "" : Math.round(item.score)}</small>
                  </p>
                ))
              ) : <p className="comparison-empty">No weak peer signal.</p>}
            </div>
          </article>
        ))}
      </div>
      <p className="comparison-disclaimer">{companies[0]?.research_summary?.disclaimer}</p>
    </section>
  );
}
