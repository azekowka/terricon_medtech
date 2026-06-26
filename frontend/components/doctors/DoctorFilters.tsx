"use client";

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import type { DoctorSpecialty } from "@/lib/types";

export interface DocFilterState {
  specialty: string;
  price_max: string;
  rating_min: string;
  experience_min: string;
  accepts_children: boolean;
  online_booking: boolean;
  verified: boolean;
  sort: string;
}

export const DOC_SORTS = [
  { key: "rating", label: "По рейтингу" },
  { key: "price_asc", label: "Сначала дешевле" },
  { key: "price_desc", label: "Сначала дороже" },
  { key: "experience", label: "По стажу" },
  { key: "reviews", label: "По отзывам" },
];

export function DoctorFilters({
  specialties,
  state,
  onChange,
}: {
  specialties: DoctorSpecialty[];
  state: DocFilterState;
  onChange: (patch: Partial<DocFilterState>) => void;
}) {
  const [specQuery, setSpecQuery] = useState("");
  const visibleSpecs = specialties
    .filter((s) => s.name.toLowerCase().includes(specQuery.trim().toLowerCase()))
    .slice(0, specQuery ? 40 : 30);

  return (
    <div className="card sticky top-20 space-y-4 p-5">
      <div className="flex items-center gap-2 font-bold text-ink">
        <SlidersHorizontal size={18} /> Фильтры
      </div>

      <div>
        <label className="label">Сортировка</label>
        <select className="input" value={state.sort} onChange={(e) => onChange({ sort: e.target.value })}>
          {DOC_SORTS.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Специализация</label>
        <input
          className="input mb-2"
          placeholder="Поиск специализации…"
          value={specQuery}
          onChange={(e) => setSpecQuery(e.target.value)}
        />
        <div className="max-h-64 space-y-0.5 overflow-y-auto pr-1">
          <button
            onClick={() => onChange({ specialty: "" })}
            className={`block w-full rounded-lg px-2.5 py-1.5 text-left text-sm ${
              !state.specialty ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Все специализации
          </button>
          {visibleSpecs.map((s) => (
            <button
              key={s.alias}
              onClick={() => onChange({ specialty: s.alias })}
              className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-sm ${
                state.specialty === s.alias ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span className="truncate">{s.name}</span>
              <span className="ml-2 shrink-0 text-xs text-slate-400">{s.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label">Цена приёма до, ₸</label>
        <input
          type="number"
          className="input"
          placeholder="например, 10000"
          value={state.price_max}
          onChange={(e) => onChange({ price_max: e.target.value })}
        />
      </div>

      <div>
        <label className="label">Рейтинг от</label>
        <select className="input" value={state.rating_min} onChange={(e) => onChange({ rating_min: e.target.value })}>
          <option value="">Любой</option>
          <option value="4">от 4.0 ★</option>
          <option value="4.5">от 4.5 ★</option>
          <option value="4.8">от 4.8 ★</option>
        </select>
      </div>

      <div>
        <label className="label">Стаж от, лет</label>
        <select className="input" value={state.experience_min} onChange={(e) => onChange({ experience_min: e.target.value })}>
          <option value="">Любой</option>
          <option value="5">от 5 лет</option>
          <option value="10">от 10 лет</option>
          <option value="20">от 20 лет</option>
        </select>
      </div>

      <Toggle label="Принимает детей" checked={state.accepts_children} onChange={(v) => onChange({ accepts_children: v })} />
      <Toggle label="Онлайн-запись" checked={state.online_booking} onChange={(v) => onChange({ online_booking: v })} />
      <Toggle label="Проверенные врачи" checked={state.verified} onChange={(v) => onChange({ verified: v })} />
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700">
      {label}
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4" />
    </label>
  );
}
