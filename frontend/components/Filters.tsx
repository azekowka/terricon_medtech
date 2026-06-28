"use client";

import { Navigation, SlidersHorizontal } from "lucide-react";
import type { Meta } from "@/lib/types";

export interface FilterState {
  city: string;
  category: string;
  price_min: string;
  price_max: string;
  rating_min: string;
  online_booking: boolean;
  include_stale: boolean;
  sort: string;
}

export const SORTS = [
  { key: "price_asc", label: "Сначала дешевле" },
  { key: "price_desc", label: "Сначала дороже" },
  { key: "rating", label: "По рейтингу" },
  { key: "updated", label: "Сначала обновлённые" },
  { key: "distance", label: "По расстоянию" },
];

export function Filters({
  meta,
  state,
  onChange,
  lockedCategory,
  onLocate,
  geoEnabled,
}: {
  meta: Meta | null;
  state: FilterState;
  onChange: (patch: Partial<FilterState>) => void;
  lockedCategory?: boolean;
  onLocate: () => void;
  geoEnabled: boolean;
}) {
  return (
    <div className="card sticky top-20 space-y-4 p-5">
      <div className="flex items-center gap-2 font-bold text-ink">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
          <SlidersHorizontal size={16} strokeWidth={1.75} />
        </span>
        Фильтры
      </div>

      <div>
        <label className="label">Сортировка</label>
        <select className="input" value={state.sort} onChange={(e) => onChange({ sort: e.target.value })}>
          {SORTS.map((s) => (
            <option key={s.key} value={s.key} disabled={s.key === "distance" && !geoEnabled}>
              {s.label}
              {s.key === "distance" && !geoEnabled ? " (вкл. геолокацию)" : ""}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Город</label>
        <select className="input" value={state.city} onChange={(e) => onChange({ city: e.target.value })}>
          <option value="">Все города</option>
          {meta?.cities.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {!lockedCategory && (
        <div>
          <label className="label">Категория</label>
          <select className="input" value={state.category} onChange={(e) => onChange({ category: e.target.value })}>
            <option value="">Все категории</option>
            {meta?.categories.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="label">Цена, ₸</label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            className="input"
            placeholder="от"
            value={state.price_min}
            onChange={(e) => onChange({ price_min: e.target.value })}
          />
          <span className="text-slate-300">—</span>
          <input
            type="number"
            className="input"
            placeholder="до"
            value={state.price_max}
            onChange={(e) => onChange({ price_max: e.target.value })}
          />
        </div>
      </div>

      <div>
        <label className="label">Минимальный рейтинг</label>
        <select className="input" value={state.rating_min} onChange={(e) => onChange({ rating_min: e.target.value })}>
          <option value="">Любой</option>
          <option value="4">от 4.0 ★</option>
          <option value="4.3">от 4.3 ★</option>
          <option value="4.5">от 4.5 ★</option>
        </select>
      </div>

      <label className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
        Только с онлайн-записью
        <input
          type="checkbox"
          checked={state.online_booking}
          onChange={(e) => onChange({ online_booking: e.target.checked })}
          className="h-4 w-4 accent-brand-600"
        />
      </label>

      <label className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
        Показывать устаревшие (&gt;30 дн.)
        <input
          type="checkbox"
          checked={state.include_stale}
          onChange={(e) => onChange({ include_stale: e.target.checked })}
          className="h-4 w-4 accent-brand-600"
        />
      </label>

      <button onClick={onLocate} className={`btn w-full ${geoEnabled ? "btn-ghost" : "btn-outline"}`}>
        <Navigation size={16} strokeWidth={1.75} /> {geoEnabled ? "Геолокация включена" : "Рядом со мной"}
      </button>
    </div>
  );
}
