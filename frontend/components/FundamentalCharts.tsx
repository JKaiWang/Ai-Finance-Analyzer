"use client";

import {
  CartesianGrid,
  Bar,
  BarChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FundamentalsResponse } from "@/lib/api";

type FundamentalChartsProps = {
  fundamentals: FundamentalsResponse;
};

type TrendPoint = {
  period: string;
  value: number | null;
  gross_margin?: number | null;
  operating_margin?: number | null;
  net_margin?: number | null;
};

const chartColors = {
  primary: "#d8d0d2",
  pink: "#c9a6b1",
  sage: "#a9b4ac",
  mauve: "#aaa1b3",
};

function formatChartValue(value: number, percent: boolean): string {
  if (percent) {
    return `${(value * 100).toFixed(0)}%`;
  }

  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function MiniChart({
  data,
  lines,
  percent = false,
}: {
  data: TrendPoint[];
  lines: Array<{ key: string; label: string; color: string }>;
  percent?: boolean;
}) {
  return (
    <div className="fundamental-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 4, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="#242424" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fill: "#777", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: string) => value.slice(0, 4)}
          />
          <YAxis
            tick={{ fill: "#777", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={48}
            tickFormatter={(value: number) => formatChartValue(value, percent)}
          />
          <Tooltip
            contentStyle={{
              border: "1px solid #3a3a38",
              background: "#191919",
              color: "#eeeeec",
              fontSize: 11,
            }}
            formatter={(value) =>
              typeof value === "number"
                ? formatChartValue(value, percent)
                : "-"
            }
          />
          {lines.length > 1 && (
            <Legend
              wrapperStyle={{ color: "#8c8c88", fontSize: 10, paddingTop: 2 }}
            />
          )}
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.label}
              stroke={line.color}
              strokeWidth={1.5}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function MiniBarChart({
  data,
  color,
}: {
  data: TrendPoint[];
  color: string;
}) {
  return (
    <div className="fundamental-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="#242424" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fill: "#777", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: string) => value.slice(0, 4)}
          />
          <YAxis
            tick={{ fill: "#777", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={48}
            tickFormatter={(value: number) => formatChartValue(value, false)}
          />
          <Tooltip
            contentStyle={{
              border: "1px solid #3a3a38",
              background: "#191919",
              color: "#eeeeec",
              fontSize: 11,
            }}
            formatter={(value) =>
              typeof value === "number" ? formatChartValue(value, false) : "-"
            }
          />
          <Bar dataKey="value" name="數值" fill={color} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function FundamentalCharts({ fundamentals }: FundamentalChartsProps) {
  const income = [...fundamentals.income_statement].reverse();
  const cashFlow = [...fundamentals.cash_flow].reverse();

  const revenueData = income.map((record) => ({
    period: record.period,
    value: record.revenue,
  }));
  const epsData = income.map((record) => ({
    period: record.period,
    value: record.eps,
  }));
  const marginData = income.map((record) => ({
    period: record.period,
    value: null,
    gross_margin:
      record.revenue && record.gross_profit !== null
        ? record.gross_profit / record.revenue
        : null,
    operating_margin:
      record.revenue && record.operating_income !== null
        ? record.operating_income / record.revenue
        : null,
    net_margin:
      record.revenue && record.net_income !== null
        ? record.net_income / record.revenue
        : null,
  }));
  const freeCashFlowData = cashFlow.map((record) => ({
    period: record.period,
    value: record.free_cash_flow,
  }));

  return (
    <section className="panel fundamentals-panel" aria-labelledby="fundamentals-heading">
      <div className="section-heading">
        <h2 id="fundamentals-heading">基本面趨勢</h2>
        <span>年度財務報表</span>
      </div>
      <div className="fundamental-chart-grid">
        <div className="fundamental-chart-card">
          <div className="metric-label">營收</div>
          <MiniBarChart data={revenueData} color={chartColors.primary} />
        </div>
        <div className="fundamental-chart-card">
          <div className="metric-label">每股盈餘 EPS</div>
          <MiniBarChart data={epsData} color={chartColors.pink} />
        </div>
        <div className="fundamental-chart-card">
          <div className="metric-label">利潤率</div>
          <MiniChart
            data={marginData}
            percent
            lines={[
              { key: "gross_margin", label: "毛利", color: chartColors.pink },
              { key: "operating_margin", label: "營業利益", color: chartColors.sage },
              { key: "net_margin", label: "淨利", color: chartColors.mauve },
            ]}
          />
        </div>
        <div className="fundamental-chart-card">
          <div className="metric-label">自由現金流 FCF</div>
          <MiniBarChart data={freeCashFlowData} color={chartColors.sage} />
        </div>
      </div>
    </section>
  );
}
