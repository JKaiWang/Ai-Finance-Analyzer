"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MovingAverageRecord, PriceRecord } from "@/lib/api";

type PriceChartProps = {
  history: PriceRecord[];
  currency: string | null;
  movingAverages?: MovingAverageRecord[];
};

type ChartTooltipProps = {
  active?: boolean;
  payload?: Array<{ value?: number }>;
  label?: string;
};

function formatPrice(value: number, currency: string | null): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency ?? "USD",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
}

function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length || typeof payload[0].value !== "number") {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      <strong>{payload[0].value.toFixed(2)}</strong>
    </div>
  );
}

export default function PriceChart({
  history,
  currency,
  movingAverages = [],
}: PriceChartProps) {
  const chartData = history.map((record) => ({
    date: record.date,
    close: record.close,
    ...movingAverages.find((item) => item.date === record.date),
  }));

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 12, right: 8, left: 0, bottom: 4 }}>
          <CartesianGrid stroke="#242424" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#777", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            minTickGap={42}
            tickFormatter={(value: string) => value.slice(0, 7)}
          />
          <YAxis
            tick={{ fill: "#777", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={48}
            tickFormatter={(value: number) => value.toFixed(2)}
            domain={["dataMin", "dataMax"]}
          />
          <Tooltip
            content={<ChartTooltip />}
            labelFormatter={(label) => String(label)}
            formatter={(value) => [
              typeof value === "number" ? formatPrice(value, currency) : "-",
              "Close",
            ]}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#d8d8d8"
            strokeWidth={1.8}
            dot={false}
            activeDot={{ r: 3, fill: "#d8d8d8", stroke: "#0b0b0b", strokeWidth: 2 }}
          />
          <Line
            type="monotone"
            dataKey="ma20"
            name="MA20"
            stroke="#c9a6b1"
            strokeWidth={1.2}
            dot={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma50"
            name="MA50"
            stroke="#a9b4ac"
            strokeWidth={1.2}
            dot={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma200"
            name="MA200"
            stroke="#aaa1b3"
            strokeWidth={1.2}
            dot={false}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
