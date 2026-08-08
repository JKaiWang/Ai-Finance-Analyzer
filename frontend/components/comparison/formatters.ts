import type { ComparisonCompany } from "@/lib/api";
import type { MetricDefinition } from "./config";

export function percent(value: number | null): string {
  return value === null || !Number.isFinite(value)
    ? "-"
    : `${(value * 100).toFixed(1)}%`;
}

export function number(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "-" : value.toFixed(2);
}

export function compact(value: number | null): string {
  return value === null || !Number.isFinite(value)
    ? "-"
    : new Intl.NumberFormat("en-US", {
        notation: "compact",
        maximumFractionDigits: 1,
      }).format(value);
}

export function formatMetric(
  value: number | null,
  format: MetricDefinition["format"],
): string {
  if (format === "percent") return percent(value);
  if (format === "compact") return compact(value);
  return number(value);
}

export function valueFor(
  company: ComparisonCompany,
  key: keyof ComparisonCompany,
): number | null {
  const value = company[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function sortPeriods(
  points: Array<{ period: string; value: number | null }>,
) {
  return [...points].sort((left, right) => left.period.localeCompare(right.period));
}
