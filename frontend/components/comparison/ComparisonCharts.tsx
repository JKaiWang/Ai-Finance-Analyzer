import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ComparisonCompany } from "@/lib/api";

import {
  colors,
  factorLabels,
  heatmapMetrics,
  type RevenueMode,
} from "./config";
import { formatMetric, sortPeriods } from "./formatters";

const chartStyle = {
  border: "1px solid #3a3a38",
  background: "#191919",
  color: "#eeeeec",
};

export function NormalizedChart({ companies }: { companies: ComparisonCompany[] }) {
  const data = useMemo(() => {
    const points = new Map<string, Record<string, string | number>>();
    companies.forEach((company) => company.normalized_history.forEach((record) => {
      const point = points.get(record.date) ?? { date: record.date };
      point[company.symbol] = record.value;
      points.set(record.date, point);
    }));
    return [...points.values()].sort((left, right) => String(left.date).localeCompare(String(right.date)));
  }, [companies]);

  return (
    <div className="comparison-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#242424" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: "#777", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(value: string) => value.slice(0, 7)} />
          <YAxis tick={{ fill: "#777", fontSize: 10 }} tickLine={false} axisLine={false} width={64} />
          <Tooltip contentStyle={chartStyle} />
          <Legend wrapperStyle={{ color: "#8c8c88", fontSize: 10 }} />
          {companies.map((company, index) => <Line key={company.symbol} type="monotone" dataKey={company.symbol} stroke={colors[index]} strokeWidth={2} dot={false} connectNulls />)}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RadarComparison({ companies }: { companies: ComparisonCompany[] }) {
  const data = Object.keys(factorLabels).map((key) => ({
    subject: factorLabels[key],
    ...Object.fromEntries(companies.map((company) => [company.symbol, company.factor_scores[key] ?? 50])),
  }));

  return (
    <div className="comparison-radar">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="68%">
          <PolarGrid stroke="#383836" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "#aaa", fontSize: 10 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          {companies.map((company, index) => <Radar key={company.symbol} name={company.symbol} dataKey={company.symbol} stroke={colors[index]} fill={colors[index]} fillOpacity={0.16} strokeWidth={2} />)}
          <Legend wrapperStyle={{ color: "#8c8c88", fontSize: 10 }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Heatmap({ companies }: { companies: ComparisonCompany[] }) {
  return (
    <div className="comparison-heatmap">
      <div className="comparison-heatmap-row comparison-heatmap-header">
        <span>Metric</span>
        {companies.map((company) => <span key={company.symbol}>{company.symbol}</span>)}
      </div>
      {heatmapMetrics.map((metric) => (
        <div className="comparison-heatmap-row" key={metric.key}>
          <strong>{metric.label}</strong>
          {companies.map((company) => {
            const cell = company.heatmap[metric.key];
            const score = cell?.score;
            const className = score === null || score === undefined
              ? "is-na"
              : score >= 75 ? "is-strong" : score <= 25 ? "is-weak" : "is-neutral";
            return (
              <span className={`heatmap-cell ${className}`} key={company.symbol}>
                <b>{score === null || score === undefined ? "—" : Math.round(score)}</b>
                <small>{cell?.value === null || cell?.value === undefined ? "N/A" : formatMetric(cell.value, metric.format)}</small>
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function trendPoints(company: ComparisonCompany, trend: string, mode: RevenueMode) {
  const points = sortPeriods(company.financial_trends[trend] ?? []);
  if (trend !== "revenue" || mode === "absolute") return points;
  if (mode === "indexed") {
    const first = points.find((point) => typeof point.value === "number" && Number.isFinite(point.value) && point.value > 0)?.value;
    return points.map((point) => ({ ...point, value: first && point.value !== null ? point.value / first * 100 : null }));
  }
  return points.map((point, index) => {
    const previous = points[index - 1]?.value;
    return { ...point, value: point.value !== null && typeof previous === "number" && previous !== 0 ? point.value / previous - 1 : null };
  });
}

export function TrendChart({
  companies,
  trend,
  title,
  format,
  mode = "absolute",
}: {
  companies: ComparisonCompany[];
  trend: string;
  title: string;
  format: "number" | "percent";
  mode?: RevenueMode;
}) {
  const data = useMemo(() => {
    const byCompany = new Map(companies.map((company) => [company.symbol, trendPoints(company, trend, mode)]));
    const periods = [...new Set([...byCompany.values()].flatMap((points) => points.map((point) => point.period)))].sort((left, right) => left.localeCompare(right));
    return periods.map((period) => ({
      period,
      ...Object.fromEntries(companies.map((company) => [company.symbol, byCompany.get(company.symbol)?.find((point) => point.period === period)?.value ?? null])),
    }));
  }, [companies, trend, mode]);
  const displayFormat = trend === "revenue" && mode === "yoy" ? "percent" : format;

  return (
    <div className="comparison-trend">
      <div className="comparison-visual-heading">
        <h4>{title}</h4>
        <span>{mode === "indexed" ? "first year = 100" : mode === "yoy" ? "YoY %" : displayFormat === "percent" ? "%" : "absolute"}</span>
      </div>
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid stroke="#242424" vertical={false} />
            <XAxis dataKey="period" tick={{ fill: "#777", fontSize: 10 }} />
            <YAxis tick={{ fill: "#777", fontSize: 10 }} tickFormatter={(value: number) => displayFormat === "percent" ? `${(value * 100).toFixed(0)}%` : value.toLocaleString()} />
            <Tooltip contentStyle={chartStyle} formatter={(value) => [typeof value === "number" ? formatMetric(value, displayFormat) : "-", title]} />
            {companies.map((company, index) => <Line key={company.symbol} type="monotone" dataKey={company.symbol} stroke={colors[index]} strokeWidth={2} dot={{ r: 2 }} connectNulls />)}
          </LineChart>
        </ResponsiveContainer>
      ) : <p className="comparison-empty">Provider 沒有提供趨勢資料。</p>}
    </div>
  );
}
