"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import type { HistorySeries } from "@/lib/types";

const COLORS = ["#1a73f0", "#0d9488", "#f59e0b", "#db2777", "#7c3aed", "#0891b2", "#65a30d", "#e11d48"];

export function PriceHistoryChart({ data }: { data: HistorySeries }) {
  // build a merged time-axis dataset
  const series = data.series.slice(0, 6);
  if (series.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-400">Недостаточно данных для графика истории.</p>;
  }

  const dateSet = new Set<string>();
  series.forEach((s) => s.points.forEach((p) => dateSet.add(p.recorded_at.slice(0, 10))));
  const dates = Array.from(dateSet).sort();

  const rows = dates.map((d) => {
    const row: Record<string, any> = { date: d };
    series.forEach((s, i) => {
      const pt = [...s.points].reverse().find((p) => p.recorded_at.slice(0, 10) <= d);
      if (pt) row[`s${i}`] = pt.price_kzt;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#64748b" }}
          tickFormatter={(d) => new Date(d).toLocaleDateString("ru-RU", { day: "2-digit", month: "short" })}
        />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} width={56} tickFormatter={(v) => `${(v / 1000).toFixed(0)}к`} />
        <Tooltip
          formatter={(v: number) => new Intl.NumberFormat("ru-RU").format(v) + " ₸"}
          labelFormatter={(d) => new Date(d).toLocaleDateString("ru-RU")}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((s, i) => (
          <Line
            key={s.clinic_id}
            type="monotone"
            dataKey={`s${i}`}
            name={s.clinic_name}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 2 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
